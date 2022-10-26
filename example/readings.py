# Example that reads the communication status and fetches readings
import asyncio
import os

from combined_energy.client import CombinedEnergy

INSTALL_ID = int(os.getenv("CE_INSTALL_ID", 0))


async def main():
    async with CombinedEnergy(
        mobile_or_email=os.getenv("CE_EMAIL", "user@example.com"),
        password=os.getenv("CE_PASSWORD", "PASSWORD"),
        installation_id=INSTALL_ID,
    ) as combined_energy:
        com_stat = await combined_energy.communication_status()
        print(com_stat)

        readings = await combined_energy.last_readings(minutes=15, increment=5)
        for device in readings.devices:
            print(device)


if __name__ == "__main__":
    asyncio.run(main())
