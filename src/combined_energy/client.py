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

from .models import (
    ConnectionStatus,
    ConnectionHistory,
    InstallationCustomers,
    Installation,
)

USER_ACCESS_HOST = "https://onwatch.combined.energy"
DATA_ACCESS_HOST = "https://ds20.combined.energy/data-service"


@dataclass
class CombinedEnergy:
    jwt: str
    # installation_id: int

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
            raise Exception(
                "Timeout occurred while connecting to the Combined Energy API"
            ) from ex

        except ClientResponseError as ex:
            raise

        except (
            ClientError,
            socket.gaierror,
        ) as ex:
            raise Exception(
                "Error occurred while communicating with the Combined Energy API"
            ) from ex

        return await response.json()

    async def user(
        self,
    ) -> Installation:
        """
        Get details of current user

        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/user",
        )
        return data
        # return Installation.parse_obj(data)

    async def installation(
        self,
        install_id: int,
    ) -> Installation:
        """
        Get details of installation

        :param install_id: System installation ID

        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/installation",
            i=install_id,
        )
        return Installation.parse_obj(data)

    async def installation_customers(
        self,
        install_id: int,
    ) -> InstallationCustomers:
        """
        Get list of customers associated with an installation

        :param install_id: System installation ID

        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/inst-customers",
            i=install_id,
        )
        return InstallationCustomers.parse_obj(data)

    async def readings(
        self,
        install_id: int,
        range_start: datetime.datetime,
        range_end: Optional[datetime.datetime],
        seconds: int,
    ):
        """
        Get readings from system

        :param install_id: System installation ID
        :param range_start: Start of readings range
        :param range_end: End of readings range
        :param seconds: Sample increment size
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/readings",
            i=install_id,
            rangeStart=int(range_start.timestamp()),
            rangeEnd=int(range_end.timestamp()) if range_end else "",
            seconds=seconds,
        )
        print(data)
        return data

    async def last_readings(
        self, install_id: int, delta: datetime.timedelta, seconds: int
    ):
        """
        Get readings for the last delta range.

        :param install_id: System installation ID
        :param delta: Timezone delta to read data from (positive)
        :param seconds: Sample increment size
        """
        now = datetime.datetime.now()
        return await self.readings(install_id, now - delta, None, seconds)

    # getPerformanceSummary: dataHost + "/dataAccess/performance-summary",
    # getTariffOptions: dataHost + "/dataAccess/tariff-options",
    # getTariffDetails: dataHost + "/dataAccess/tariff-details",
    async def communication_status(self, install_id: int) -> ConnectionStatus:
        """
        Get communication status of the installation
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/comm-stat", i=install_id
        )
        return ConnectionStatus.parse_obj(data)

    async def communication_history(self, install_id: int) -> ConnectionHistory:
        """
        Get communication history of the installation
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/comm-hist", i=install_id
        )
        return ConnectionHistory.parse_obj(data)

    #
    # userAccessLogin: userAccessHost + "/user/Login",
    # userAccessChangePasswordRequest: userAccessHost + "/user/ChangePasswordRequest",
    # userAccessChangePassword: userAccessHost + "/user/ChangePassword",
    # userAccessCheckChangeKey: userAccessHost + "/user/CheckChangeKey",
    # userAccessResume: userAccessHost + "/user/Resume",
    # userUpdatePreferences: userAccessHost + "/user/UpdatePreferences",
    # userTariffSelect: userAccessHost + "/user/TariffSelect",
    # userHelpRequest: userAccessHost + "/user/HelpRequest",
    # userTariffQuery: userAccessHost + "/user/TariffQuery"

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> CombinedEnergy:
        return self

    async def __aexit__(self, *_exc_info):
        await self.close()
