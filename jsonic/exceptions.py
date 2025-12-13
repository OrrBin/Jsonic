"""Custom exceptions for Jsonic with path context."""


class JsonicError(Exception):
    """Base exception for Jsonic errors with path context."""
    
    def __init__(self, message: str, path: str = None):
        self.path = path or ""
        if self.path:
            message = f"{message}\n  at path: {self.path}"
        super().__init__(message)


class SerializationError(JsonicError, TypeError):
    """Error during serialization with path context."""
    pass


class DeserializationError(JsonicError, TypeError, AttributeError):
    """Error during deserialization with path context."""
    pass
