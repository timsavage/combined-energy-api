from enum import Enum


class DeviceType(str, Enum):
    Battery = "BATTERY"
    Combiner = "COMBINER"
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
