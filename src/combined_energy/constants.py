"""Constants used by API."""

from enum import Enum
from importlib import metadata
import logging

LOGGER = logging.getLogger(__package__)
VERSION = metadata.version("combined-energy-api")


class DeviceType(str, Enum):
    """Type of device."""

    Battery = "BATTERY"
    Combiner = "COMBINER"
    EnergyPredicted = "ENERGY_PRED"
    Receiver = "DRED_RECEIVER"  # Not sure what this is
    EnergyBalance = "ENERGY_BALANCE"
    GenericConsumer = "GENERIC_CONSUMER"
    GridMeter = "GRID_METER"
    Monitor = "MONITOR"  # Not sure what this is
    PoolHeater = "POOL_HEATER"
    SolarPredicted = "SOLAR_PRED"
    SolarPV = "SOLAR_PV"
    Tank = "TANKPAK"  # Not sure what this is
    Total = "TOTAL"
    WaterHeater = "WATER_HEATER"


class Category(str, Enum):
    """Category of device."""

    Airconditioner = "AIRCON"
    Battery = "BATTERY"
    Building = "BUILDING"
    CarCharger = "CAR_CHARGER"
    Combiner = "COMBINER"
    Cooking = "COOKING"
    GridMeter = "GRID_METER"
    Heating = "HEATING"
    Monitor = "MONITOR"
    Others = "OTHERS"
    Pool = "POOL"
    SolarPV = "SOLAR_PV"
    Tank = "TANKPAK"
    WaterHeater = "WATER_HEATER"
