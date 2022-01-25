

class ReolinkError(Exception):
    pass


class ApiError(ReolinkError):
    """Raised when API returns an error code"""
    pass


class InvalidContentTypeError(ReolinkError):
    """Raised when Snapshot command returns an invalid JPEG file"""
    pass


class SnapshotIsNotValidFileTypeError(ReolinkError):
    """Raised when Snapshot command returns an invalid JPEG file"""
    pass


class CredentialsInvalidError(ReolinkError):
    """Raised when an API call returns a credential issue"""
    pass
