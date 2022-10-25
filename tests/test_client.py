import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, ANY

import aiohttp.client
import pytest

from combined_energy import client


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
    target = client.CombinedEnergy("abc", installation_id=123)
    target._request = AsyncMock(return_value=json.loads(content))

    return target


class TestCombinedEnergy:
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

    # @pytest.mark.asyncio
    # async def test_installation_customers(self, api_responses: Path):
    #     target = create_mocked_client(api_responses / "inst-customers.json")
    #
    #     actual = await target.installation_customers()
    #
    #     assert actual.status == "ACTIVE"
    #     target._request.assert_called_with(
    #         client.DATA_ACCESS_HOST + "/dataAccess/inst-customers", i=123
    #     )

    # @pytest.mark.asyncio
    # async def test_readings(self, api_responses: Path):
    #     target = create_mocked_client(api_responses / "readings.json")
    #
    #     actual = await target.readings()
    #
    #     assert actual.status == "ACTIVE"
    #     target._request.assert_called_with(
    #         client.DATA_ACCESS_HOST + "/dataAccess/readings", i=123
    #     )

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
