# Python: Asynchronous client for Combined Energy API

Provides an async Python 3.11+ interface for the http://combined.energy/ monitoring platform API.

<p align="center">

[![Testing](https://github.com/timsavage/combined-energy-api/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/timsavage/combined-energy-api/actions/workflows/tests.yml)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=timsavage_combined-energy-api&metric=coverage)](https://sonarcloud.io/summary/new_code?id=timsavage_combined-energy-api)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=timsavage_combined-energy-api&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=timsavage_combined-energy-api)
[![PyPI](https://img.shields.io/pypi/v/combined-energy-api?color=green)](https://pypi.org/project/combined-energy-api)
![PyPI - License](https://img.shields.io/pypi/l/combined-energy-api)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</p>

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

- Python 3.11+
- poetry
- pre-commit

Ensure pre-commit is installed into your git repository with `pre-commit install`.
