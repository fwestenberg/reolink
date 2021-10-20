

class ReolinkError(Exception):
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
