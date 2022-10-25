from __future__ import annotations

import asyncio
import datetime
import logging
import socket
from dataclasses import dataclass
from importlib import metadata
from typing import Optional, Dict

import async_timeout
from aiohttp import ClientSession, ClientResponseError, ClientError
from aiohttp.hdrs import METH_GET, METH_POST

from . import exceptions
from .models import (
    ConnectionStatus,
    ConnectionHistory,
    InstallationCustomers,
    Installation,
    CurrentUser,
    Readings,
    Login,
)

USER_ACCESS_HOST = "https://onwatch.combined.energy"
DATA_ACCESS_HOST = "https://ds20.combined.energy/data-service"
now = datetime.datetime.now

LOGGING = logging.getLogger(__name__)


@dataclass
class CombinedEnergy:
    """
    Client library for Combined Energy API
    """

    mobile_or_email: str
    password: str
    installation_id: int

    # Configuration Options
    expiry_window: int = 300
    request_timeout: float = 8.0

    # State
    session: Optional[ClientSession] = None
    _close_session: bool = False
    _jwt: Optional[str] = None
    _expires: Optional[datetime] = None

    async def _make_request(
        self,
        url: str,
        params: Dict[str, str] = None,
        data: Dict[str, str] = None,
        *,
        method: str = METH_GET,
    ):
        """
        Handle a request to the Combined Energy API
        """
        version = metadata.version("combined-energy-api")
        headers = {
            "Accept": "application/json",
            "User-Agent": f"PythonCombinedEnergy/{version}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method, url, params=params, headers=headers, data=data
                )
                if response.status == 500:
                    LOGGING.error("Server error: %s", await response.text())
                response.raise_for_status()

        except asyncio.TimeoutError as ex:
            raise exceptions.CombinedEnergyTimeoutError(
                "Timeout occurred while connecting to the Combined Energy API"
            ) from ex

        except ClientResponseError as ex:
            raise exceptions.CombinedEnergyError(
                f"Unexpected error: {ex.status}"
            ) from ex

        except (
            ClientError,
            socket.gaierror,
        ) as ex:
            raise exceptions.CombinedEnergyError(
                "Error occurred while communicating with the Combined Energy API"
            ) from ex

        return await response.json()

    async def _get_token(self):
        """
        Get JWT
        """
        login = await self.login()
        self._jwt = login.jwt
        self._expires = login.expires(self.expiry_window)

    async def _request(self, url: str, **params):
        # Check if a login is required
        if not self._jwt or now() > self._expires:
            LOGGING.info("Login expired; re-login" if self._jwt else "Login required")
            await self._get_token()

        # Apply token
        params.setdefault("jwt", self._jwt)

        return await self._make_request(url, params)

    async def user(
        self,
    ) -> CurrentUser:
        """
        Get details of current user

        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/user",
        )
        return CurrentUser.parse_obj(data)

    async def installation(
        self,
    ) -> Installation:
        """
        Get details of installation
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/installation",
            i=self.installation_id,
        )
        return Installation.parse_obj(data)

    async def installation_customers(
        self,
    ) -> InstallationCustomers:
        """
        Get list of customers associated with an installation

        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/inst-customers",
            i=self.installation_id,
        )
        return InstallationCustomers.parse_obj(data)

    async def readings(
        self,
        range_start: datetime.datetime,
        range_end: Optional[datetime.datetime],
        increment: int,
    ) -> Readings:
        """
        Get readings from system

        :param range_start: Start of readings range
        :param range_end: End of readings range
        :param increment: Sample increment size in seconds
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/readings",
            i=self.installation_id,
            rangeStart=int(range_start.timestamp()),
            rangeEnd=int(range_end.timestamp()) if range_end else "",
            seconds=increment,
        )
        return Readings.parse_obj(data)

    async def last_readings(
        self,
        hours: float = 0,
        minutes: float = 0,
        *,
        increment: int,
    ):
        """
        Get readings for the last delta range.

        :param hours: Delta in hours
        :param minutes: Delta in minutes
        :param increment: Sample increment size in seconds
        """

        delta = datetime.timedelta(hours=hours, minutes=minutes)
        if not delta.total_seconds():
            raise ValueError("Either a time range must be provided")
        return await self.readings(now() - delta, None, increment)

    # getPerformanceSummary: dataHost + "/dataAccess/performance-summary",
    # getTariffDetails: dataHost + "/dataAccess/tariff-details",

    async def communication_status(self) -> ConnectionStatus:
        """
        Get communication status of the installation
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/comm-stat",
            i=self.installation_id,
        )
        return ConnectionStatus.parse_obj(data)

    async def communication_history(self) -> ConnectionHistory:
        """
        Get communication history of the installation
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/comm-hist",
            i=self.installation_id,
        )
        return ConnectionHistory.parse_obj(data)

    async def login(self) -> Login:
        """
        Login and obtain a web token
        """
        data = await self._make_request(
            USER_ACCESS_HOST + "/user/Login",
            data={
                "mobileOrEmail": self.mobile_or_email,
                "pass": self.password,
                "store": False,
            },
            method=METH_POST,
        )
        if data.get("status") != "ok":
            raise exceptions.CombinedEnergyAuthError(data.get("error", "Login failed"))
        return Login.parse_obj(data)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> CombinedEnergy:
        return self

    async def __aexit__(self, *_exc_info):
        await self.close()
