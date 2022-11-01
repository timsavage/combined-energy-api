from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

import pytest

from combined_energy import helpers


async def async_iter(iterable):
    async for item in iterable:
        yield item


async def async_next(iterator):
    return await iterator.__anext__()


class TestReadingsIterator:
    def test_next_range_start__where_no_request_made(self):
        target = helpers.ReadingsIterator(
            AsyncMock(helpers.CombinedEnergy), increment=10
        )

        actual = target.next_range_start

        assert actual is None

    def test_next_range_start__where_successful_request_made(self):
        target = helpers.ReadingsIterator(
            AsyncMock(helpers.CombinedEnergy), increment=10
        )
        target._last_end = datetime(2022, 2, 22, 22, 22, 22)

        actual = target.next_range_start

        assert actual == datetime(2022, 2, 22, 22, 22, 22)

    def test_next_range_start__where_timedelta_set(self, monkeypatch):
        monkeypatch.setattr(helpers, "now", lambda: datetime(2022, 2, 22, 22, 22, 22))

        target = helpers.ReadingsIterator(
            AsyncMock(helpers.CombinedEnergy),
            increment=10,
            initial_delta=timedelta(minutes=22),
        )

        actual = target.next_range_start

        assert actual == datetime(2022, 2, 22, 22, 00, 22)

    @pytest.mark.asyncio
    async def test_check_for_log_session_restart__check_behaviour(self):
        mock_client = AsyncMock(helpers.CombinedEnergy)
        target = helpers.ReadingsIterator(
            mock_client, increment=10, log_session_reset_count=2
        )

        await target._check_for_log_session_restart()
        mock_client.start_log_session.assert_not_called()

        target._empty.append(False)
        target._empty.append(True)

        await target._check_for_log_session_restart()
        mock_client.start_log_session.assert_not_called()

        target._empty.append(True)

        await target._check_for_log_session_restart()
        mock_client.start_log_session.assert_called()

    @pytest.mark.asyncio
    async def test_iterator(self):
        mock_client = AsyncMock(
            helpers.CombinedEnergy,
            readings=AsyncMock(
                side_effect=[
                    Mock(range_count=1, range_end=datetime(2022, 2, 22, 22, 00, 21)),
                    Mock(range_count=1, range_end=datetime(2022, 2, 22, 22, 00, 22)),
                    Mock(range_count=0, range_end=datetime(2022, 2, 22, 22, 00, 22)),
                    Mock(range_count=0, range_end=datetime(2022, 2, 22, 22, 00, 22)),
                    Mock(range_count=3, range_end=datetime(2022, 2, 22, 22, 00, 25)),
                ]
            ),
        )
        target = helpers.ReadingsIterator(
            mock_client, increment=10, log_session_reset_count=2
        )
        iterator = async_iter(target)

        # Check first request
        await async_next(iterator)
        assert target.next_range_start == datetime(2022, 2, 22, 22, 00, 21)
        mock_client.start_log_session.assert_not_called()

        # Check second request
        await async_next(iterator)
        assert target.next_range_start == datetime(2022, 2, 22, 22, 00, 22)
        mock_client.start_log_session.assert_not_called()

        # Check third request
        await async_next(iterator)
        assert target.next_range_start == datetime(2022, 2, 22, 22, 00, 22)
        mock_client.start_log_session.assert_not_called()

        # Check forth request
        await async_next(iterator)
        assert target.next_range_start == datetime(2022, 2, 22, 22, 00, 22)
        mock_client.start_log_session.assert_not_called()

        # Check fifth request
        await async_next(iterator)
        assert target.next_range_start == datetime(2022, 2, 22, 22, 00, 25)
        mock_client.start_log_session.assert_called()
