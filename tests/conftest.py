from pathlib import Path

import pytest

HERE = Path(__file__).parent


@pytest.fixture
def api_responses() -> Path:
    return HERE / "fixtures" / "api-responses"
