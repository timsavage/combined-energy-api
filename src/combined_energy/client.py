"""Client for API."""

from __future__ import annotations

import asyncio
from asyncio import timeout as aio_timeout
from dataclasses import dataclass
import datetime
import logging
import socket

from aiohttp import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST

from . import exceptions
from .constants import LOGGER, VERSION
from .models import (
    ConnectionHistory,
    ConnectionStatus,
    CurrentUser,
    Installation,
    InstallationCustomers,
    Login,
    Readings,
)

USER_ACCESS_HOST = "https://onwatch.combined.energy"
DATA_ACCESS_HOST = "https://ds20.combined.energy/data-service"
MQTT_ACCESS_HOST = "https://dp20.combined.energy"
now = datetime.datetime.now


@dataclass
class CombinedEnergy:
    """Client library for Combined Energy API."""

    mobile_or_email: str
    password: str
    installation_id: int

    # Configuration Options
    expiry_window: int = 300
    request_timeout: float = 10.0

    # State
    session: ClientSession | None = None
    _close_session: bool = False
    _jwt: str | None = None
    _expires: datetime.datetime | None = None

    async def _make_request(
        self,
        url: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
        *,
        method: str = METH_GET,
        accept: str = "application/json",
        request_timeout: float | None = None,
    ):
        """Handle a request to the Combined Energy API."""
        headers = {
            "Accept": accept,
            "User-Agent": f"PythonCombinedEnergy/{VERSION}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug(
                "Request to %s?%s",
                url,
                "&".join(f"{k}={v}" for k, v in (params or {}).items()),
            )

        try:
            async with aio_timeout(request_timeout or self.request_timeout):
                response = await self.session.request(
                    method, url, params=params, headers=headers, data=data
                )
                if response.status == 500:
                    # Trigger response.text to ensure error is captured
                    LOGGER.error("Server error: %s", await response.text())
                response.raise_for_status()

        except asyncio.TimeoutError as ex:
            raise exceptions.CombinedEnergyTimeoutError(
                "Timeout occurred while connecting to the Combined Energy API"
            ) from ex

        except ClientResponseError as ex:
            if ex.status == 401:
                raise exceptions.CombinedEnergyPermissionError(
                    "Current user does not have access to the specified resource"
                ) from ex

            raise exceptions.CombinedEnergyError(
                f"Unexpected error: {ex.status}", ex.status
            ) from ex

        except (
            ClientError,
            socket.gaierror,
        ) as ex:
            LOGGER.error("Socket error: %s", ex)
            raise exceptions.CombinedEnergyError(
                "Error occurred while communicating with the Combined Energy API"
            ) from ex

        return await response.json()

    async def _get_token(self):
        """Get JWT."""
        login = await self.login()
        self._jwt = login.jwt
        self._expires = login.expires(self.expiry_window)

    async def _ensure_token(self):
        """Check if token is required."""
        if not self._jwt or now() > self._expires:
            LOGGER.info("Login expired; re-login" if self._jwt else "Login required")
            await self._get_token()

    async def _request(self, url: str, **params):
        # Apply token
        await self._ensure_token()
        params.setdefault("jwt", self._jwt)

        return await self._make_request(url, params)

    async def user(
        self,
    ) -> CurrentUser:
        """Get details of current user."""
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/user",
        )
        return CurrentUser.model_validate(data)

    async def installation(
        self,
    ) -> Installation:
        """Get details of installation."""
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/installation",
            i=self.installation_id,
        )
        return Installation.model_validate(data)

    async def installation_customers(
        self,
    ) -> InstallationCustomers:
        """Get list of customers associated with an installation."""
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/inst-customers",
            i=self.installation_id,
        )
        return InstallationCustomers.model_validate(data)

    async def readings(
        self,
        range_start: datetime.datetime | None,
        range_end: datetime.datetime | None,
        increment: int,
    ) -> Readings:
        """Get readings from system.

        :param range_start: Start of readings range
        :param range_end: End of readings range
        :param increment: Sample increment size in seconds
        """
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/readings",
            i=self.installation_id,
            rangeStart=int(range_start.timestamp()) if range_start else "",
            rangeEnd=int(range_end.timestamp()) if range_end else "",
            seconds=increment,
        )
        readings = Readings.model_validate(data)

        return readings

    async def last_readings(
        self,
        hours: float = 0,
        minutes: float = 0,
        seconds: float = 0,
        *,
        increment: int,
    ):
        """Get readings for the last delta range.

        :param hours: Delta in hours
        :param minutes: Delta in minutes
        :param seconds: Delta in seconds
        :param increment: Sample increment size in seconds
        """

        delta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        if not delta.total_seconds():
            raise ValueError("Either a time range must be provided")
        return await self.readings(now() - delta, None, increment)

    # getPerformanceSummary: dataHost + "/dataAccess/performance-summary",
    # getTariffDetails: dataHost + "/dataAccess/tariff-details",

    async def communication_status(self) -> ConnectionStatus:
        """Get communication status of the installation."""
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/comm-stat",
            i=self.installation_id,
        )
        return ConnectionStatus.model_validate(data)

    async def communication_history(self) -> ConnectionHistory:
        """Get communication history of the installation."""
        data = await self._request(
            DATA_ACCESS_HOST + "/dataAccess/comm-hist",
            i=self.installation_id,
        )
        return ConnectionHistory.model_validate(data)

    async def login(self) -> Login:
        """Login and obtain a web token."""
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
        return Login.model_validate(data)

    async def start_log_session(self) -> bool:
        """Trigger the start of a log session (required if readings stop being supplied)."""
        await self._ensure_token()

        try:
            data = await self._make_request(
                MQTT_ACCESS_HOST + "/mqtt2/user/LogSessionStart",
                data={
                    "i": self.installation_id,
                    "jwt": self._jwt,
                },
                method=METH_POST,
            )
            return data.get("status") == "ok"

        except exceptions.CombinedEnergyTimeoutError as ex:
            # Not sure why this particular request consistently times out, ignoring
            # the response brings it back to life
            LOGGER.warning("LogSessionStart request timed out with: %s", ex)
            return True  # Assume ok

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> CombinedEnergy:
        """Async context manager aenter implementation."""
        return self

    async def __aexit__(self, *_exc_info):
        """Async context manager aexit implementation."""
        await self.close()
