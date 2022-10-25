import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import aiohttp.client
import pytest

from combined_energy import client
from combined_energy.models import (
    DeviceReadingsCombiner,
    DeviceReadingsSolarPV,
    DeviceReadingsGridMeter,
    DeviceReadingsGenericConsumer,
    DeviceReadingsWaterHeater,
    DeviceReadingsEnergyBalance,
)


def create_mock_session(response: Path, *, status: int = 200):
    content = response.read_text(encoding="UTF-8")
    return AsyncMock(
        aiohttp.client.ClientSession,
        request=AsyncMock(
            return_value=AsyncMock(
                status=status,
                text=AsyncMock(return_value=content),
                json=AsyncMock(return_value=json.loads(content)),
            ),
        ),
    )


def create_mocked_client(response: Path):
    content = response.read_text(encoding="UTF-8")
    target = client.CombinedEnergy("user@example.com", "password", installation_id=123)
    target._request = AsyncMock(return_value=json.loads(content))

    return target


@pytest.fixture
def fixed_time(monkeypatch):
    monkeypatch.setattr(
        client, "now", lambda: datetime(2022, 10, 24, 3, 50, 23, tzinfo=timezone.utc)
    )


class TestCombinedEnergy:
    @pytest.fixture
    def target(self):
        return client.CombinedEnergy("user@example", "pass", installation_id=123)

    @pytest.mark.asyncio
    async def test_user(self, api_responses: Path):
        target = create_mocked_client(api_responses / "user.json")

        actual = await target.user()

        assert actual.status == "ok"
        assert actual.user.fullname == "Dave Dobbs"
        target._request.assert_called_with(client.DATA_ACCESS_HOST + "/dataAccess/user")

    @pytest.mark.asyncio
    async def test_installation(self, api_responses: Path):
        target = create_mocked_client(api_responses / "installation.json")

        actual = await target.installation()

        assert actual.status == "ACTIVE"
        target._request.assert_called_with(
            client.DATA_ACCESS_HOST + "/dataAccess/installation", i=123
        )

    @pytest.mark.asyncio
    async def test_installation_customers(self, api_responses: Path):
        target = create_mocked_client(api_responses / "inst-customers.json")

        actual = await target.installation_customers()

        assert actual.status == "ok"
        assert actual.customers[0].primary is True
        target._request.assert_called_with(
            client.DATA_ACCESS_HOST + "/dataAccess/inst-customers", i=123
        )

    @pytest.mark.asyncio
    async def test_readings(self, api_responses: Path):
        target = create_mocked_client(api_responses / "readings.json")

        actual = await target.readings(
            datetime(2022, 10, 24, 3, 50, 13, tzinfo=timezone.utc),
            datetime(2022, 10, 24, 3, 50, 23, tzinfo=timezone.utc),
            increment=5,
        )

        assert actual.devices[0].device_type == "COMBINER"
        isinstance(actual.devices[0], DeviceReadingsCombiner)
        assert actual.devices[1].device_type == "SOLAR_PV"
        isinstance(actual.devices[1], DeviceReadingsSolarPV)
        assert actual.devices[3].device_type == "GRID_METER"
        isinstance(actual.devices[3], DeviceReadingsGridMeter)
        assert actual.devices[4].device_type == "WATER_HEATER"
        isinstance(actual.devices[4], DeviceReadingsWaterHeater)
        assert actual.devices[5].device_type == "ENERGY_BALANCE"
        isinstance(actual.devices[5], DeviceReadingsEnergyBalance)
        assert actual.devices[6].device_type == "GENERIC_CONSUMER"
        isinstance(actual.devices[6], DeviceReadingsGenericConsumer)

        target._request.assert_called_with(
            client.DATA_ACCESS_HOST + "/dataAccess/readings",
            i=123,
            rangeStart=1666583413,
            rangeEnd=1666583423,
            seconds=5,
        )

    @pytest.mark.asyncio
    async def test_last_readings(self, api_responses: Path, fixed_time):
        target = create_mocked_client(api_responses / "readings.json")

        actual = await target.last_readings(
            minutes=5,
            increment=5,
        )

        assert actual.range_start == datetime(
            2022, 10, 24, 3, 50, 15, tzinfo=timezone.utc
        )
        assert actual.range_end == datetime(
            2022, 10, 24, 3, 50, 25, tzinfo=timezone.utc
        )

        target._request.assert_called_with(
            client.DATA_ACCESS_HOST + "/dataAccess/readings",
            i=123,
            rangeStart=1666583123,
            rangeEnd="",
            seconds=5,
        )

    @pytest.mark.asyncio
    async def test_last_reading__where_no_range_specified(
        self,
        target,
    ):
        with pytest.raises(ValueError):
            await target.last_readings(increment=5)

    @pytest.mark.asyncio
    async def test_communication_status(self, api_responses: Path):
        target = create_mocked_client(api_responses / "comm-stat.json")

        actual = await target.communication_status()

        assert actual.status == "ok"
        assert actual.connected is True
        assert actual.since == datetime(2022, 10, 24, 3, 50, 13, tzinfo=timezone.utc)
        target._request.assert_called_with(
            client.DATA_ACCESS_HOST + "/dataAccess/comm-stat", i=123
        )

    @pytest.mark.asyncio
    async def test_communication_history(self, target, aresponses, api_responses: Path):
        aresponses.add(
            "onwatch.combined.energy",
            "/user/Login",
            "POST",
            aresponses.Response(
                text="""{"status": "ok", "jwt": "foo", "expireMins": 30}""",
                status=200,
                content_type="application/json",
            ),
        )
        aresponses.add(
            "ds20.combined.energy",
            "/data-service/dataAccess/comm-hist",
            "GET",
            aresponses.Response(
                text=(api_responses / "comm-hist.json").read_text(),
                status=200,
                content_type="application/json",
            ),
        )

        actual = await target.communication_history()

        assert actual.status == "ok"
        assert actual.history[0].timestamp == datetime(
            2022, 10, 24, 3, 50, 13, 254000, tzinfo=timezone.utc
        )

    @pytest.mark.asyncio
    async def test_login__where_login_is_successful(self, target, aresponses):
        aresponses.add(
            "onwatch.combined.energy",
            "/user/Login",
            "POST",
            aresponses.Response(
                text="""{"status": "ok", "jwt": "foo", "expireMins": 30}""",
                status=200,
                content_type="application/json",
            ),
        )

        actual = await target.login()

        aresponses.assert_plan_strictly_followed()
        assert actual.jwt == "foo"

    @pytest.mark.asyncio
    async def test_login__where_login_fails(self, target, aresponses):
        aresponses.add(
            "onwatch.combined.energy",
            "/user/Login",
            "POST",
            aresponses.Response(
                text="""{"status": "failed", "error": "bad password"}""",
                status=200,
                content_type="application/json",
            ),
        )

        with pytest.raises(client.exceptions.CombinedEnergyAuthError):
            await target.login()

        aresponses.assert_plan_strictly_followed()

    @pytest.mark.asyncio
    async def test_async_context_manager__external_session(self):
        async with client.CombinedEnergy(
            "user@example", "pass", installation_id=123, session=AsyncMock()
        ) as target:
            assert target.session is not None

        assert target.session is not None

    @pytest.mark.asyncio
    async def test_async_context_manager__internal_session(self):
        session = AsyncMock()

        async with client.CombinedEnergy(
            "user@example", "pass", installation_id=123
        ) as target:
            target.session = session
            target._close_session = True

        assert target.session is None
        session.close.assert_called()
