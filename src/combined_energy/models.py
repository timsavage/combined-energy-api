"""API Schema model."""

from datetime import datetime, timedelta
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field, ValidationError

from .constants import LOGGER, DeviceType
from .utils import energy_to_power

now = datetime.now
OptionalFloatList = list[None | float]
OptionalStrList = list[None | str]


class Login(BaseModel):
    """Response from Login."""

    status: str
    expire_minutes: int = Field(alias="expireMins")
    jwt: str

    # Capture time login was created
    created: datetime = Field(default_factory=now)

    def expires(self, expiry_window: int) -> datetime:
        """Calculate when this login expires."""
        offset = timedelta(minutes=self.expire_minutes, seconds=-expiry_window)
        return self.created + offset


class _CommonModel(BaseModel):
    status: str
    installation_id: int = Field(alias="installationId")


class User(BaseModel):
    """Individual user."""

    type: str
    id: int
    email: str
    mobile: str
    fullname: str
    dsa_ok: bool = Field(alias="dsaOk")
    show_introduction: None | str = Field(alias="showIntroduction")


class CurrentUser(BaseModel):
    """Current logged in user."""

    status: str
    user: User


class ConnectionStatus(_CommonModel):
    """Connection Status of the monitor."""

    connected: bool
    since: datetime


class ConnectionHistoryEntry(BaseModel):
    """Entry in connection history."""

    connected: bool
    timestamp: datetime = Field(alias="t")
    device: str = Field(alias="d")
    s: float


class ConnectionHistoryRoute(BaseModel):
    """Route in connection history."""

    timestamp: datetime = Field(alias="t")
    device: str = Field(alias="d")


class ConnectionHistory(_CommonModel):
    """Connection History of the monitor."""

    history: list[ConnectionHistoryEntry]
    route: ConnectionHistoryRoute


class Device(BaseModel):
    """Details of a device."""

    device_id: int = Field(alias="deviceId")
    ref_name: str = Field(alias="refName")
    display_name: str = Field(alias="displayName")
    device_type: str = Field(alias="deviceType")
    device_manufacturer: None | str = Field(alias="deviceManufacturer")
    device_model_name: None | str = Field(alias="deviceModelName")
    supplier_device: bool = Field(alias="supplierDevice")
    storage_device: bool = Field(alias="storageDevice")
    consumer_device: bool = Field(alias="consumerDevice")
    status: str
    max_power_supply: None | int = Field(alias="maxPowerSupply")
    max_power_consumption: None | int = Field(alias="maxPowerConsumption")
    icon_override: None | str = Field(alias="iconOverride")
    order_override: None | int = Field(alias="orderOverride")
    category: str


class Installation(_CommonModel):
    """Details of an installation."""

    source: str
    role: str
    read_only: bool = Field(alias="readOnly")
    dmg_id: int = Field(alias="dmgId")
    tags: list[str]

    mqtt_account_kura: str = Field(alias="mqttAccountKura")
    mqtt_broker_ems: str = Field(alias="mqttBrokerEms")

    timezone: str
    street_address: str = Field(alias="streetAddress")
    locality: str
    state: str
    postcode: str

    review_status: str = Field(alias="reviewStatus")
    nmi: str
    phase: int
    org_id: int = Field(alias="orgId")
    brand: str

    tariff_plan_id: int = Field(alias="tariffPlanId")
    tariff_plan_accepted: int = Field(alias="tariffPlanAccepted")

    devices: list[Device]
    pm: dict[str, list[dict]]


class Customer(BaseModel):
    """Individual customer."""

    customer_id: int = Field(alias="customerId")
    phone: None | str
    email: str
    name: str
    primary: bool


class InstallationCustomers(_CommonModel):
    """Response from customers."""

    customers: list[Customer]


class DeviceReadings(BaseModel):
    """Readings for a particular device."""

    device_id: int | None = Field(alias="deviceId", default=None)
    range_start: datetime | None = Field(alias="rangeStart")
    range_end: datetime | None = Field(alias="rangeEnd")
    timestamp: list[datetime]
    sample_seconds: None | list[int] = Field(alias="sampleSecs")


def _device_energy_sample_to_power(
    attribute: str, *, sample_index: int = -1
) -> Callable[[DeviceReadings], None | float]:
    def _energy_sample_as_power(self: DeviceReadings) -> None | float:
        """Generate a power instantaneous power figure in kW."""
        if self.sample_seconds:
            energy_samples = getattr(self, attribute)
            return energy_to_power(
                energy_samples[sample_index],
                self.sample_seconds[sample_index],
            )

    return _energy_sample_as_power


class DeviceReadingsCombiner(DeviceReadings):
    """Readings for the Combiner device."""

    device_type: Literal["COMBINER"] = Field(alias="deviceType")

    energy_supplied: None | list[None | float] = Field(alias="energySupplied")
    energy_supplied_solar: None | list[None | float] = Field(
        alias="energySuppliedSolar"
    )
    energy_supplied_battery: None | list[None | float] = Field(
        alias="energySuppliedBattery"
    )
    energy_supplied_grid: None | list[None | float] = Field(alias="energySuppliedGrid")
    energy_consumed_other: None | list[None | float] = Field(
        alias="energyConsumedOther"
    )
    energy_consumed_other_solar: None | list[None | float] = Field(
        alias="energyConsumedOtherSolar"
    )
    energy_consumed_other_battery: None | list[None | float] = Field(
        alias="energyConsumedOtherBattery"
    )
    energy_consumed_other_grid: None | list[None | float] = Field(
        alias="energyConsumedOtherGrid"
    )
    energy_consumed: None | list[None | float] = Field(alias="energyConsumed")
    energy_consumed_solar: None | list[None | float] = Field(
        alias="energyConsumedSolar"
    )
    energy_consumed_battery: None | list[None | float] = Field(
        alias="energyConsumedBattery"
    )
    energy_consumed_grid: None | list[None | float] = Field(alias="energyConsumedGrid")
    energy_correction: None | list[None | float] = Field(alias="energyCorrection")
    temperature: None | list[None | float]


class DeviceReadingsSolarPV(DeviceReadings):
    """Readings for the Solar PV device."""

    device_type: Literal["SOLAR_PV"] = Field(alias="deviceType")
    operation_status: None | list[None | str] = Field(alias="operationStatus")
    operation_message: None | list[None | str] = Field(alias="operationMessage")

    energy_supplied: None | list[None | float] = Field(alias="energySupplied")

    # Calculate power figures
    power_supply = property(_device_energy_sample_to_power("energy_supplied"))

    def __str__(self) -> str:
        """Convert self to a string representation."""
        if self.sample_seconds:
            return f"Generation: {self.power_supply:0.02f}kW"
        else:
            return "_.__kW"


class DeviceReadingsGridMeter(DeviceReadings):
    """Readings for the Grid Meter device."""

    device_type: Literal["GRID_METER"] = Field(alias="deviceType")
    operation_status: None | list[None | str] = Field(alias="operationStatus")
    operation_message: None | list[None | str] = Field(alias="operationMessage")

    energy_supplied: None | list[None | float] = Field(alias="energySupplied")
    energy_consumed: None | list[None | float] = Field(alias="energyConsumed")
    energy_consumed_solar: None | list[None | float] = Field(
        alias="energyConsumedSolar"
    )
    energy_consumed_battery: None | list[None | float] = Field(
        alias="energyConsumedBattery"
    )
    power_factor_a: None | list[None | float] = Field(alias="powerFactorA")
    power_factor_b: None | list[None | float] = Field(alias="powerFactorB")
    power_factor_c: None | list[None | float] = Field(alias="powerFactorC")
    voltage_a: None | list[None | float] = Field(alias="voltageA")
    voltage_b: None | list[None | float] = Field(alias="voltageB")
    voltage_c: None | list[None | float] = Field(alias="voltageC")

    # Calculate power figures
    power_supply = property(_device_energy_sample_to_power("energy_supplied"))
    power_consumption = property(_device_energy_sample_to_power("energy_consumed"))
    power_consumption_solar = property(
        _device_energy_sample_to_power("energy_consumed_solar")
    )
    power_consumption_battery = property(
        _device_energy_sample_to_power("energy_consumed_battery")
    )

    def __str__(self) -> str:
        """Convert self to a string representation."""
        if self.sample_seconds:
            return (
                f"Import: {self.power_supply:0.02f}kW; "
                f"Export: {self.power_consumption:0.02f}kW ("
                f"Solar: {self.power_consumption_solar:0.02f}kW; "
                f"Battery: {self.power_consumption_battery:0.02f}kW"
                f")"
            )
        else:
            return "Import: _.__kW; Export: _.__kW (Solar: _.__kW; Battery: _.__kW)"


class DeviceReadingsGenericConsumer(DeviceReadings):
    """Readings for a Generic consumer device."""

    device_type: Literal["GENERIC_CONSUMER"] = Field(alias="deviceType")
    operation_status: None | list[None | str] = Field(alias="operationStatus")
    operation_message: None | list[None | str] = Field(alias="operationMessage")

    energy_consumed: None | list[None | float] = Field(alias="energyConsumed")
    energy_consumed_solar: None | list[None | float] = Field(
        alias="energyConsumedSolar"
    )
    energy_consumed_battery: None | list[None | float] = Field(
        alias="energyConsumedBattery"
    )
    energy_consumed_grid: None | list[None | float] = Field(alias="energyConsumedGrid")

    # Calculate power figures
    power_consumption = property(_device_energy_sample_to_power("energy_consumed"))
    power_consumption_solar = property(
        _device_energy_sample_to_power("energy_consumed_solar")
    )
    power_consumption_battery = property(
        _device_energy_sample_to_power("energy_consumed_battery")
    )
    power_consumption_grid = property(
        _device_energy_sample_to_power("energy_consumed_grid")
    )

    def __str__(self) -> str:
        """Convert self to a string representation."""
        if self.sample_seconds:
            return (
                f"Consumption: {self.power_consumption:0.02f}kW ("
                f"Solar: {self.power_consumption_solar:0.02f}kW; "
                f"Battery: {self.power_consumption_battery:0.02f}kW; "
                f"Grid: {self.power_consumption_grid:0.02f}kW"
                f")"
            )
        else:
            return "_.__kW (S: _.__kW; G: _.__kW; B: _.__kW)"


class DeviceReadingsWaterHeater(DeviceReadingsGenericConsumer):
    """Readings for a Water heater device."""

    device_type: Literal["WATER_HEATER"] = Field(alias="deviceType")

    available_energy: None | list[None | float] = Field(alias="availableEnergy")
    max_energy: None | list[None | float] = Field(alias="maxEnergy")
    temp_sensor1: None | list[None | float] = Field(alias="s1")
    temp_sensor2: None | list[None | float] = Field(alias="s2")
    temp_sensor3: None | list[None | float] = Field(alias="s3")
    temp_sensor4: None | list[None | float] = Field(alias="s4")
    temp_sensor5: None | list[None | float] = Field(alias="s5")
    temp_sensor6: None | list[None | float] = Field(alias="s6")
    water_heater_status: None | list[None | dict[str, Any]] = Field(alias="whStatus")

    def __str__(self):
        """Convert instance to string."""
        if self.sample_seconds:
            return (
                f"{super().__str__()}; "
                f"Available: {self.available_energy[-1]}l ({self.energy_ratio:02.0f}%); "
                f"Temp: {self.output_temp:02.01f}℃"
            )
        else:
            return f"{super().__str__()}; Available _l (__%); Temp: __℃"

    @property
    def energy_ratio(self) -> None | float:
        """Ratio of energy available; in %."""
        if self.sample_seconds:
            return round((self.available_energy[-1] / self.max_energy[-1]) * 100, 1)

    @property
    def output_temp(self) -> None | float:
        """Output temperature of water.

        This is the max temp of available sensors.
        """
        if self.sample_seconds:
            return max(
                [
                    self.temp_sensor1[-1],
                    self.temp_sensor2[-1],
                    self.temp_sensor3[-1],
                    self.temp_sensor4[-1],
                    self.temp_sensor5[-1],
                    self.temp_sensor6[-1],
                ]
            )


class DeviceReadingsEnergyBalance(DeviceReadingsGenericConsumer):
    """Readings for the Energy Balance device."""

    device_type: Literal["ENERGY_BALANCE"] = Field(alias="deviceType")


DEVICE_TYPE_MAP = {
    DeviceType.Combiner: DeviceReadingsCombiner,
    DeviceType.SolarPV: DeviceReadingsSolarPV,
    DeviceType.GridMeter: DeviceReadingsGridMeter,
    DeviceType.GenericConsumer: DeviceReadingsGenericConsumer,
    DeviceType.WaterHeater: DeviceReadingsWaterHeater,
    DeviceType.EnergyBalance: DeviceReadingsEnergyBalance,
}


class Readings(BaseModel):
    """Reading history data."""

    range_start: datetime = Field(alias="rangeStart")
    range_end: datetime = Field(alias="rangeEnd")
    range_count: int = Field(alias="rangeCount")
    seconds: int
    installation_id: int = Field(alias="installationId")
    server_time: datetime = Field(alias="serverTime")

    devices: list[DeviceReadings]
    unknown_devices: list[dict[str, Any]]

    def __init__(self, **data):
        """Initialise readings and pre-process devices."""
        raw_devices = data.pop("devices", [])
        data["devices"], data["unknown_devices"] = self._populate_devices(raw_devices)
        super().__init__(**data)

    @staticmethod
    def _populate_devices(
        raw_devices: list[dict[str, Any]],
    ) -> (list[DeviceReadings], list[dict[str, Any]]):
        """Populate known devices and document unknown.

        This is a workaround to handle devices that are not known to the library
        """
        devices = []
        unknown_devices = []
        for raw_device in raw_devices:
            device_type_name = raw_device.get("deviceType")
            if device_type := DEVICE_TYPE_MAP.get(device_type_name):
                try:
                    devices.append(device_type(**raw_device))
                except ValidationError as ex:
                    LOGGER.error("Validation failed: %s", ex)
                    LOGGER.debug("Device data: %s", raw_device)
                    unknown_devices.append(raw_device)
            else:
                LOGGER.warning("Unknown device type: %s", device_type_name)
                LOGGER.debug("Device data: %s", raw_device)
                unknown_devices.append(raw_device)

        return devices, unknown_devices
