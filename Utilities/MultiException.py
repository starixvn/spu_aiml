class Error(Exception):
    """Base class for other exceptions"""
    pass

class ContinueGroupBetting(Error):
    """Raised when want to continue app"""
    pass

class ParentException(Error):
    pass

class ChildException(Error):
    pass