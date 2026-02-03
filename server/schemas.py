"""
Pydantic schemas for API request/response validation
"""

import re
from typing import Optional
from pydantic import BaseModel, field_validator

# Validation patterns
IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)
MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,62}$")
HOSTNAME_PATTERN = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.[A-Za-z0-9-]{1,63})*$")


class PlugCreate(BaseModel):
    name: str
    ip: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Plug name cannot be empty")
        if len(v) > 63:
            raise ValueError(f"Plug name too long: {len(v)} characters (max 63)")
        if not NAME_PATTERN.match(v):
            raise ValueError(
                "Plug name must start with alphanumeric and contain only alphanumeric, hyphens, and underscores"
            )
        return v

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("IP address cannot be empty")
        if not IP_PATTERN.match(v):
            raise ValueError(f"Invalid IP address format: '{v}'")
        return v


class PlugRemove(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Plug name cannot be empty")
        return v


class PlugUpdate(BaseModel):
    name: str
    ip: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Plug name cannot be empty")
        return v

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("IP address cannot be empty")
        if not IP_PATTERN.match(v):
            raise ValueError(f"Invalid IP address format: '{v}'")
        return v


class ServerCreate(BaseModel):
    name: str
    hostname: str
    mac: Optional[str] = None
    plug: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Server name cannot be empty")
        if len(v) > 63:
            raise ValueError(f"Server name too long: {len(v)} characters (max 63)")
        if not NAME_PATTERN.match(v):
            raise ValueError(
                "Server name must start with alphanumeric and contain only alphanumeric, hyphens, and underscores"
            )
        return v

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Hostname cannot be empty")
        if len(v) > 253:
            raise ValueError(f"Hostname too long: {len(v)} characters (max 253)")
        if not HOSTNAME_PATTERN.match(v):
            raise ValueError(f"Invalid hostname format: '{v}'")
        return v

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper().replace("-", ":")
        if not MAC_PATTERN.match(v):
            raise ValueError(f"Invalid MAC address format: '{v}'")
        return v


class ServerUpdate(BaseModel):
    name: str
    hostname: Optional[str] = None
    mac: Optional[str] = None
    plug: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Server name cannot be empty")
        return v

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            raise ValueError("Hostname cannot be empty")
        if len(v) > 253:
            raise ValueError(f"Hostname too long: {len(v)} characters (max 253)")
        if not HOSTNAME_PATTERN.match(v):
            raise ValueError(f"Invalid hostname format: '{v}'")
        return v

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper().replace("-", ":")
        if not MAC_PATTERN.match(v):
            raise ValueError(f"Invalid MAC address format: '{v}'")
        return v


class ServerRemove(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Server name cannot be empty")
        return v


class PowerAction(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Server name cannot be empty")
        return v


class ElectricityPrice(BaseModel):
    price: float  # Price per kWh

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Price cannot be negative")
        if v > 10:
            raise ValueError("Price seems unreasonably high (max 10 per kWh)")
        return v
