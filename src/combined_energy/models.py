from datetime import datetime
from typing import List, Optional, Dict

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
