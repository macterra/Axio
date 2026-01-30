"""
AKR-0 Execution Harness

Traffic generation and orchestration for Conditions A/B/C.
Implements canonical ordering, batch processing, and TransformationRequest generation.
"""

from dataclasses import dataclass
from typing import Union, Optional
from copy import deepcopy

from pcg32 import PCG32
from structures import (
    AuthorityState,
    EpochTickEvent,
    AuthorityInjectionEvent,
    TransformationRequestEvent,
    ActionRequestEvent,
    TransformationType,
    ConflictStatus,
    ScopeElement,
)
from canonical import (
    compute_epoch_tick_event_id,
    compute_transformation_request_id,
    compute_action_request_id,
    canonical_order,
    check_duplicates,
)
from aie import AIE, AIEConfig, Condition, ADDRESS_BOOK_SIZE, RESOURCE_COUNT, OPERATIONS
from kernel import AKRKernel, KernelResult
from logger import RunLogger


# Configuration per preregistration
EPOCHS_PER_RUN = 100
ACTIONS_PER_EPOCH = 20

TRANSFORMATION_REQUESTS_PER_EPOCH = {
    Condition.A: 0,
    Condition.B: 5,
    Condition.C: 10,
}


@dataclass
class HarnessConfig:
    """Harness configuration for a run."""
    condition: Condition
    seed: int
    epochs: int = EPOCHS_PER_RUN
    actions_per_epoch: int = ACTIONS_PER_EPOCH
    output_dir: str = "logs"


Event = Union[
    EpochTickEvent,
    AuthorityInjectionEvent,
    TransformationRequestEvent,
    ActionRequestEvent,
]


class ExecutionHarness:
    """
    AKR-0 Execution Harness.

    Generates synthetic traffic, applies canonical ordering,
    and orchestrates kernel execution.
    """

    def __init__(self, config: HarnessConfig):
        self.config = config
        self.rng = PCG32(seed=config.seed, stream=0)

        # Event sequence counter for uniqueness
        self.event_seq = 0

        # Initialize AIE
        aie_config = AIEConfig(
            condition=config.condition,
            seed=config.seed,
            epochs=config.epochs,
        )
        self.aie = AIE(aie_config)

        # Initialize kernel
        self.kernel = AKRKernel()

        # Initialize logger
        self.logger = RunLogger(
            run_id=f"{config.condition.value}_{config.seed}",
            output_dir=config.output_dir,
        )

        # Build address book and scope pool (same as AIE)
        self.address_book = [f"H{i:04d}" for i in range(1, ADDRESS_BOOK_SIZE + 1)]
        self.scope_pool = []
        for r in range(RESOURCE_COUNT):
            resource_id = f"R{r:04d}"
            for op in OPERATIONS:
                self.scope_pool.append((resource_id, op))

    def run(self) -> dict:
        """
        Execute a full run.

        Returns:
            Summary dict with results
        """
        self.logger.log_run_start(self.config)

        results = {
            "condition": self.config.condition.value,
            "seed": self.config.seed,
            "epochs": 0,
            "total_events": 0,
            "actions_executed": 0,
            "actions_refused": 0,
            "conflicts_registered": 0,
            "transformations": 0,
            "deadlock": None,
            "failure": None,
            "final_state_hash": None,
        }

        try:
            for epoch in range(self.config.epochs):
                epoch_result = self._run_epoch(epoch)

                results["epochs"] += 1
                results["total_events"] += epoch_result["events_processed"]
                results["actions_executed"] += epoch_result["actions_executed"]
                results["actions_refused"] += epoch_result["actions_refused"]
                results["conflicts_registered"] += epoch_result["conflicts_registered"]
                results["transformations"] += epoch_result["transformations"]

                if epoch_result.get("deadlock"):
                    results["deadlock"] = epoch_result["deadlock"]
                    break

                if epoch_result.get("failure"):
                    results["failure"] = epoch_result["failure"]
                    break

        except Exception as e:
            results["failure"] = str(e)
            self.logger.log_error(str(e))

        results["final_state_hash"] = self.kernel.state.state_id
        self.logger.log_run_end(results)

        return results

    def _run_epoch(self, epoch: int) -> dict:
        """
        Run a single epoch.

        1. Advance epoch (EPOCH_TICK)
        2. Generate batch events
        3. Apply canonical ordering
        4. Process events
        """
        result = {
            "epoch": epoch,
            "events_processed": 0,
            "actions_executed": 0,
            "actions_refused": 0,
            "conflicts_registered": 0,
            "transformations": 0,
            "deadlock": None,
            "failure": None,
        }

        # Generate epoch tick (except for epoch 0 which starts at 0)
        if epoch > 0:
            tick_event = self._create_epoch_tick(epoch)
            tick_result = self._process_event(tick_event)
            result["events_processed"] += 1

            if tick_result.failure:
                result["failure"] = tick_result.failure.value
                return result

        # Generate batch of events for this epoch
        batch = self._generate_epoch_batch(epoch)

        # Check for duplicates
        if check_duplicates(batch):
            result["failure"] = "DUPLICATE_EVENT"
            return result

        # Log pre-ordering
        self.logger.log_pre_order_batch(epoch, batch)

        # Apply canonical ordering
        ordered_batch = canonical_order(batch)

        # Log post-ordering
        self.logger.log_post_order_batch(epoch, ordered_batch)

        # Process events
        for event in ordered_batch:
            kernel_result = self._process_event(event)
            result["events_processed"] += 1

            if kernel_result.failure:
                result["failure"] = kernel_result.failure.value
                return result

            # Track results by output type
            output_type = kernel_result.output.output_type.value
            if output_type == "ACTION_EXECUTED":
                result["actions_executed"] += 1
            elif output_type == "ACTION_REFUSED":
                result["actions_refused"] += 1
            elif output_type == "CONFLICT_REGISTERED":
                result["conflicts_registered"] += 1
            elif output_type == "AUTHORITY_TRANSFORMED":
                result["transformations"] += 1
            elif output_type == "DEADLOCK_DECLARED":
                result["deadlock"] = kernel_result.deadlock.value if kernel_result.deadlock else "UNKNOWN"
                return result

        # Check for deadlock after processing batch (per Q9)
        deadlock = self.kernel.check_deadlock()
        if deadlock:
            deadlock_result = self.kernel.declare_deadlock(deadlock)
            self.logger.log_event(None, deadlock_result)
            result["deadlock"] = deadlock.value
            return result

        return result

    def _generate_epoch_batch(self, epoch: int) -> list[Event]:
        """Generate all events for an epoch (pre-ordering)."""
        batch = []

        # 1. Authority injections from AIE
        injections = self.aie.generate_epoch_injections(epoch)
        batch.extend(injections)

        # 2. Action requests
        actions = self._generate_action_requests(epoch)
        batch.extend(actions)

        # 3. Transformation requests (condition-dependent)
        transforms = self._generate_transformation_requests(epoch)
        batch.extend(transforms)

        return batch

    def _generate_action_requests(self, epoch: int) -> list[ActionRequestEvent]:
        """Generate action requests for an epoch."""
        requests = []

        for i in range(self.config.actions_per_epoch):
            self.event_seq += 1

            # Random holder
            holder_id = self.rng.choice(self.address_book)

            # Random scope element
            scope_elem = self.rng.choice(self.scope_pool)

            # Add nonce to ensure uniqueness
            # The scope includes a tuple with nonce for ID generation
            event = ActionRequestEvent(
                epoch=epoch,
                request_id="",  # Computed below
                requester_holder_id=holder_id,
                action=[scope_elem],
                nonce=self.event_seq,
            )
            event.request_id = compute_action_request_id(event)

            requests.append(event)

        return requests

    def _generate_transformation_requests(
        self, epoch: int
    ) -> list[TransformationRequestEvent]:
        """
        Generate transformation requests per Q39.

        - Condition A: None
        - Condition B: 5 per epoch (random, all should fail)
        - Condition C: 10 per epoch (targeted at conflicts)
        """
        n = TRANSFORMATION_REQUESTS_PER_EPOCH[self.config.condition]
        if n == 0:
            return []

        requests = []

        if self.config.condition == Condition.B:
            # Random requests that should all fail
            for _ in range(n):
                self.event_seq += 1
                holder_id = self.rng.choice(self.address_book)
                transformation = self.rng.choice([
                    TransformationType.REVOKE_AUTHORITY.value,
                    TransformationType.RESOLVE_CONFLICT.value,
                ])

                # Random targets (will fail due to no authority)
                event = TransformationRequestEvent(
                    epoch=epoch,
                    request_id="",
                    requester_holder_id=holder_id,
                    transformation=transformation,
                    targets={
                        "authorityIds": [f"A:nonexistent_{self.rng.next_u32()}"],
                        "scopeElements": None,
                        "conflictIds": None,
                    },
                    nonce=self.event_seq,
                )
                event.request_id = compute_transformation_request_id(event)
                requests.append(event)

        elif self.config.condition == Condition.C:
            # Targeted at conflicts per Q39
            open_conflicts = self.kernel.state.get_open_conflicts()

            # 70% RESOLVE_CONFLICT, 30% REVOKE_AUTHORITY
            resolve_count = int(n * 0.7)
            revoke_count = n - resolve_count

            # Generate RESOLVE_CONFLICT requests
            for i in range(resolve_count):
                holder_id = self.rng.choice(self.address_book)
                self.event_seq += 1

                if open_conflicts:
                    # Target a real conflict
                    conflict = open_conflicts[i % len(open_conflicts)]
                    # Pick an authority to revoke
                    if conflict.authority_ids:
                        auth_to_revoke = self.rng.choice(conflict.authority_ids)
                    else:
                        auth_to_revoke = None

                    event = TransformationRequestEvent(
                        epoch=epoch,
                        request_id="",
                        requester_holder_id=holder_id,
                        transformation=TransformationType.RESOLVE_CONFLICT.value,
                        targets={
                            "authorityIds": [auth_to_revoke] if auth_to_revoke else [],
                            "scopeElements": None,
                            "conflictIds": [conflict.conflict_id],
                        },
                        nonce=self.event_seq,
                    )
                else:
                    # No conflicts yet, make a placeholder
                    event = TransformationRequestEvent(
                        epoch=epoch,
                        request_id="",
                        requester_holder_id=holder_id,
                        transformation=TransformationType.RESOLVE_CONFLICT.value,
                        targets={
                            "authorityIds": [],
                            "scopeElements": None,
                            "conflictIds": [f"C:nonexistent_{self.rng.next_u32()}"],
                        },
                        nonce=self.event_seq,
                    )

                event.request_id = compute_transformation_request_id(event)
                requests.append(event)

            # Generate REVOKE_AUTHORITY requests
            active_auths = self.kernel.state.get_active_authorities()
            for i in range(revoke_count):
                holder_id = self.rng.choice(self.address_book)
                self.event_seq += 1

                if active_auths:
                    # Target a real authority in a conflict
                    auth = active_auths[i % len(active_auths)]
                    event = TransformationRequestEvent(
                        epoch=epoch,
                        request_id="",
                        requester_holder_id=holder_id,
                        transformation=TransformationType.REVOKE_AUTHORITY.value,
                        targets={
                            "authorityIds": [auth.authority_id],
                            "scopeElements": None,
                            "conflictIds": None,
                        },
                        nonce=self.event_seq,
                    )
                else:
                    event = TransformationRequestEvent(
                        epoch=epoch,
                        request_id="",
                        requester_holder_id=holder_id,
                        transformation=TransformationType.REVOKE_AUTHORITY.value,
                        targets={
                            "authorityIds": [f"A:nonexistent_{self.rng.next_u32()}"],
                            "scopeElements": None,
                            "conflictIds": None,
                        },
                        nonce=self.event_seq,
                    )

                event.request_id = compute_transformation_request_id(event)
                requests.append(event)

        return requests

    def _create_epoch_tick(self, target_epoch: int) -> EpochTickEvent:
        """Create an EPOCH_TICK event."""
        event = EpochTickEvent(
            event_id="",
            target_epoch=target_epoch,
        )
        event.event_id = compute_epoch_tick_event_id(event)
        return event

    def _process_event(self, event: Event) -> KernelResult:
        """Process an event through the kernel and log it."""
        result = self.kernel.process_event(event)
        self.logger.log_event(event, result)
        return result
