"""Input validation utilities for Homelab client"""

import re
from typing import Optional
from .exceptions import ValidationError


# Regex patterns
IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)

MAC_PATTERN = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
)

HOSTNAME_PATTERN = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.[A-Za-z0-9-]{1,63})*$"
)

NAME_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_-]{0,62}$"
)


def validate_ip_address(ip: str) -> str:
    """Validate IPv4 address format
    
    Args:
        ip: IP address string to validate
        
    Returns:
        The validated IP address
        
    Raises:
        ValidationError: If IP address is invalid
    """
    if not ip or not isinstance(ip, str):
        raise ValidationError("IP address cannot be empty")
    
    ip = ip.strip()
    
    if not IP_PATTERN.match(ip):
        raise ValidationError(
            f"Invalid IP address format: '{ip}'. "
            "Expected format: XXX.XXX.XXX.XXX (e.g., 192.168.1.100)"
        )
    
    return ip


def validate_mac_address(mac: str) -> str:
    """Validate MAC address format
    
    Args:
        mac: MAC address string to validate
        
    Returns:
        The validated MAC address (normalized to uppercase with colons)
        
    Raises:
        ValidationError: If MAC address is invalid
    """
    if not mac or not isinstance(mac, str):
        raise ValidationError("MAC address cannot be empty")
    
    mac = mac.strip().upper()
    
    # Normalize separators to colons
    mac = mac.replace("-", ":")
    
    if not MAC_PATTERN.match(mac):
        raise ValidationError(
            f"Invalid MAC address format: '{mac}'. "
            "Expected format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"
        )
    
    return mac


def validate_hostname(hostname: str) -> str:
    """Validate hostname format
    
    Args:
        hostname: Hostname string to validate
        
    Returns:
        The validated hostname
        
    Raises:
        ValidationError: If hostname is invalid
    """
    if not hostname or not isinstance(hostname, str):
        raise ValidationError("Hostname cannot be empty")
    
    hostname = hostname.strip().lower()
    
    if len(hostname) > 253:
        raise ValidationError(
            f"Hostname too long: {len(hostname)} characters (max 253)"
        )
    
    if not HOSTNAME_PATTERN.match(hostname):
        raise ValidationError(
            f"Invalid hostname format: '{hostname}'. "
            "Hostname must contain only alphanumeric characters, hyphens, and dots."
        )
    
    return hostname


def validate_name(name: str, resource_type: str = "resource") -> str:
    """Validate resource name (plug name, server name)
    
    Args:
        name: Name string to validate
        resource_type: Type of resource for error messages
        
    Returns:
        The validated name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError(f"{resource_type.capitalize()} name cannot be empty")
    
    name = name.strip()
    
    if len(name) > 63:
        raise ValidationError(
            f"{resource_type.capitalize()} name too long: {len(name)} characters (max 63)"
        )
    
    if not NAME_PATTERN.match(name):
        raise ValidationError(
            f"Invalid {resource_type} name: '{name}'. "
            "Name must start with alphanumeric and contain only alphanumeric, hyphens, and underscores."
        )
    
    return name


def validate_positive_float(value: float, name: str = "value", min_val: float = 0.0, max_val: Optional[float] = None) -> float:
    """Validate a positive float value
    
    Args:
        value: Float value to validate
        name: Name of the value for error messages
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive), None for no limit
        
    Returns:
        The validated float
        
    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name.capitalize()} must be a number")
    
    if value < min_val:
        raise ValidationError(f"{name.capitalize()} must be at least {min_val}")
    
    if max_val is not None and value > max_val:
        raise ValidationError(f"{name.capitalize()} must be at most {max_val}")
    
    return float(value)
