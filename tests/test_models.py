from datetime import datetime

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
