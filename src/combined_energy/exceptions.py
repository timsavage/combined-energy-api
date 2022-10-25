class CombinedEnergyError(Exception):
    """
    Common Error for Combined Energy API
    """


class CombinedEnergyTimeoutError(CombinedEnergyError):
    """
    Timeout occurred accessing API
    """


class CombinedEnergyAuthError(CombinedEnergyError):
    """
    Error occurred with Authentication
    """
