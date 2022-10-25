from enum import Enum


class DeviceType(str, Enum):
    Combiner = "COMBINER"
    EnergyBalance = "ENERGY_BALANCE"
    GenericConsumer = "GENERIC_CONSUMER"
    GridMeter = "GRID_METER"
    SolarPV = "SOLAR_PV"
    WaterHeater = "WATER_HEATER"


class Category(str, Enum):
    Airconditioner = "AIRCON"
    Building = "BUILDING"
    GridMeter = "GRID_METER"
    SolarPV = "SOLAR_PV"
    WaterHeater = "WATER_HEATER"
