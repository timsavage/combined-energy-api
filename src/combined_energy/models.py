from datetime import datetime
from typing import List, Optional, Dict, Literal, Union

from pydantic import BaseModel, validator, Field


class CommonModel(BaseModel):
    status: str
    installation_id: int = Field(alias="installationId")


class User(BaseModel):
    """
    Individual user
    """

    type: str
    id: int
    email: str
    mobile: str
    fullname: str
    dsa_ok: bool = Field(alias="dsaOk")
    show_introduction: Optional[str] = Field(alias="showIntroduction")


class CurrentUser(BaseModel):
    """
    Current logged in user
    """

    status: str
    user: User


class ConnectionStatus(CommonModel):
    """
    Connection Status of the monitor
    """

    connected: bool
    since: datetime

    @staticmethod
    @validator(
        "since",
        pre=True,
    )
    def preparse_timestamp(value: int) -> datetime:
        return datetime.fromtimestamp(value)


class ConnectionHistoryEntry(BaseModel):
    """
    Entry in connection history
    """

    connected: bool
    timestamp: datetime = Field(alias="t")
    device: str = Field(alias="d")
    s: str

    @staticmethod
    @validator(
        "timestamp",
        pre=True,
    )
    def preparse_timestamp(value: int) -> datetime:
        return datetime.fromtimestamp(value)


class ConnectionHistoryRoute(BaseModel):
    """
    Route in connection history
    """

    timestamp: datetime = Field(alias="t")
    device: str = Field(alias="d")

    @staticmethod
    @validator(
        "timestamp",
        pre=True,
    )
    def preparse_timestamp(value: int) -> datetime:
        return datetime.fromtimestamp(value)


class ConnectionHistory(CommonModel):
    """
    Connection History of the monitor
    """

    history: List[ConnectionHistoryEntry]
    route: ConnectionHistoryRoute


class Device(BaseModel):
    """
    Details of a device
    """

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


class Installation(CommonModel):
    """
    Details of an installation
    """

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
    """
    Individual customer
    """

    customer_id: int = Field(alias="customerId")
    phone: Optional[str]
    email: str
    name: str
    primary: bool


class InstallationCustomers(CommonModel):
    """
    Response from customers
    """

    customers: List[Customer]


class DeviceReadings(BaseModel):
    """
    Readings for a particular device
    """

    device_id: Optional[int] = Field(alias="deviceId")
    range_start: datetime = Field(alias="rangeStart")
    range_end: datetime = Field(alias="rangeEnd")
    timestamp: List[int]
    sample_seconds: List[int] = Field(alias="sampleSecs")


class DeviceReadingsCombiner(DeviceReadings):
    device_type: Literal["COMBINER"] = Field(alias="deviceType")

    energy_supplied: List[float] = Field(alias="energySupplied")
    energy_supplied_solar: List[float] = Field(alias="energySuppliedSolar")
    energy_supplied_battery: List[float] = Field(alias="energySuppliedBattery")
    energy_supplied_grid: List[float] = Field(alias="energySuppliedGrid")
    energy_consumed_other: List[float] = Field(alias="energyConsumedOther")
    energy_consumed_other_solar: List[float] = Field(alias="energyConsumedOtherSolar")
    energy_consumed_other_battery: List[float] = Field(
        alias="energyConsumedOtherBattery"
    )
    energy_consumed_other_grid: List[float] = Field(alias="energyConsumedOtherGrid")
    energy_consumed: List[float] = Field(alias="energyConsumed")
    energy_consumed_solar: List[float] = Field(alias="energyConsumedSolar")
    energy_consumed_battery: List[float] = Field(alias="energyConsumedBattery")
    energy_consumed_grid: List[float] = Field(alias="energyConsumedGrid")
    energy_correction: List[int] = Field(alias="energyCorrection")
    temperature: List[Optional[float]]


class DeviceReadingsSolarPV(DeviceReadings):
    device_type: Literal["SOLAR_PV"] = Field(alias="deviceType")
    operation_status: List[str] = Field(alias="operationStatus")
    operation_message: List[Optional[str]] = Field(alias="operationMessage")

    energy_supplied: List[float] = Field(alias="energySupplied")


class DeviceReadingsGridMeter(DeviceReadings):
    device_type: Literal["GRID_METER"] = Field(alias="deviceType")


class DeviceReadingsGenericConsumer(DeviceReadings):
    device_type: Literal["GENERIC_CONSUMER"] = Field(alias="deviceType")
    operation_status: List[str] = Field(alias="operationStatus")
    operation_message: List[Optional[str]] = Field(alias="operationMessage")

    energy_consumed: List[float] = Field(alias="energyConsumed")
    energy_consumed_solar: List[float] = Field(alias="energyConsumedSolar")
    energy_consumed_battery: List[float] = Field(alias="energyConsumedBattery")
    energy_consumed_grid: List[float] = Field(alias="energyConsumedGrid")


class DeviceReadingsWaterHeater(DeviceReadingsGenericConsumer):
    device_type: Literal["WATER_HEATER"] = Field(alias="deviceType")

    available_energy: List[float] = Field(alias="availableEnergy")
    max_energy: List[float] = Field(alias="maxEnergy")
    temp_sensor1: List[float] = Field(alias="s1")
    temp_sensor2: List[float] = Field(alias="s2")
    temp_sensor3: List[float] = Field(alias="s3")
    temp_sensor4: List[float] = Field(alias="s4")
    temp_sensor5: List[float] = Field(alias="s5")
    temp_sensor6: List[float] = Field(alias="s6")
    water_heater_status: List[str] = Field(alias="whStatus")


class DeviceReadingsEnergyBalance(DeviceReadingsGenericConsumer):
    device_type: Literal["ENERGY_BALANCE"] = Field(alias="deviceType")


class Readings(BaseModel):
    """
    Reading history data
    """

    range_start: datetime = Field(alias="rangeStart")
    range_end: datetime = Field(alias="rangeEnd")
    range_count: int = Field(alias="rangeCount")
    seconds: int
    installation_id: int = Field(alias="installationId")
    server_time: datetime = Field(alias="serverTime")
    devices: List[
        Union[
            DeviceReadingsCombiner,
            DeviceReadingsSolarPV,
            DeviceReadingsGridMeter,
            DeviceReadingsWaterHeater,
            DeviceReadingsEnergyBalance,
            DeviceReadingsGenericConsumer,
        ]
    ] = Field(descriminator="device_type")

    @staticmethod
    @validator(
        "range_start",
        "range_end",
        "server_time",
        pre=True,
    )
    def preparse_timestamp(value: int) -> datetime:
        return datetime.fromtimestamp(value)
