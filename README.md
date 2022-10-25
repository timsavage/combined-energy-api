# Python: Asynchronous client for Combined Energy API

Provides an async Python 3.8+ interface for the http://combined.energy/ monitoring platform API.

## Installation

This package is currently only available from source

## Usage

```python
import asyncio

from combined_energy import CombinedEnergy

async def main():
    """
    Example using Combined Energy API client.
    """

    async with CombinedEnergy(
        mobile_or_email="user@example.com",
        password="YOUR_COMBINED_ENERGY_PASSWORD",
        installation_id=9999,
    ) as combined_energy:

        status = await combined_energy.communication_status()
        print(status)

        # Get the last 2 hours in 5 min increments
        readings = await combined_energy.last_readings(hours=2, increment=300)
        print(readings)

asyncio.run(main())

```


### Development Environment

You will need:

- Python 3.8+
- pipenv
- 