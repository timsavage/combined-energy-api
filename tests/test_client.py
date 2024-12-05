from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import aresponses
from aresponses import ResponsesMockServer
import pytest
from yarl import URL

from combined_energy import client
from combined_energy.models import (
    DeviceReadingsCombiner,
    DeviceReadingsEnergyBalance,
    DeviceReadingsGenericConsumer,
    DeviceReadingsGridMeter,
    DeviceReadingsSolarPV,
    DeviceReadingsWaterHeater,
)


@pytest.fixture
def fixed_time(monkeypatch):
    monkeypatch.setattr(
        client, "now", lambda: datetime(2022, 10, 24, 3, 50, 23, tzinfo=timezone.utc)
    )


def mock_route(
    mock_server: ResponsesMockServer,
    url: URL,
    response: Path = None,
    *,
    method: str = "GET",
    status: int = 200,
    mock_login: bool = True,
    **params: str,
):
    """Generate a mock route from a fixture file."""
    url = URL(url)

    if mock_login:
        mock_server.add(
            "onwatch.combined.energy",
            "/user/Login",
            "POST",
            aresponses.Response(
                text="""{"status": "ok", "jwt": "foo", "expireMins": 30}""",
                status=200,
                content_type="application/json",
            ),
        )
        params["jwt"] = "foo"

    if params:
        url = url.with_query(params)

    mock_server.add(
        url.host,
        url.path_qs,
        method,
        aresponses.Response(
            text=response.read_text(),
            status=status,
            content_type="application/json",
        ),
        match_querystring=True,
    )


class TestCombinedEnergy:
    @pytest.fixture
    def target(self):
        return client.CombinedEnergy("user@example", "pass", installation_id=123)

    @pytest.mark.asyncio
    async def test_user(self, api_responses: Path, aresponses, target):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/user",
            api_responses / "user.json",
        )

        actual = await target.user()

        aresponses.assert_plan_strictly_followed()
        assert actual.status == "ok"
        assert actual.user.fullname == "Dave Dobbs"

    @pytest.mark.asyncio
    async def test_installation(self, api_responses: Path, aresponses, target):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/installation",
            api_responses / "installation.json",
            i="123",
        )

        actual = await target.installation()

        aresponses.assert_plan_strictly_followed()
        assert actual.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_installation_customers(
        self, api_responses: Path, aresponses, target
    ):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/inst-customers",
            api_responses / "inst-customers.json",
            i="123",
        )

        actual = await target.installation_customers()

        aresponses.assert_plan_strictly_followed()
        assert actual.status == "ok"
        assert actual.customers[0].primary is True

    @pytest.mark.asyncio
    async def test_readings(self, api_responses: Path, aresponses, target):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/readings",
            api_responses / "readings.json",
            i="123",
            rangeStart="1666583413",
            rangeEnd="1666583423",
            seconds="5",
        )

        actual = await target.readings(
            datetime(2022, 10, 24, 3, 50, 13, tzinfo=timezone.utc),
            datetime(2022, 10, 24, 3, 50, 23, tzinfo=timezone.utc),
            increment=5,
        )

        aresponses.assert_plan_strictly_followed()
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

    @pytest.mark.asyncio
    async def test_last_readings(
        self, api_responses: Path, aresponses, target, fixed_time
    ):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/readings",
            api_responses / "readings.json",
            i="123",
            rangeStart="1666583123",
            rangeEnd="",
            seconds="5",
        )

        actual = await target.last_readings(
            minutes=5,
            increment=5,
        )

        aresponses.assert_plan_strictly_followed()
        assert actual.range_start == datetime(
            2022, 10, 24, 3, 50, 15, tzinfo=timezone.utc
        )
        assert actual.range_end == datetime(
            2022, 10, 24, 3, 50, 25, tzinfo=timezone.utc
        )

    @pytest.mark.asyncio
    async def test_last_reading__where_no_range_specified(
        self, api_responses: Path, target
    ):
        with pytest.raises(ValueError):
            await target.last_readings(increment=5)

    @pytest.mark.asyncio
    async def test_communication_status(self, api_responses: Path, aresponses, target):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/comm-stat",
            api_responses / "comm-stat.json",
            i="123",
        )

        actual = await target.communication_status()

        aresponses.assert_plan_strictly_followed()
        assert actual.status == "ok"
        assert actual.connected is True
        assert actual.since == datetime(2022, 10, 24, 3, 50, 13, tzinfo=timezone.utc)

    @pytest.mark.asyncio
    async def test_communication_history(self, api_responses: Path, aresponses, target):
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

        aresponses.assert_plan_strictly_followed()
        assert actual.status == "ok"
        assert actual.history[0].timestamp == datetime(
            2022, 10, 24, 3, 50, 13, 254000, tzinfo=timezone.utc
        )

    @pytest.mark.asyncio
    async def test_login__where_login_is_successful(
        self, api_responses: Path, aresponses, target
    ):
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
    async def test_start_log_session__where_refresh_is_successful(
        self, api_responses, target, aresponses
    ):
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
            "dp20.combined.energy",
            "/mqtt2/user/LogSessionStart",
            "POST",
            aresponses.Response(
                text=(api_responses / "LogSessionStart.json").read_text(),
                status=200,
                content_type="application/json",
            ),
        )

        await target.start_log_session()

        aresponses.assert_plan_strictly_followed()

    @pytest.mark.asyncio
    async def test_request__with_permission_denied(
        self, target, aresponses, api_responses
    ):
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/comm-stat",
            api_responses / "comm-stat.json",
            status=401,
            i="123",
        )

        with pytest.raises(client.exceptions.CombinedEnergyPermissionError):
            await target.communication_status()

        aresponses.assert_plan_strictly_followed()

    @pytest.mark.asyncio
    async def test_request__with_server_error(
        self, target, aresponses, api_responses, caplog
    ):
        caplog.at_level("ERROR", client.LOGGER)
        mock_route(
            aresponses,
            client.DATA_ACCESS_HOST + "/dataAccess/comm-stat",
            api_responses / "comm-stat.json",
            status=500,
            i="123",
        )

        with pytest.raises(client.exceptions.CombinedEnergyError):
            await target.communication_status()

        aresponses.assert_plan_strictly_followed()
        assert len(caplog.messages) == 1
        assert caplog.messages[0].startswith("Server error")

    # @pytest.mark.asyncio
    # async def test_request__with_client_error(
    #     self, target, aresponses, api_responses, caplog
    # ):
    #     caplog.at_level("ERROR", client.LOGGER)
    #     mock_route(
    #         aresponses,
    #         client.DATA_ACCESS_HOST + "/dataAccess/comm-stat",
    #         api_responses / "comm-stat.json",
    #         i="123",
    #         eek="!",
    #     )
    #
    #     with pytest.raises(client.exceptions.CombinedEnergyError):
    #         await target.communication_status()
    #
    #     assert len(caplog.messages) == 2
    #     assert caplog.messages[1].startswith("Socket error")

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
