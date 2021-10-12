

class InvalidContentTypeError(Exception):
    """Raised when Snapshot command returns an invalid JPEG file"""
    pass

class SnapshotIsNotValidFileTypeError(Exception):
    """Raised when Snapshot command returns an invalid JPEG file"""
    pass


class CredentialsInvalidError(Exception):
    """Raised when an API call returns a credential issue"""
    pass
