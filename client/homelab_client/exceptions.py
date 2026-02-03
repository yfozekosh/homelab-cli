"""Custom exceptions for Homelab client"""


class HomelabError(Exception):
    """Base exception for all Homelab client errors"""

    pass


class APIError(HomelabError):
    """Error communicating with the Homelab API"""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ConfigurationError(HomelabError):
    """Error with client configuration"""

    pass


class ValidationError(HomelabError):
    """Error validating input data"""

    pass


class ResourceNotFoundError(HomelabError):
    """Requested resource was not found"""

    pass


class ConnectionError(HomelabError):
    """Error connecting to the server"""

    pass
