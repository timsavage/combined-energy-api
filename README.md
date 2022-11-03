# Python: Asynchronous client for Combined Energy API

Provides an async Python 3.8+ interface for the http://combined.energy/ monitoring platform API.

> Note this API client is reverse engineered from observing requests being made  
> in the web-application. Please report any failures to read data, this is likely
> to occur for readings as I am only able to create entries for devices that I 
> have.

## Installation

Install from PyPI

```shell
python3 -m pip install combined-energy-api
```

## Usage

```python
import asyncio

from combined_energy import CombinedEnergy
from combined_energy.helpers import ReadingsIterator

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

        # To generate a stream of readings use the iterator, this example fetches
        # data in 5 minute increments
        async for readings in ReadingsIterator(combined_energy, increment=300):
            print(readings)
            await asyncio.sleep(300)

asyncio.run(main())

```


### Development Environment

You will need:

- Python 3.8+
- poetry