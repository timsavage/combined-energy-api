"""API Schema model."""
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

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
    range_start: datetime = Field(alias="rangeStart")
    range_end: datetime = Field(alias="rangeEnd")
    timestamp: List[datetime]
    sample_seconds: Optional[List[int]] = Field(alias="sampleSecs")


class DeviceReadingsBattery(DeviceReadings):
    """Placeholder for Battery."""

    device_type: Literal["BATTERY"] = Field(alias="deviceType")


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


class DeviceReadingsSolarPredicted(DeviceReadings):
    """Placeholder for solar predictions."""

    device_type: Literal["SOLAR_PRED"] = Field(alias="deviceType")


class DeviceReadingsSolarPV(DeviceReadings):
    """Readings for the Solar PV device."""

    device_type: Literal["SOLAR_PV"] = Field(alias="deviceType")
    operation_status: Optional[List[Optional[str]]] = Field(alias="operationStatus")
    operation_message: Optional[List[Optional[str]]] = Field(alias="operationMessage")

    energy_supplied: Optional[List[float]] = Field(alias="energySupplied")


class DeviceReadingsGridMeter(DeviceReadings):
    """Readings for the Grid Meter device."""

    device_type: Literal["GRID_METER"] = Field(alias="deviceType")


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


class DeviceReadingsPoolHeater(DeviceReadings):
    """Placeholder for a pool heater."""

    device_type: Literal["POOL_HEATER"] = Field(alias="deviceType")


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


class DeviceReadingsEnergyBalance(DeviceReadingsGenericConsumer):
    """Readings for the Energy Balance device."""

    device_type: Literal["ENERGY_BALANCE"] = Field(alias="deviceType")


class Readings(BaseModel):
    """Reading history data."""

    range_start: datetime = Field(alias="rangeStart")
    range_end: datetime = Field(alias="rangeEnd")
    range_count: int = Field(alias="rangeCount")
    seconds: int
    installation_id: int = Field(alias="installationId")
    server_time: datetime = Field(alias="serverTime")
    devices: List[
        Union[
            DeviceReadingsBattery,
            DeviceReadingsCombiner,
            DeviceReadingsSolarPredicted,
            DeviceReadingsSolarPV,
            DeviceReadingsGridMeter,
            DeviceReadingsGenericConsumer,
            DeviceReadingsPoolHeater,
            DeviceReadingsWaterHeater,
            DeviceReadingsEnergyBalance,
        ]
    ] = Field(descriminator="device_type")
