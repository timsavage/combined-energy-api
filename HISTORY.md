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
