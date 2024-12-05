import pytest

from combined_energy import utils


def test_energy_to_power():
    actual = utils.energy_to_power(5.0, 5.0)

    assert actual == 3.6


@pytest.mark.parametrize("seconds", (0.0, -1.0))
def test_energy_to_power__raises_value_error_for_invalid_seconds(seconds):
    with pytest.raises(ValueError, match=r"Seconds must be a positive float\."):
        utils.energy_to_power(5.0, seconds)
