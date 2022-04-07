"""Exceptions raised by TotalConnectClient."""


class TotalConnectError(Exception):
    pass


class AuthenticationError(TotalConnectError):
    pass


class InvalidSessionError(AuthenticationError):
    pass


class BadResultCodeError(TotalConnectError):
    pass


class FeatureNotSupportedError(TotalConnectError):
    """The user hardware and/or account permissions do not support
    the requested feature.
    """


class RetryableTotalConnectError(TotalConnectError):
    """These errors are likely to resolve themselves if the action is retried.
    If an error requires some other action (such as reauthenticating an
    expired session) before being retried, it is not "retryable."
    """


class PartialResponseError(RetryableTotalConnectError):
    """Raised if the response is missing a section that it is always supposed to have.
    Because the TotalConnect servers are flaky, these are rather frequent.
    """


class UsercodeInvalid(TotalConnectError):
    """The provided usercode is invalid."""


class UsercodeUnavailable(TotalConnectError):
    """The TotalConnect usercode unavailable or invalid."""


class ServiceUnavailable(TotalConnectError):
    """The TotalConnect service is unavailable or unreachable."""
