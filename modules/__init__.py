"""
Modules Package for Disaster Management System

This package contains core business logic modules:
- serial_reader: Serial port communication and packet parsing
- data_manager: Victim data management and CRUD operations
- analytics: Statistics calculation and data analysis
- map_manager: Map creation and rendering with Google Maps
"""

from .serial_reader import SerialReader
from .data_manager import DataManager
from .analytics import Analytics
from .map_manager import MapManager

__all__ = [
    'SerialReader',
    'DataManager',
    'Analytics',
    'MapManager'
]

__version__ = '1.0.0'
__author__ = 'Disaster Management Team'