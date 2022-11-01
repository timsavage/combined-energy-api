# Example that reads the communication status and fetches readings
import asyncio
import logging
import os

from combined_energy.client import CombinedEnergy
from combined_energy.helpers import ReadingsIterator

INSTALL_ID = int(os.getenv("CE_INSTALL_ID", 0))


async def main():
    logging.basicConfig(level=logging.DEBUG)

    async with CombinedEnergy(
        mobile_or_email=os.getenv("CE_EMAIL", "user@example.com"),
        password=os.getenv("CE_PASSWORD", "PASSWORD"),
        installation_id=INSTALL_ID,
    ) as combined_energy:
        com_stat = await combined_energy.communication_status()
        print(com_stat)

        async for readings in ReadingsIterator(combined_energy, increment=5):
            print(
                f"{readings.range_start} - {readings.range_end}: {readings.range_count}"
            )

            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
