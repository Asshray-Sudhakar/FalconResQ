"""
Validators Module
Data validation functions for ensuring data integrity
Validates packets, coordinates, and system inputs
"""

from typing import Dict, Any, Tuple, Optional, List
import re
import config


def validate_packet(packet: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate incoming data packet from serial port
    
    Args:
        packet: Data packet dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if packet is valid, False otherwise
        - error_message: None if valid, error description if invalid
    """
    
    # Check if packet is a dictionary
    if not isinstance(packet, dict):
        return False, "Packet must be a dictionary"
    
    # Check required fields
    required_fields = ['ID', 'LAT', 'LON', 'TIME']
    missing_fields = [field for field in required_fields if field not in packet]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate victim ID
    is_valid, error = validate_victim_id(packet['ID'])
    if not is_valid:
        return False, f"Invalid ID: {error}"
    
    # Validate coordinates
    is_valid, error = validate_coordinates(packet['LAT'], packet['LON'])
    if not is_valid:
        return False, f"Invalid coordinates: {error}"
    
    # Validate time format
    is_valid, error = validate_time_format(packet['TIME'])
    if not is_valid:
        return False, f"Invalid time: {error}"
    
    # Validate RSSI if present
    if 'RSSI' in packet:
        is_valid, error = validate_rssi(packet['RSSI'])
        if not is_valid:
            return False, f"Invalid RSSI: {error}"
    
    return True, None


def validate_victim_id(victim_id: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate victim ID
    
    Args:
        victim_id: Victim ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check type
    try:
        vid = int(victim_id)
    except (ValueError, TypeError):
        return False, "ID must be a number"
    
    # Check range
    if vid < config.MIN_VICTIM_ID or vid > config.MAX_VICTIM_ID:
        return False, f"ID must be between {config.MIN_VICTIM_ID} and {config.MAX_VICTIM_ID}"
    
    return True, None


def validate_coordinates(lat: Any, lon: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate latitude and longitude coordinates
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check types
    try:
        lat_float = float(lat)
        lon_float = float(lon)
    except (ValueError, TypeError):
        return False, "Coordinates must be numbers"
    
    # Validate latitude range
    min_lat, max_lat = config.VALID_LAT_RANGE
    if not (min_lat <= lat_float <= max_lat):
        return False, f"Latitude must be between {min_lat} and {max_lat}"
    
    # Validate longitude range
    min_lon, max_lon = config.VALID_LON_RANGE
    if not (min_lon <= lon_float <= max_lon):
        return False, f"Longitude must be between {min_lon} and {max_lon}"
    
    # Check for zero coordinates (likely invalid)
    if lat_float == 0 and lon_float == 0:
        return False, "Coordinates cannot both be zero"
    
    return True, None


def validate_rssi(rssi: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate RSSI (signal strength) value
    
    Args:
        rssi: RSSI value in dBm
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check type
    try:
        rssi_int = int(rssi)
    except (ValueError, TypeError):
        return False, "RSSI must be a number"
    
    # Allow default value
    if rssi_int == -999:
        return True, None
    
    # Check range
    min_rssi, max_rssi = config.VALID_RSSI_RANGE
    if not (min_rssi <= rssi_int <= max_rssi):
        return False, f"RSSI must be between {min_rssi} and {max_rssi} dBm"
    
    return True, None


def validate_time_format(time_str: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate time string format
    
    Args:
        time_str: Time string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check type
    if not isinstance(time_str, str):
        return False, "Time must be a string"
    
    # Check if empty
    if not time_str.strip():
        return False, "Time cannot be empty"
    
    # Common time formats
    valid_patterns = [
        r'^\d{2}:\d{2}$',           # HH:MM
        r'^\d{2}:\d{2}:\d{2}$',     # HH:MM:SS
        r'^\d{1,2}:\d{2}$',         # H:MM or HH:MM
        r'^\d{1,2}:\d{2}:\d{2}$'    # H:MM:SS or HH:MM:SS
    ]
    
    # Check if matches any valid pattern
    for pattern in valid_patterns:
        if re.match(pattern, time_str):
            return True, None
    
    return False, "Time must be in format HH:MM or HH:MM:SS"


def validate_status(status: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate victim status
    
    Args:
        status: Status string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(status, str):
        return False, "Status must be a string"
    
    if status not in config.ALL_STATUSES:
        return False, f"Status must be one of: {', '.join(config.ALL_STATUSES)}"
    
    return True, None


def validate_operator_name(name: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate operator name
    
    Args:
        name: Operator name
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(name, str):
        return False, "Name must be a string"
    
    if not name.strip():
        return False, "Name cannot be empty"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False, "Name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    return True, None


def validate_timestamp(timestamp_str: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate timestamp string format (YYYY-MM-DD HH:MM:SS)
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(timestamp_str, str):
        return False, "Timestamp must be a string"
    
    from datetime import datetime
    
    try:
        datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return True, None
    except ValueError:
        return False, "Timestamp must be in format YYYY-MM-DD HH:MM:SS"


def validate_port_name(port: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate serial port name
    
    Args:
        port: Port name (e.g., "COM20", "/dev/ttyUSB0")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(port, str):
        return False, "Port name must be a string"
    
    if not port.strip():
        return False, "Port name cannot be empty"
    
    # Windows COM ports
    if re.match(r'^COM\d+$', port, re.IGNORECASE):
        return True, None
    
    # Linux/Mac serial ports
    if re.match(r'^/dev/(tty|cu)\.[a-zA-Z0-9\-_]+$', port):
        return True, None
    
    if re.match(r'^/dev/ttyUSB\d+$', port):
        return True, None
    
    if re.match(r'^/dev/ttyACM\d+$', port):
        return True, None
    
    return False, "Invalid port name format"


def validate_baud_rate(baud_rate: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate baud rate
    
    Args:
        baud_rate: Baud rate value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    try:
        baud = int(baud_rate)
    except (ValueError, TypeError):
        return False, "Baud rate must be a number"
    
    # Common baud rates
    valid_baud_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
    
    if baud not in valid_baud_rates:
        return False, f"Baud rate must be one of: {', '.join(map(str, valid_baud_rates))}"
    
    return True, None


def validate_notes(notes: Any, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Validate rescue notes
    
    Args:
        notes: Notes text
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(notes, str):
        return False, "Notes must be a string"
    
    if len(notes) > max_length:
        return False, f"Notes must be less than {max_length} characters"
    
    return True, None


def validate_json_structure(data: Any, required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON data structure has required fields
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None


def validate_file_path(file_path: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate file path format
    
    Args:
        file_path: File path string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(file_path, str):
        return False, "File path must be a string"
    
    if not file_path.strip():
        return False, "File path cannot be empty"
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        if char in file_path:
            return False, f"File path cannot contain '{char}'"
    
    # Check extension for common formats
    valid_extensions = ['.json', '.csv', '.txt', '.log']
    has_valid_extension = any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    if not has_valid_extension:
        return False, f"File must have one of these extensions: {', '.join(valid_extensions)}"
    
    return True, None


def validate_zoom_level(zoom: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate map zoom level
    
    Args:
        zoom: Zoom level value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    try:
        zoom_int = int(zoom)
    except (ValueError, TypeError):
        return False, "Zoom level must be a number"
    
    if not (1 <= zoom_int <= 20):
        return False, "Zoom level must be between 1 and 20"
    
    return True, None


def validate_priority(priority: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate priority level
    
    Args:
        priority: Priority string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(priority, str):
        return False, "Priority must be a string"
    
    valid_priorities = ["HIGH", "MEDIUM", "LOW"]
    
    if priority not in valid_priorities:
        return False, f"Priority must be one of: {', '.join(valid_priorities)}"
    
    return True, None


def validate_threshold_value(value: Any, min_val: float, max_val: float, name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate threshold configuration value
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the threshold (for error messages)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return False, f"{name} must be a number"
    
    if not (min_val <= val_float <= max_val):
        return False, f"{name} must be between {min_val} and {max_val}"
    
    return True, None


def validate_update_count(count: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate packet update count
    
    Args:
        count: Update count value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    try:
        count_int = int(count)
    except (ValueError, TypeError):
        return False, "Update count must be a number"
    
    if count_int < 0:
        return False, "Update count cannot be negative"
    
    if count_int > 10000:
        return False, "Update count exceeds maximum (10000)"
    
    return True, None


def sanitize_input(text: str, max_length: int = 200) -> str:
    """
    Sanitize user input by removing dangerous characters
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    
    if not isinstance(text, str):
        return ""
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()
    
    # Limit length
    sanitized = sanitized[:max_length]
    
    return sanitized


def validate_export_format(format_type: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate export file format type
    
    Args:
        format_type: Format type string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not isinstance(format_type, str):
        return False, "Format type must be a string"
    
    valid_formats = ['csv', 'json', 'txt']
    
    if format_type.lower() not in valid_formats:
        return False, f"Format must be one of: {', '.join(valid_formats)}"
    
    return True, None


def validate_sector_size(size: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate geographic sector size
    
    Args:
        size: Sector size in decimal degrees
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    try:
        size_float = float(size)
    except (ValueError, TypeError):
        return False, "Sector size must be a number"
    
    if not (0.0001 <= size_float <= 1.0):
        return False, "Sector size must be between 0.0001 and 1.0 degrees"
    
    return True, None


def is_valid_packet_batch(packets: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], List[int]]:
    """
    Validate a batch of packets
    
    Args:
        packets: List of packet dictionaries
        
    Returns:
        Tuple of (is_valid, error_message, invalid_indices)
        - is_valid: True if all packets valid
        - error_message: Description of errors
        - invalid_indices: List of invalid packet indices
    """
    
    if not isinstance(packets, list):
        return False, "Packets must be a list", []
    
    if not packets:
        return False, "Packet list is empty", []
    
    invalid_indices = []
    errors = []
    
    for idx, packet in enumerate(packets):
        is_valid, error = validate_packet(packet)
        if not is_valid:
            invalid_indices.append(idx)
            errors.append(f"Packet {idx}: {error}")
    
    if invalid_indices:
        error_msg = "; ".join(errors[:5])  # Limit to first 5 errors
        if len(errors) > 5:
            error_msg += f" ... and {len(errors) - 5} more errors"
        return False, error_msg, invalid_indices
    
    return True, None, []