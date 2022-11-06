# Example that reads the communication status and fetches readings
import asyncio
from datetime import timedelta
import logging
import os

from combined_energy.client import CombinedEnergy
from combined_energy.helpers import ReadingsIterator


async def main():
    """Main entry point."""

    logging.basicConfig(level=logging.DEBUG)

    async with CombinedEnergy(
        mobile_or_email=os.getenv("CE_EMAIL", "user@example.com"),
        password=os.getenv("CE_PASSWORD", "PASSWORD"),
        installation_id=int(os.getenv("CE_INSTALL_ID", 0)),
    ) as combined_energy:
        com_stat = await combined_energy.communication_status()
        print(com_stat)

        async for readings in ReadingsIterator(
            combined_energy, increment=5, initial_delta=timedelta(seconds=30)
        ):
            print(
                f"{readings.range_start} - {readings.range_end}: {readings.range_count}"
            )
            print(
                *(
                    f"{device.device_type}-{device.device_id} {device}"
                    for device in readings.devices
                ),
                sep="\n",
            )

            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
