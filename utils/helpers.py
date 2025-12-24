"""
Helper Utilities Module
Common utility functions used across the application
Formatting, calculations, and conversions
"""

from datetime import datetime
from typing import Tuple, Dict, Any, Optional
import config


def format_time_ago(timestamp_str: str) -> str:
    """
    Convert timestamp to human-readable 'X time ago' format
    
    Args:
        timestamp_str: Timestamp string in format "YYYY-MM-DD HH:MM:SS"
        
    Returns:
        Human-readable time string (e.g., "5 minutes ago")
    """
    
    if not timestamp_str:
        return "Unknown"
    
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - timestamp
        
        seconds = int(delta.total_seconds())
        
        if seconds < 0:
            return "Just now"
        elif seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''} ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
            
    except (ValueError, TypeError):
        return "Invalid timestamp"


def calculate_priority(victim_data: Dict[str, Any], 
                      rssi_strong_threshold: int = None, 
                      rssi_weak_threshold: int = None,
                      time_critical_threshold: int = None) -> Tuple[str, str]:
    """
    Calculate victim priority based on RSSI and last update time
    
    Args:
        victim_data: Dictionary containing victim information
        rssi_strong_threshold: Signal strong threshold (uses config default if None)
        rssi_weak_threshold: Signal weak threshold (uses config default if None)
        time_critical_threshold: Critical time threshold in minutes (uses config default if None)
        
    Returns:
        Tuple of (priority_level, priority_label)
        - priority_level: "HIGH", "MEDIUM", or "LOW"
        - priority_label: Human-readable label
    """
    
    # Use provided thresholds or fall back to config defaults
    rssi_strong = rssi_strong_threshold if rssi_strong_threshold is not None else config.RSSI_STRONG_THRESHOLD
    rssi_weak = rssi_weak_threshold if rssi_weak_threshold is not None else config.RSSI_WEAK_THRESHOLD
    time_critical = time_critical_threshold if time_critical_threshold is not None else config.TIME_CRITICAL_THRESHOLD
    
    rssi = victim_data.get('RSSI', -999)
    last_update_str = victim_data.get('LAST_UPDATE')
    
    # Calculate time since last update
    time_since_update_minutes = 0
    if last_update_str:
        try:
            last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
            time_since_update_minutes = (datetime.now() - last_update).total_seconds() / 60
        except (ValueError, TypeError):
            time_since_update_minutes = 0
    
    # HIGH Priority conditions
    if rssi < rssi_weak or time_since_update_minutes > time_critical:
        return "HIGH", "Critical"
    
    # MEDIUM Priority conditions
    elif rssi_weak <= rssi < rssi_strong and time_since_update_minutes <= time_critical:
        return "MEDIUM", "Standard"
    
    # LOW Priority (good signal, recently updated)
    else:
        return "LOW", "Stable"


def get_signal_color(rssi: int, rssi_strong_threshold: int = None, rssi_weak_threshold: int = None) -> Tuple[str, str]:
    """
    Get color representation for signal strength
    
    Args:
        rssi: Signal strength in dBm
        rssi_strong_threshold: Strong signal threshold (uses config default if None)
        rssi_weak_threshold: Weak signal threshold (uses config default if None)
        
    Returns:
        Tuple of (label, hex_color)
    """
    
    # Use provided thresholds or fall back to config defaults
    rssi_strong = rssi_strong_threshold if rssi_strong_threshold is not None else config.RSSI_STRONG_THRESHOLD
    rssi_weak = rssi_weak_threshold if rssi_weak_threshold is not None else config.RSSI_WEAK_THRESHOLD
    
    if rssi > rssi_strong:
        return "Strong", config.SIGNAL_COLORS['strong']
    elif rssi_weak <= rssi <= rssi_strong:
        return "Medium", config.SIGNAL_COLORS['medium']
    else:
        return "Weak", config.SIGNAL_COLORS['weak']


def get_signal_indicator(rssi: int, rssi_strong_threshold: int = None, rssi_weak_threshold: int = None) -> str:
    """
    Get text indicator for signal strength (for non-UI contexts)
    
    Args:
        rssi: Signal strength in dBm
        rssi_strong_threshold: Strong signal threshold (uses config default if None)
        rssi_weak_threshold: Weak signal threshold (uses config default if None)
        
    Returns:
        Text indicator: "STRONG", "MEDIUM", or "WEAK"
    """
    
    # Use provided thresholds or fall back to config defaults
    rssi_strong = rssi_strong_threshold if rssi_strong_threshold is not None else config.RSSI_STRONG_THRESHOLD
    rssi_weak = rssi_weak_threshold if rssi_weak_threshold is not None else config.RSSI_WEAK_THRESHOLD
    
    if rssi > rssi_strong:
        return "STRONG"
    elif rssi_weak <= rssi <= rssi_strong:
        return "MEDIUM"
    else:
        return "WEAK"


def format_coordinates(lat: float, lon: float, precision: int = 6) -> str:
    """
    Format coordinates to string with specified precision
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        precision: Number of decimal places (default 6)
        
    Returns:
        Formatted coordinate string
    """
    
    return f"{lat:.{precision}f}, {lon:.{precision}f}"


def get_status_color(status: str) -> str:
    """
    Get color hex code for victim status
    
    Args:
        status: Victim status (STRANDED, EN_ROUTE, RESCUED)
        
    Returns:
        Hex color code
    """
    
    return config.STATUS_COLORS.get(status, "#999999")


def get_marker_color(status: str) -> str:
    """
    Get marker color name for maps (Folium compatible)
    
    Args:
        status: Victim status
        
    Returns:
        Color name for Folium markers
    """
    
    return config.MARKER_COLORS.get(status, 'gray')


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d {hours}h"


def format_rssi_display(rssi: int) -> str:
    """
    Format RSSI value for display with label
    
    Args:
        rssi: Signal strength in dBm
        
    Returns:
        Formatted RSSI string with label
    """
    
    if rssi == -999:
        return "No Signal"
    
    label, _ = get_signal_color(rssi)
    return f"{rssi} dBm ({label})"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: First coordinate (decimal degrees)
        lat2, lon2: Second coordinate (decimal degrees)
        
    Returns:
        Distance in kilometers
    """
    
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance


def format_distance(distance_km: float) -> str:
    """
    Format distance for display
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        Formatted distance string
    """
    
    if distance_km < 1:
        meters = int(distance_km * 1000)
        return f"{meters}m"
    else:
        return f"{distance_km:.2f}km"


def get_priority_color(priority: str) -> str:
    """
    Get color for priority level
    
    Args:
        priority: Priority level (HIGH, MEDIUM, LOW)
        
    Returns:
        Hex color code
    """
    
    priority_colors = {
        "HIGH": "#dc3545",      # Red
        "MEDIUM": "#ffc107",    # Yellow
        "LOW": "#28a745"        # Green
    }
    
    return priority_colors.get(priority, "#6c757d")


def format_timestamp(timestamp_str: str, format_type: str = "display") -> str:
    """
    Format timestamp for different contexts
    
    Args:
        timestamp_str: Timestamp string
        format_type: "display", "export", or "filename"
        
    Returns:
        Formatted timestamp string
    """
    
    if not timestamp_str:
        return ""
    
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        if format_type == "display":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "export":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "filename":
            return dt.strftime("%Y%m%d_%H%M%S")
        else:
            return timestamp_str
            
    except (ValueError, TypeError):
        return timestamp_str


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format value as percentage
    
    Args:
        value: Value to format (0-100)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    
    return f"{value:.{decimals}f}%"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Result of division or default
    """
    
    if denominator == 0:
        return default
    
    return numerator / denominator


def format_count(count: int, singular: str, plural: str = None) -> str:
    """
    Format count with appropriate singular/plural noun
    
    Args:
        count: Number to format
        singular: Singular form of noun
        plural: Plural form (adds 's' if None)
        
    Returns:
        Formatted count string
    """
    
    if plural is None:
        plural = singular + "s"
    
    if count == 1:
        return f"{count} {singular}"
    else:
        return f"{count} {plural}"


def get_time_category(timestamp_str: str) -> str:
    """
    Categorize timestamp into time ranges
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        Category: "recent", "hour_ago", "today", "older"
    """
    
    if not timestamp_str:
        return "unknown"
    
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - timestamp
        
        minutes = delta.total_seconds() / 60
        
        if minutes < 10:
            return "recent"
        elif minutes < 60:
            return "hour_ago"
        elif delta.days == 0:
            return "today"
        else:
            return "older"
            
    except (ValueError, TypeError):
        return "unknown"


def validate_rssi_value(rssi: int) -> bool:
    """
    Validate if RSSI value is within reasonable range
    
    Args:
        rssi: RSSI value in dBm
        
    Returns:
        True if valid, False otherwise
    """
    
    if rssi == -999:  # Default value for missing RSSI
        return True
    
    return config.VALID_RSSI_RANGE[0] <= rssi <= config.VALID_RSSI_RANGE[1]


def get_status_badge_html(status: str) -> str:
    """
    Generate HTML badge for status display
    
    Args:
        status: Victim status
        
    Returns:
        HTML string for badge
    """
    
    color = get_status_color(status)
    
    return f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{status}</span>'


def get_priority_badge_html(priority: str) -> str:
    """
    Generate HTML badge for priority display
    
    Args:
        priority: Priority level
        
    Returns:
        HTML string for badge
    """
    
    color = get_priority_color(priority)
    text_color = "white" if priority == "HIGH" else "black"
    
    return f'<span style="background-color: {color}; color: {text_color}; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{priority}</span>'


def format_signal_bar(rssi: int, width: int = 100) -> str:
    """
    Generate HTML progress bar for signal strength
    
    Args:
        rssi: RSSI value
        width: Width of bar in pixels
        
    Returns:
        HTML string for progress bar
    """
    
    # Normalize RSSI to 0-100 scale
    # Typical range: -120 (worst) to -30 (best)
    min_rssi = -120
    max_rssi = -30
    
    percentage = ((rssi - min_rssi) / (max_rssi - min_rssi)) * 100
    percentage = max(0, min(100, percentage))  # Clamp to 0-100
    
    _, color = get_signal_color(rssi)
    
    return f"""
    <div style="width: {width}px; background-color: #e0e0e0; border-radius: 3px; overflow: hidden;">
        <div style="width: {percentage}%; background-color: {color}; height: 15px; transition: width 0.3s;"></div>
    </div>
    """


def generate_victim_summary(victim: Dict[str, Any]) -> str:
    """
    Generate one-line summary of victim information
    
    Args:
        victim: Victim data dictionary
        
    Returns:
        Summary string
    """
    
    vid = victim['ID']
    status = victim['STATUS']
    rssi_display = format_rssi_display(victim['RSSI'])
    time_ago = format_time_ago(victim['LAST_UPDATE'])
    
    return f"ID {vid} | {status} | {rssi_display} | Last seen {time_ago}"


def is_stale_data(timestamp_str: str) -> bool:
    """
    Check if data is stale (no recent updates)
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        True if stale, False otherwise
    """
    
    if not timestamp_str:
        return True
    
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        minutes_ago = (datetime.now() - timestamp).total_seconds() / 60
        
        return minutes_ago > config.TIME_STALE_THRESHOLD
        
    except (ValueError, TypeError):
        return True


def calculate_rescue_duration(first_detected: str, rescued_time: str) -> Optional[float]:
    """
    Calculate time taken from detection to rescue
    
    Args:
        first_detected: First detection timestamp
        rescued_time: Rescue timestamp
        
    Returns:
        Duration in minutes, or None if calculation fails
    """
    
    try:
        detected = datetime.strptime(first_detected, "%Y-%m-%d %H:%M:%S")
        rescued = datetime.strptime(rescued_time, "%Y-%m-%d %H:%M:%S")
        
        duration_seconds = (rescued - detected).total_seconds()
        duration_minutes = duration_seconds / 60
        
        return duration_minutes if duration_minutes >= 0 else None
        
    except (ValueError, TypeError):
        return None