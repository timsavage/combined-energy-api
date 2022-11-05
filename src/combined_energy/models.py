"""API Schema model."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Callable

from pydantic import BaseModel, Field, ValidationError

from .constants import LOGGER, DeviceType
from .utils import energy_to_power

now = datetime.now
OptionalFloatList = List[Optional[float]]


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
    show_introduction: Optional[str] = Field(alias="showIntroduction")


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
    s: str


class ConnectionHistoryRoute(BaseModel):
    """Route in connection history."""

    timestamp: datetime = Field(alias="t")
    device: str = Field(alias="d")


class ConnectionHistory(_CommonModel):
    """Connection History of the monitor."""

    history: List[ConnectionHistoryEntry]
    route: ConnectionHistoryRoute


class Device(BaseModel):
    """Details of a device."""

    device_id: int = Field(alias="deviceId")
    ref_name: str = Field(alias="refName")
    display_name: str = Field(alias="displayName")
    device_type: str = Field(alias="deviceType")
    device_manufacturer: Optional[str] = Field(alias="deviceManufacturer")
    device_model_name: Optional[str] = Field(alias="deviceModelName")
    supplier_device: bool = Field(alias="supplierDevice")
    storage_device: bool = Field(alias="storageDevice")
    consumer_device: bool = Field(alias="consumerDevice")
    status: str
    max_power_supply: Optional[int] = Field(alias="maxPowerSupply")
    max_power_consumption: Optional[int] = Field(alias="maxPowerConsumption")
    icon_override: Optional[str] = Field(alias="iconOverride")
    order_override: Optional[int] = Field(alias="orderOverride")
    category: str


class Installation(_CommonModel):
    """Details of an installation."""

    source: str
    role: str
    read_only: bool = Field(alias="readOnly")
    dmg_id: int = Field(alias="dmgId")
    tags: List[str]

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

    devices: List[Device]
    pm: Dict[str, List[dict]]


class Customer(BaseModel):
    """Individual customer."""

    customer_id: int = Field(alias="customerId")
    phone: Optional[str]
    email: str
    name: str
    primary: bool


class InstallationCustomers(_CommonModel):
    """Response from customers."""

    customers: List[Customer]


class DeviceReadings(BaseModel):
    """Readings for a particular device."""

    device_id: Optional[int] = Field(alias="deviceId")
    range_start: Optional[datetime] = Field(alias="rangeStart")
    range_end: Optional[datetime] = Field(alias="rangeEnd")
    timestamp: List[datetime]
    sample_seconds: Optional[List[int]] = Field(alias="sampleSecs")


def device_energy_sample_to_power(
    attribute: str, *, sample_index: int = -1
) -> Callable[[DeviceReadings], Optional[float]]:
    def _energy_sample_as_power(self: DeviceReadings) -> Optional[float]:
        """Current power consumption; this is the latest energy consumed converted to kW."""
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

    energy_supplied: Optional[OptionalFloatList] = Field(alias="energySupplied")
    energy_supplied_solar: Optional[OptionalFloatList] = Field(
        alias="energySuppliedSolar"
    )
    energy_supplied_battery: Optional[OptionalFloatList] = Field(
        alias="energySuppliedBattery"
    )
    energy_supplied_grid: Optional[OptionalFloatList] = Field(
        alias="energySuppliedGrid"
    )
    energy_consumed_other: Optional[OptionalFloatList] = Field(
        alias="energyConsumedOther"
    )
    energy_consumed_other_solar: Optional[OptionalFloatList] = Field(
        alias="energyConsumedOtherSolar"
    )
    energy_consumed_other_battery: Optional[OptionalFloatList] = Field(
        alias="energyConsumedOtherBattery"
    )
    energy_consumed_other_grid: Optional[OptionalFloatList] = Field(
        alias="energyConsumedOtherGrid"
    )
    energy_consumed: Optional[OptionalFloatList] = Field(alias="energyConsumed")
    energy_consumed_solar: Optional[OptionalFloatList] = Field(
        alias="energyConsumedSolar"
    )
    energy_consumed_battery: Optional[OptionalFloatList] = Field(
        alias="energyConsumedBattery"
    )
    energy_consumed_grid: Optional[OptionalFloatList] = Field(
        alias="energyConsumedGrid"
    )
    energy_correction: Optional[OptionalFloatList] = Field(alias="energyCorrection")
    temperature: Optional[OptionalFloatList]


class DeviceReadingsSolarPV(DeviceReadings):
    """Readings for the Solar PV device."""

    device_type: Literal["SOLAR_PV"] = Field(alias="deviceType")
    operation_status: Optional[List[Optional[str]]] = Field(alias="operationStatus")
    operation_message: Optional[List[Optional[str]]] = Field(alias="operationMessage")

    energy_supplied: Optional[List[float]] = Field(alias="energySupplied")

    def __str__(self) -> str:
        """Convert self to a string representation."""
        if self.energy_supplied:
            return f"{self.power_supplied:0.02f}kW"
        else:
            return "_.__kW"

    @property
    def power_supplied(self) -> Optional[float]:
        """Current power generation; this is the latest energy supplied converted to kW."""
        if self.sample_seconds:
            return energy_to_power(self.energy_supplied[-1], self.sample_seconds[-1])


class DeviceReadingsGridMeter(DeviceReadings):
    """Readings for the Grid Meter device."""

    device_type: Literal["GRID_METER"] = Field(alias="deviceType")
    operation_status: Optional[List[Optional[str]]] = Field(alias="operationStatus")
    operation_message: Optional[List[Optional[str]]] = Field(alias="operationMessage")

    energy_consumed: Optional[List[float]] = Field(alias="energyConsumed")
    energy_consumed_solar: Optional[List[float]] = Field(alias="energyConsumedSolar")
    energy_consumed_battery: Optional[List[float]] = Field(
        alias="energyConsumedBattery"
    )

    def __str__(self) -> str:
        """Convert self to a string representation."""
        if self.energy_consumed:
            return (
                f"{self.power_consumption:0.02f}kW ("
                f"S: {self.power_consumption_solar:0.02f}kW; "
                f"B: {self.power_consumption_battery:0.02f}kW"
                f")"
            )
        else:
            return "_.__kW (S: _.__kW; B: _.__kW)"

    power_consumption: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed")
    )
    power_consumption_solar: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed_solar")
    )
    power_consumption_battery: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed_battery")
    )


class DeviceReadingsGenericConsumer(DeviceReadings):
    """Readings for a Generic consumer device."""

    device_type: Literal["GENERIC_CONSUMER"] = Field(alias="deviceType")
    operation_status: Optional[List[Optional[str]]] = Field(alias="operationStatus")
    operation_message: Optional[List[Optional[str]]] = Field(alias="operationMessage")

    energy_consumed: Optional[List[float]] = Field(alias="energyConsumed")
    energy_consumed_solar: Optional[List[float]] = Field(alias="energyConsumedSolar")
    energy_consumed_battery: Optional[List[float]] = Field(
        alias="energyConsumedBattery"
    )
    energy_consumed_grid: Optional[List[float]] = Field(alias="energyConsumedGrid")

    def __str__(self) -> str:
        """Convert self to a string representation."""
        if self.energy_consumed:
            return (
                f"{self.power_consumption:0.02f}kW ("
                f"S: {self.power_consumption_solar:0.02f}kW; "
                f"G: {self.power_consumption_grid:0.02f}kW; "
                f"B: {self.power_consumption_battery:0.02f}kW"
                f")"
            )
        else:
            return "_.__kW (S: _.__kW; G: _.__kW; B: _.__kW)"

    power_consumption: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed")
    )
    power_consumption_solar: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed_solar")
    )
    power_consumption_battery: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed_battery")
    )
    power_consumption_grid: Optional[float] = property(
        device_energy_sample_to_power("energy_consumed_grid")
    )


class DeviceReadingsWaterHeater(DeviceReadingsGenericConsumer):
    """Readings for a Water heater device."""

    device_type: Literal["WATER_HEATER"] = Field(alias="deviceType")

    available_energy: Optional[OptionalFloatList] = Field(alias="availableEnergy")
    max_energy: Optional[OptionalFloatList] = Field(alias="maxEnergy")
    temp_sensor1: Optional[OptionalFloatList] = Field(alias="s1")
    temp_sensor2: Optional[OptionalFloatList] = Field(alias="s2")
    temp_sensor3: Optional[OptionalFloatList] = Field(alias="s3")
    temp_sensor4: Optional[OptionalFloatList] = Field(alias="s4")
    temp_sensor5: Optional[OptionalFloatList] = Field(alias="s5")
    temp_sensor6: Optional[OptionalFloatList] = Field(alias="s6")
    water_heater_status: Optional[List[Optional[str]]] = Field(alias="whStatus")

    def __str__(self):
        if self.sample_seconds:
            return f"{super().__str__()}; Available {self.available_energy[-1]}l ({self.energy_ratio:02.0f}%)"
        else:
            return f"{super().__str__()}; Available _l (__%)"

    @property
    def energy_ratio(self):
        """Ratio of energy available; in %."""
        if self.sample_seconds:
            return (self.available_energy[-1] / self.max_energy[-1]) * 100


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

    devices: List[DeviceReadings]
    unknown_devices: List[Dict[str, Any]]

    def __init__(self, **data):
        """Initialise readings and pre-process devices."""
        raw_devices = data.pop("devices", [])
        data["devices"], data["unknown_devices"] = self._populate_devices(raw_devices)
        super().__init__(**data)

    @staticmethod
    def _populate_devices(
        raw_devices: List[Dict[str, Any]]
    ) -> (List[DeviceReadings], List[Dict[str, Any]]):
        """
        Populate known devices and document unknown.

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
