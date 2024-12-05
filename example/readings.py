"""Example that reads the communication status and fetches readings."""

import asyncio
import datetime
from datetime import timedelta
import logging
import os

from combined_energy.client import CombinedEnergy
from combined_energy.helpers import ReadingsIterator


async def main():
    """Start applicaiton and start featching readings."""

    logging.basicConfig(level=logging.DEBUG)

    async with CombinedEnergy(
        mobile_or_email=os.getenv("CE_EMAIL", "user@example.com"),
        password=os.getenv("CE_PASSWORD", "PASSWORD"),
        installation_id=int(os.getenv("CE_INSTALL_ID", "0")),
    ) as api:
        com_stat = await api.communication_status()
        print(com_stat)

        readings = await api.readings(
            datetime.datetime(2022, 11, 9, 0, 30, 0),
            datetime.datetime(2022, 11, 9, 1, 0, 0),
            increment=5,
        )
        devices = {device.device_type: device for device in readings.devices}
        data = sum(devices["ENERGY_BALANCE"].energy_consumed)
        print("Home Consumed:", data / 1000, "kWh")

        async for readings in ReadingsIterator(
            api, increment=5, initial_delta=timedelta(seconds=30)
        ):
            print(
                f"{readings.range_start} - {readings.range_end}: {readings.range_count}"
            )

            for device in readings.devices:
                print(f"{device.device_type}-{device.device_id} {device}")
                if device.device_type == "ENERGY_BALANCE":
                    print("Home:", sum(device.energy_consumed))

            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
