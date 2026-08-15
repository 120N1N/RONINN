class CorvusError(Exception):
    """Base exception for Corvus platform"""
    pass

class ToolError(CorvusError):
    """Raised when an external tool fails or returns error"""
    pass

class ScanError(CorvusError):
    """Raised when scan logic fails"""
    pass

class ValidationError(CorvusError):
    """Raised when target validation fails"""
    pass
