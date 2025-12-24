"""
Utilities Package for Disaster Management System

This package contains helper functions and validators:
- helpers: Formatting, time conversion, color utilities
- validators: Data validation functions
"""

from .helpers import (
    format_time_ago,
    get_signal_color,
    get_signal_indicator,
    calculate_priority,
    format_coordinates,
    get_status_color
)

from .validators import (
    validate_packet,
    validate_coordinates,
    validate_rssi,
    validate_victim_id
)

__all__ = [
    # Helper functions
    'format_time_ago',
    'get_signal_color',
    'get_signal_indicator',
    'calculate_priority',
    'format_coordinates',
    'get_status_color',
    
    # Validators
    'validate_packet',
    'validate_coordinates',
    'validate_rssi',
    'validate_victim_id'
]

__version__ = '1.0.0'