from pathlib import Path
import sys

import pytest

HERE = Path(__file__).parent

# Configure src location
SRC = (HERE.parent / "src").absolute()
sys.path.insert(0, SRC.as_posix())


@pytest.fixture
def api_responses() -> Path:
    return HERE / "fixtures" / "api-responses"
