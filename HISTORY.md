## 1.0.0

- Reintroduce pydantic 2 (not that it is the default in Home Assistant).
- Bump to a major release as pydantic 2 is a breaking change.

## 0.8.0

- Fix blocking IO fetching metadata during asyncio request (thanks @evilmarty)
- Drop support for Python 3.10
- Update dependency versions

## 0.7.0
- Revert

## _0.6.1_

**Release Pulled**

- Relax version of pydantic to being greater than 2 to prevent version collisions with other
  Home assistant components.

## _0.6_

**Release Pulled**

- Update the handling of `DeviceReadingsWaterHeater.wh_status` to expect a list of dictionaries.
  This appears to be an update to the API to correct the previous behaviour of wh_status being a
  list of json encoded strings.

## 0.5

Initial release
