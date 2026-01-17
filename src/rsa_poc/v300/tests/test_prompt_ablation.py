"""Tests for Run AA: Prompt-Level Semantic Excision

Tests the IdObfuscationMap, PromptSemanticExcisionFilter, leakage detector,
and de-obfuscation functionality.
"""

import pytest
from rsa_poc.v300.prompt_ablation import (
    IdObfuscationMap,
    PromptSemanticExcisionFilter,
    check_semantic_leakage,
    deobfuscate_artifact,
    obfuscate_apcm,
    obfuscate_feasible_actions,
    CANONICAL_ACTION_IDS,
    CANONICAL_PREFERENCE_IDS,
    CANONICAL_BELIEF_IDS,
    STRUCTURAL_ENUMS,
)


class TestIdObfuscationMap:
    """Tests for deterministic ID bijection."""

    def test_map_creation(self):
        """Map should be created with correct structure."""
        obf_map = IdObfuscationMap(global_seed=42)

        assert len(obf_map.action_map) == len(CANONICAL_ACTION_IDS)
        assert len(obf_map.preference_map) == len(CANONICAL_PREFERENCE_IDS)
        assert len(obf_map.belief_map) == len(CANONICAL_BELIEF_IDS)

    def test_determinism(self):
        """Same seed should produce same bijection."""
        map1 = IdObfuscationMap(global_seed=42)
        map2 = IdObfuscationMap(global_seed=42)

        assert map1.forward_map == map2.forward_map
        assert map1.inverse_map == map2.inverse_map
        assert map1.map_hash == map2.map_hash

    def test_different_seeds_produce_different_maps(self):
        """Different seeds should produce different bijections."""
        map1 = IdObfuscationMap(global_seed=42)
        map2 = IdObfuscationMap(global_seed=123)

        assert map1.forward_map != map2.forward_map
        assert map1.map_hash != map2.map_hash

    def test_bijection_invertibility(self):
        """Forward and inverse maps should be true inverses."""
        obf_map = IdObfuscationMap(global_seed=42)

        for canonical, obfuscated in obf_map.forward_map.items():
            assert obf_map.inverse_map[obfuscated] == canonical

    def test_opaque_id_format(self):
        """Obfuscated IDs should follow the opaque format."""
        obf_map = IdObfuscationMap(global_seed=42)

        for obf_id in obf_map.action_map.values():
            assert obf_id.startswith("A_")
            assert len(obf_id) == 5  # A_001

        for obf_id in obf_map.preference_map.values():
            assert obf_id.startswith("P_")
            assert len(obf_id) == 5  # P_001

        for obf_id in obf_map.belief_map.values():
            assert obf_id.startswith("B_")
            assert len(obf_id) == 5  # B_001

    def test_obfuscate_text(self):
        """Obfuscate should replace canonical IDs with opaque tokens."""
        obf_map = IdObfuscationMap(global_seed=42)

        text = "Agent chose COOPERATE because it SATISFIES P_PREFER_COOPERATION"
        result = obf_map.obfuscate(text)

        # Canonical IDs should be gone
        assert "COOPERATE" not in result
        assert "P_PREFER_COOPERATION" not in result

        # Structural enums should remain
        assert "SATISFIES" in result

        # Opaque tokens should be present
        assert "A_" in result
        assert "P_" in result

    def test_deobfuscate_text(self):
        """Deobfuscate should restore canonical IDs."""
        obf_map = IdObfuscationMap(global_seed=42)

        original = "Agent chose COOPERATE and avoided DEFECT"
        obfuscated = obf_map.obfuscate(original)
        restored = obf_map.deobfuscate(obfuscated)

        assert restored == original

    def test_roundtrip(self):
        """Obfuscate then deobfuscate should be identity."""
        obf_map = IdObfuscationMap(global_seed=42)

        texts = [
            "COOPERATE SATISFIES P_PREFER_COOPERATION",
            "DEFECT VIOLATES P_NO_DEFECT",
            "Choose between WAIT, SHARE, and HELP",
            "Beliefs: WORLD_STATE is stable",
        ]

        for text in texts:
            obfuscated = obf_map.obfuscate(text)
            restored = obf_map.deobfuscate(obfuscated)
            assert restored == text, f"Roundtrip failed for: {text}"

    def test_structural_enums_preserved(self):
        """Structural enums should not be obfuscated."""
        obf_map = IdObfuscationMap(global_seed=42)

        text = "Action SATISFIES constraint, mode is REVISE, strength is HARD"
        result = obf_map.obfuscate(text)

        assert "SATISFIES" in result
        assert "REVISE" in result
        assert "HARD" in result

    def test_obfuscate_artifact(self):
        """Should recursively obfuscate artifact structure."""
        obf_map = IdObfuscationMap(global_seed=42)

        artifact = {
            "action_claim": {
                "candidate_action_id": "COOPERATE",
                "relation": "SATISFIES",
            },
            "references": {
                "pref_ids": ["P_PREFER_COOPERATION", "P_NO_DEFECT"],
            },
            "step": 1,  # Non-string should be preserved
        }

        result = obf_map.obfuscate_artifact(artifact)

        # Action ID obfuscated
        assert result["action_claim"]["candidate_action_id"].startswith("A_")

        # Structural enum preserved
        assert result["action_claim"]["relation"] == "SATISFIES"

        # Preference IDs obfuscated
        for pref_id in result["references"]["pref_ids"]:
            assert pref_id.startswith("P_")

        # Non-string preserved
        assert result["step"] == 1

    def test_deobfuscate_artifact(self):
        """Should restore canonical IDs in artifact."""
        obf_map = IdObfuscationMap(global_seed=42)

        original = {
            "action_claim": {
                "candidate_action_id": "COOPERATE",
                "relation": "SATISFIES",
            },
            "references": {
                "pref_ids": ["P_PREFER_COOPERATION"],
            },
        }

        obfuscated = obf_map.obfuscate_artifact(original)
        restored = obf_map.deobfuscate_artifact(obfuscated)

        assert restored == original

    def test_map_hash_stable(self):
        """Map hash should be stable and non-empty."""
        obf_map = IdObfuscationMap(global_seed=42)

        assert len(obf_map.map_hash) == 16

        # Same seed = same hash
        obf_map2 = IdObfuscationMap(global_seed=42)
        assert obf_map.map_hash == obf_map2.map_hash

    def test_to_dict(self):
        """Serialization should capture key metadata."""
        obf_map = IdObfuscationMap(global_seed=42, run_id="test_run")

        data = obf_map.to_dict()

        assert data["global_seed"] == 42
        assert data["run_id"] == "test_run"
        assert data["map_hash"] == obf_map.map_hash
        assert data["action_count"] == len(CANONICAL_ACTION_IDS)


class TestSemanticLeakageDetector:
    """Tests for leakage detection."""

    def test_no_leakage(self):
        """Clean text should pass leakage check."""
        text = "Agent chose A_001 because it SATISFIES P_001"
        result = check_semantic_leakage(text)

        assert result.passed is True
        assert len(result.leaked_ids) == 0

    def test_action_leakage(self):
        """Leaked action ID should be detected."""
        text = "Agent chose COOPERATE instead of A_002"
        result = check_semantic_leakage(text)

        assert result.passed is False
        assert "COOPERATE" in result.leaked_ids

    def test_preference_leakage(self):
        """Leaked preference ID should be detected."""
        text = "This violates P_NO_DEFECT according to constraint P_001"
        result = check_semantic_leakage(text)

        assert result.passed is False
        assert "P_NO_DEFECT" in result.leaked_ids

    def test_multiple_leaks(self):
        """Multiple leaks should all be detected."""
        text = "COOPERATE SATISFIES P_PREFER_COOPERATION and avoids DEFECT"
        result = check_semantic_leakage(text)

        assert result.passed is False
        assert "COOPERATE" in result.leaked_ids
        assert "P_PREFER_COOPERATION" in result.leaked_ids
        assert "DEFECT" in result.leaked_ids

    def test_word_boundary_matching(self):
        """Should not match substrings within other words."""
        # "WAIT" should not match "WAITING"
        text = "WAITING for A_001 to complete"
        result = check_semantic_leakage(text)

        assert result.passed is True

    def test_structural_enums_allowed(self):
        """Structural enums should not trigger leakage."""
        text = "A_001 SATISFIES P_001, mode is REVISE"
        result = check_semantic_leakage(text)

        assert result.passed is True

    def test_leak_locations_captured(self):
        """Leak locations should provide context."""
        text = "The agent decided to COOPERATE with others"
        result = check_semantic_leakage(text)

        assert result.passed is False
        assert len(result.leak_locations) > 0
        assert "COOPERATE" in result.leak_locations[0]


class TestPromptSemanticExcisionFilter:
    """Tests for the prompt filter."""

    def test_basic_obfuscation(self):
        """Filter should obfuscate prompt correctly."""
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        prompt = """
        Feasible actions: COOPERATE, DEFECT, WAIT

        Constraints:
        - DEFECT VIOLATES P_NO_DEFECT
        - COOPERATE SATISFIES P_PREFER_COOPERATION
        """

        result = filter_.apply(prompt)

        # No canonical IDs should remain
        assert result.leakage_check.passed is True
        assert "COOPERATE" not in result.obfuscated_prompt
        assert "DEFECT" not in result.obfuscated_prompt
        assert "P_NO_DEFECT" not in result.obfuscated_prompt

        # Structural enums should remain
        assert "VIOLATES" in result.obfuscated_prompt
        assert "SATISFIES" in result.obfuscated_prompt

    def test_trace_removal(self):
        """Filter should remove derivation trace sections."""
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        prompt = """
        Feasible actions: A_001, A_002

        # Derivation Trace
        Previous step chose COOPERATE because of trust.
        This is semantic content that would leak meaning.

        Make your choice:
        """

        result = filter_.apply(prompt, remove_traces=True)

        assert result.traces_removed is True
        assert "Derivation Trace" not in result.obfuscated_prompt
        assert "Previous step" not in result.obfuscated_prompt

    def test_hashes_computed(self):
        """Filter should compute all required hashes."""
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        result = filter_.apply("COOPERATE or DEFECT?")

        assert len(result.canonical_prompt_hash) == 16
        assert len(result.obfuscated_prompt_hash) == 16
        assert len(result.map_hash) == 16
        assert result.canonical_prompt_hash != result.obfuscated_prompt_hash

    def test_symbol_count(self):
        """Filter should count obfuscated symbols."""
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        prompt = "COOPERATE, DEFECT, WAIT: three actions"
        result = filter_.apply(prompt)

        assert result.obfuscated_symbol_count == 3

    def test_leakage_detection_integrated(self):
        """Filter should detect leakage in obfuscated output."""
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        # Normal case - no leakage
        result = filter_.apply("COOPERATE SATISFIES P_PREFER_COOPERATION")
        assert result.leakage_check.passed is True

    def test_last_result_stored(self):
        """Filter should store last result."""
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        filter_.apply("COOPERATE test")

        assert filter_.last_result is not None
        assert filter_.last_result.obfuscated_symbol_count > 0


class TestDeobfuscateArtifact:
    """Tests for artifact de-obfuscation."""

    def test_basic_deobfuscation(self):
        """Should restore canonical IDs in J_raw."""
        obf_map = IdObfuscationMap(global_seed=42)

        # Simulate LLM output with obfuscated IDs
        j_raw_obf = {
            "action_claim": {
                "candidate_action_id": obf_map.action_map["COOPERATE"],
                "relation": "SATISFIES",
            },
            "references": {
                "pref_ids": [obf_map.preference_map["P_PREFER_COOPERATION"]],
            },
        }

        j_raw = deobfuscate_artifact(j_raw_obf, obf_map)

        assert j_raw["action_claim"]["candidate_action_id"] == "COOPERATE"
        assert j_raw["action_claim"]["relation"] == "SATISFIES"
        assert j_raw["references"]["pref_ids"] == ["P_PREFER_COOPERATION"]

    def test_nested_structures(self):
        """Should handle deeply nested structures."""
        obf_map = IdObfuscationMap(global_seed=42)

        j_raw_obf = {
            "level1": {
                "level2": {
                    "action": obf_map.action_map["DEFECT"],
                    "prefs": [
                        obf_map.preference_map["P_NO_DEFECT"],
                        obf_map.preference_map["P_NO_LIE"],
                    ],
                },
            },
        }

        j_raw = deobfuscate_artifact(j_raw_obf, obf_map)

        assert j_raw["level1"]["level2"]["action"] == "DEFECT"
        assert "P_NO_DEFECT" in j_raw["level1"]["level2"]["prefs"]
        assert "P_NO_LIE" in j_raw["level1"]["level2"]["prefs"]


class TestAPCMObfuscation:
    """Tests for APCM structure obfuscation."""

    def test_apcm_obfuscation(self):
        """Should obfuscate both action and preference IDs in APCM."""
        obf_map = IdObfuscationMap(global_seed=42)

        apcm = {
            "COOPERATE": {
                "violates": set(),
                "satisfies": {"P_PREFER_COOPERATION"},
            },
            "DEFECT": {
                "violates": {"P_NO_DEFECT"},
                "satisfies": set(),
            },
        }

        result = obfuscate_apcm(apcm, obf_map)

        # Action IDs should be obfuscated
        assert "COOPERATE" not in result
        assert "DEFECT" not in result

        # Preference IDs should be obfuscated
        for action_constraints in result.values():
            for pref_id in action_constraints["violates"]:
                assert pref_id.startswith("P_")
            for pref_id in action_constraints["satisfies"]:
                assert pref_id.startswith("P_")

    def test_feasible_actions_obfuscation(self):
        """Should obfuscate list of feasible actions."""
        obf_map = IdObfuscationMap(global_seed=42)

        feasible = ["COOPERATE", "DEFECT", "WAIT"]
        result = obfuscate_feasible_actions(feasible, obf_map)

        assert len(result) == 3
        for action in result:
            assert action.startswith("A_")

        # Should not contain canonical IDs
        assert "COOPERATE" not in result
        assert "DEFECT" not in result
        assert "WAIT" not in result


class TestEndToEndRunAA:
    """End-to-end tests for Run AA pipeline."""

    def test_full_pipeline(self):
        """Test complete obfuscation → LLM simulation → deobfuscation."""
        # Setup
        obf_map = IdObfuscationMap(global_seed=42)
        filter_ = PromptSemanticExcisionFilter(obf_map)

        # Step 1: Build canonical prompt
        canonical_prompt = """
        You are an agent making a decision.

        Feasible actions: COOPERATE, DEFECT, WAIT

        Constraints:
        - DEFECT VIOLATES P_NO_DEFECT
        - COOPERATE SATISFIES P_PREFER_COOPERATION

        Choose an action that respects your constraints.
        """

        # Step 2: Apply obfuscation
        result = filter_.apply(canonical_prompt)

        assert result.leakage_check.passed, f"Leakage detected: {result.leakage_check.leaked_ids}"

        # Step 3: Simulate LLM response with obfuscated IDs
        # LLM would see opaque tokens and respond with them
        coop_obf = obf_map.action_map["COOPERATE"]
        pref_obf = obf_map.preference_map["P_PREFER_COOPERATION"]

        j_raw_obf = {
            "action_claim": {
                "candidate_action_id": coop_obf,
                "relation": "SATISFIES",
            },
            "references": {
                "pref_ids": [pref_obf],
            },
        }

        # Step 4: Deobfuscate immediately after LLM
        j_raw = deobfuscate_artifact(j_raw_obf, obf_map)

        # Step 5: Verify canonical form restored
        assert j_raw["action_claim"]["candidate_action_id"] == "COOPERATE"
        assert j_raw["action_claim"]["relation"] == "SATISFIES"
        assert "P_PREFER_COOPERATION" in j_raw["references"]["pref_ids"]

    def test_determinism_across_seeds(self):
        """Same seed should produce identical obfuscation."""
        seed = 42
        prompt = "COOPERATE or DEFECT? P_NO_DEFECT matters."

        # Run 1
        map1 = IdObfuscationMap(global_seed=seed)
        filter1 = PromptSemanticExcisionFilter(map1)
        result1 = filter1.apply(prompt)

        # Run 2
        map2 = IdObfuscationMap(global_seed=seed)
        filter2 = PromptSemanticExcisionFilter(map2)
        result2 = filter2.apply(prompt)

        assert result1.obfuscated_prompt == result2.obfuscated_prompt
        assert result1.obfuscated_prompt_hash == result2.obfuscated_prompt_hash
        assert result1.map_hash == result2.map_hash
