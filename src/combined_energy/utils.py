"""Utility methods."""

from typing import Final

KWH_TO_KW: Final[float] = 3.6


def energy_to_power(energy: float, seconds: float) -> float:
    """Convert an energy value to power.

    Essentially take an energy value in kWh and calculate an instant power in kW.
    """
    if seconds <= 0.0:
        raise ValueError("Seconds must be a positive float.")

    return energy * KWH_TO_KW / seconds
