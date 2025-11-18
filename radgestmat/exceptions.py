"""
Custom exceptions for RadGestMat
"""
from django.core.exceptions import ValidationError, PermissionDenied


class RadGestMatException(Exception):
    """Base exception for RadGestMat"""
    pass


class MaterialNotAvailableException(RadGestMatException):
    """Raised when material is not available for checkout"""
    pass


class InvalidAttributionException(RadGestMatException):
    """Raised when attribution is invalid"""
    pass


class DepartmentAccessDenied(PermissionDenied):
    """Raised when user doesn't have access to a department"""
    pass


class MaterialNotFoundException(RadGestMatException):
    """Raised when material is not found"""
    pass


class QRCodeGenerationException(RadGestMatException):
    """Raised when QR code generation fails"""
    pass


class AlerteServiceException(RadGestMatException):
    """Raised when alert service encounters an error"""
    pass

