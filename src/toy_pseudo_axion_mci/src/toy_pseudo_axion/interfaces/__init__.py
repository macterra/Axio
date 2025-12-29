"""Interface module for causal interfaces (full, mci_latent, mci_minimal)."""

from .base import CausalInterface, InterfaceSpec
from .full import FullInterface
from .mci_latent import MCILatentInterface, compute_replay_model_action
from .mci_minimal import MCIMinimalInterface

__all__ = [
    "CausalInterface",
    "InterfaceSpec",
    "FullInterface",
    "MCILatentInterface",
    "MCIMinimalInterface",
    "compute_replay_model_action",
    "get_interface",
]


def get_interface(mode: str) -> CausalInterface:
    """Get an interface instance for the given mode.

    Args:
        mode: One of "full", "mci_latent", "mci_minimal"

    Returns:
        Interface instance
    """
    if mode == "full":
        return FullInterface()
    elif mode == "mci_latent":
        return MCILatentInterface()
    elif mode == "mci_minimal":
        return MCIMinimalInterface()
    else:
        raise ValueError(f"Unknown interface mode: {mode}. Must be one of ['full', 'mci_latent', 'mci_minimal']")
