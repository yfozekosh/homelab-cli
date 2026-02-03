"""Dependency injection for FastAPI endpoints"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from .config import Config
from .plug_service import PlugService
from .server_service import ServerService
from .power_service import PowerControlService
from .status_service import StatusService


class ServiceContainer:
    """Container for all application services"""
    
    _instance = None
    
    def __init__(self):
        config_path = Path(os.getenv("CONFIG_PATH", "/app/data/config.json"))
        self.config = Config(config_path)
        self.plug_service = PlugService()
        self.server_service = ServerService()
        self.power_service = PowerControlService(self.plug_service, self.server_service)
        self.status_service = StatusService(self.config, self.plug_service, self.server_service)
    
    @classmethod
    def get_instance(cls) -> "ServiceContainer":
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the container (useful for testing)"""
        cls._instance = None


@lru_cache
def get_service_container() -> ServiceContainer:
    """Get the service container (cached)"""
    return ServiceContainer.get_instance()


def get_config(container: ServiceContainer = Depends(get_service_container)) -> Config:
    """Dependency for Config"""
    return container.config


def get_plug_service(container: ServiceContainer = Depends(get_service_container)) -> PlugService:
    """Dependency for PlugService"""
    return container.plug_service


def get_server_service(container: ServiceContainer = Depends(get_service_container)) -> ServerService:
    """Dependency for ServerService"""
    return container.server_service


def get_power_service(container: ServiceContainer = Depends(get_service_container)) -> PowerControlService:
    """Dependency for PowerControlService"""
    return container.power_service


def get_status_service(container: ServiceContainer = Depends(get_service_container)) -> StatusService:
    """Dependency for StatusService"""
    return container.status_service


# Type aliases for cleaner endpoint signatures
ConfigDep = Annotated[Config, Depends(get_config)]
PlugServiceDep = Annotated[PlugService, Depends(get_plug_service)]
ServerServiceDep = Annotated[ServerService, Depends(get_server_service)]
PowerServiceDep = Annotated[PowerControlService, Depends(get_power_service)]
StatusServiceDep = Annotated[StatusService, Depends(get_status_service)]
