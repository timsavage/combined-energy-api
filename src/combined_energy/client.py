from __future__ import annotations

import asyncio
import datetime
import socket
from dataclasses import dataclass
from importlib import metadata
from typing import Optional

import async_timeout
from aiohttp import ClientSession, ClientResponseError, ClientError
from aiohttp.hdrs import METH_GET

from . import exceptions
from .models import (
    ConnectionStatus,
    ConnectionHistory,
    InstallationCustomers,
    Installation,
    CurrentUser,
    Readings,
)

USER_ACCESS_HOST = "https://onwatch.combined.energy"
DATA_ACCESS_HOST = "https://ds20.combined.energy/data-service"


@dataclass
class CombinedEnergy:
    """
    Client library for Combined Energy API
    """

    jwt: str
    installation_id: int

    request_timeout: float = 8.0
    session: Optional[ClientSession] = None

    _close_session: bool = False

    async def _request(
        self,
        url: str,
        *,
        method: str = METH_GET,
        **params,
    ):
        """
        Handle a request to the Combined Energy API
        """
        version = metadata.version("combined-energy-api")
        headers = {
            "Accept": "application/json",
            "User-Agent": f"PythonCombinedEnergy/{version}",
        }
        if self.jwt:
            params.setdefault("jwt", self.jwt)

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                )
                if response.status == 500:
                    print(await response.text())
                response.raise_for_status()

        except asyncio.TimeoutError as ex:
            raise exceptions.CombinedEnergyTimeoutError(
                "Timeout occurred while connecting to the Combined Energy API"
            ) from ex

        except ClientResponseError as ex:
            # TODO: Process these errors (are often text...)
            raise

        except (
            ClientError,
            socket.gaierror,
        ) as ex:
            raise exceptions.CombinedEnergyError(
                "Error occurred while communicating with the Combined Energy API"
            ) from ex

        return await response.json()

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
        seconds: int,
    ) -> Readings:
        """
        Get readings from system

        :param range_start: Start of readings range
        :param range_end: End of readings range
        :param seconds: Sample increment size
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/readings",
            i=self.installation_id,
            rangeStart=int(range_start.timestamp()),
            rangeEnd=int(range_end.timestamp()) if range_end else "",
            seconds=seconds,
        )
        return Readings.parse_obj(data)

    async def last_readings(
        self,
        delta: datetime.timedelta,
        seconds: int,
    ):
        """
        Get readings for the last delta range.

        :param delta: Timezone delta to read data from (positive)
        :param seconds: Sample increment size
        """
        now = datetime.datetime.now()
        return await self.readings(now - delta, None, seconds)

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

    # userAccessLogin: userAccessHost + "/user/Login",
    # userAccessChangePasswordRequest: userAccessHost + "/user/ChangePasswordRequest",
    # userAccessChangePassword: userAccessHost + "/user/ChangePassword",
    # userAccessCheckChangeKey: userAccessHost + "/user/CheckChangeKey",
    # userAccessResume: userAccessHost + "/user/Resume",

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> CombinedEnergy:
        return self

    async def __aexit__(self, *_exc_info):
        await self.close()
