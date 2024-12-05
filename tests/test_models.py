from datetime import datetime
from unittest.mock import Mock

import pytest

from combined_energy import models


class TestLogin:
    def test_expires(self):
        target = models.Login(
            status="ok",
            expireMins=30,
            jwt="...",
            created=datetime(2022, 10, 26, 1, 44),
        )

        actual = target.expires(60)

        assert actual == datetime(2022, 10, 26, 2, 13)


def test_device_energy_sample_to_power__where_reading_has_data():
    mock_device_readings = Mock(
        models.DeviceReadings, energy_readings=[2.3, 5.0], sample_seconds=[5, 5]
    )

    target = models._device_energy_sample_to_power("energy_readings")

    actual = target(mock_device_readings)

    assert actual == 3.6


def test_device_energy_sample_to_power__where_no_data():
    mock_device_readings = Mock(
        models.DeviceReadings, energy_readings=None, sample_seconds=[]
    )

    target = models._device_energy_sample_to_power("energy_readings")

    actual = target(mock_device_readings)

    assert actual is None


class TestDeviceReadingsWaterHeater:
    @pytest.fixture
    def target_available(self) -> models.DeviceReadingsWaterHeater:
        return models.DeviceReadingsWaterHeater(
            deviceId=1,
            rangeStart=None,
            rangeEnd=None,
            timestamp=[datetime.now(), datetime.now()],
            sampleSecs=[5, 5],
            operationStatus=[None, None],
            operationMessage=[None, None],
            energyConsumed=[1, 1],
            energyConsumedSolar=[1, 1],
            energyConsumedBattery=[1, 1],
            energyConsumedGrid=[1, 1],
            deviceType="WATER_HEATER",
            availableEnergy=[300, 491.4],
            maxEnergy=[630, 630],
            s1=[16.5, 17.5],
            s2=[16.5, 23.5],
            s3=[16.5, 50.8],
            s4=[16.5, 55.8],
            s5=[16.5, 60.3],
            s6=[16.5, 68.9],
            whStatus=[None, None],
        )

    @pytest.fixture
    def target_not_available(self) -> models.DeviceReadingsWaterHeater:
        return models.DeviceReadingsWaterHeater(
            deviceId=1,
            rangeStart=None,
            rangeEnd=None,
            timestamp=[],
            sampleSecs=[],
            operationStatus=None,
            operationMessage=None,
            energyConsumed=None,
            energyConsumedSolar=None,
            energyConsumedBattery=None,
            energyConsumedGrid=None,
            deviceType="WATER_HEATER",
            availableEnergy=None,
            maxEnergy=None,
            s1=None,
            s2=None,
            s3=None,
            s4=None,
            s5=None,
            s6=None,
            whStatus=None,
        )

    def test_energy_ratio__where_data_available(self, target_available):
        actual = target_available.energy_ratio

        assert actual == 78.0

    def test_energy_ratio__where_no_data(self, target_not_available):
        actual = target_not_available.energy_ratio

        assert actual is None

    def test_output_temp__where_data_available(self, target_available):
        actual = target_available.output_temp

        assert actual == 68.9

    def test_output_temp__where_no_data(self, target_not_available):
        actual = target_not_available.output_temp

        assert actual is None
