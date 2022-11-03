"""Expected exception types."""


class CombinedEnergyError(Exception):
    """Common Error for Combined Energy API."""


class CombinedEnergyTimeoutError(CombinedEnergyError):
    """Timeout occurred accessing API."""


class CombinedEnergyAuthError(CombinedEnergyError):
    """Error occurred with Authentication."""


class CombinedEnergyPermissionError(CombinedEnergyError):
    """Don't have permission to access particular item."""
