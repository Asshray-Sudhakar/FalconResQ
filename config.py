"""
Configuration Management for Disaster Management System
Loads settings from environment variables and defines constants
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==================== API KEYS ====================

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

# Validate API key presence
if not GOOGLE_MAPS_API_KEY:
    print("WARNING: GOOGLE_MAPS_API_KEY not found in .env file")
    print("Please create a .env file and add your Google Maps API key")

# ==================== SERIAL PORT SETTINGS ====================

# NO DEFAULT PORT - User must select in settings
DEFAULT_SERIAL_PORT = None  # Will be set by user in settings
DEFAULT_BAUD_RATE = 115200  # Default, but user can change

SERIAL_TIMEOUT = 1  # seconds

# Available baud rates for selection
AVAILABLE_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

# ==================== MAP SETTINGS ====================

# Default map center - Will be overridden by user's location
# These are fallback values if geolocation fails
DEFAULT_MAP_CENTER_LAT = float(os.getenv('MAP_CENTER_LAT', '13.022'))
DEFAULT_MAP_CENTER_LON = float(os.getenv('MAP_CENTER_LON', '77.587'))
DEFAULT_MAP_ZOOM = int(os.getenv('MAP_ZOOM', '14'))

# Map tile providers (fallback options)
MAP_TILE_PROVIDERS = {
    'google_roadmap': 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    'google_satellite': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    'google_hybrid': 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    'openstreetmap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
}

# ==================== PRIORITY THRESHOLDS ====================

# RSSI (Signal Strength) thresholds in dBm
RSSI_STRONG_THRESHOLD = -70  # Signal stronger than this is "good"
RSSI_WEAK_THRESHOLD = -85    # Signal weaker than this is "critical"

# Time thresholds in minutes
TIME_STALE_THRESHOLD = 20    # No update for this long = stale data
TIME_CRITICAL_THRESHOLD = 15 # No update for this long = high priority

# ==================== STATUS DEFINITIONS ====================

# Victim status options
STATUS_STRANDED = "STRANDED"
STATUS_EN_ROUTE = "EN_ROUTE"
STATUS_RESCUED = "RESCUED"

ALL_STATUSES = [STATUS_STRANDED, STATUS_EN_ROUTE, STATUS_RESCUED]

# ==================== COLOR SCHEMES ====================

# Status colors (for UI elements)
STATUS_COLORS = {
    STATUS_STRANDED: "#FF4445",  # Red
    STATUS_EN_ROUTE: "#FFA500",  # Orange
    STATUS_RESCUED: "#00CC66"    # Green
}

# Signal strength colors
SIGNAL_COLORS = {
    'strong': "#00CC66",   # Green
    'medium': "#FFCC00",   # Yellow
    'weak': "#FF4444"      # Red
}

# Map marker colors (for Folium)
MARKER_COLORS = {
    STATUS_STRANDED: 'red',
    STATUS_EN_ROUTE: 'orange',
    STATUS_RESCUED: 'green'
}

# ==================== DATA PERSISTENCE ====================

# Data backup settings
BACKUP_INTERVAL_SECONDS = 30  # Auto-save every 30 seconds
BACKUP_FILE_PATH = os.path.join('data', 'victims_backup.json')
RESCUE_LOG_PATH = os.path.join('data', 'rescue_log.csv')

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# ==================== UI SETTINGS ====================

# NO AUTOMATIC REFRESH - Updates on packet receive
DASHBOARD_REFRESH_INTERVAL = 0  # Disabled - real-time updates
ANALYTICS_REFRESH_INTERVAL = 0  # Disabled - real-time updates

# Table display settings
MAX_ROWS_DISPLAY = 100
DEFAULT_SORT_COLUMN = 'LAST_UPDATE'
DEFAULT_SORT_ORDER = 'desc'

# ==================== GEOGRAPHIC SETTINGS ====================

# Grid sector size for density analysis (in decimal degrees)
# Approximately 100m x 100m at equator
SECTOR_SIZE_LAT = 0.001
SECTOR_SIZE_LON = 0.001

# ==================== VALIDATION RULES ====================

# Coordinate validation ranges
VALID_LAT_RANGE = (-90, 90)
VALID_LON_RANGE = (-180, 180)

# RSSI validation range (typical LoRa values)
VALID_RSSI_RANGE = (-150, -30)

# ID validation
MIN_VICTIM_ID = 1
MAX_VICTIM_ID = 9999

# ==================== EXPORT SETTINGS ====================

# CSV export columns
EXPORT_COLUMNS = [
    'ID', 'LAT', 'LON', 'STATUS', 'RSSI',
    'FIRST_DETECTED', 'LAST_UPDATE', 'RESCUED_TIME',
    'RESCUED_BY', 'UPDATE_COUNT'
]

# Export filename format
EXPORT_FILENAME_FORMAT = "{type}_victims_{timestamp}.csv"

# ==================== OPERATOR SETTINGS ====================

# Default operator name
DEFAULT_OPERATOR_NAME = "Operator"

# ==================== HARDWARE SPECIFICATIONS ====================

# Device information (for documentation/reference)
VICTIM_DEVICE = "WiFi LoRa 32(V3), ESP32S3 + SX1262"
DRONE_DEVICE = "Wireless Tracker, ESP32S3 + SX1262 + GPS"
GROUND_STATION_DEVICE = "WiFi LoRa 32(V3), ESP32S3 + SX1262"

# Communication protocol
COMMUNICATION_PROTOCOL = "Meshtastic / LoRaWAN Compatible"

# ==================== DEBUGGING ====================

# Debug mode
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

# Logging level
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# ==================== HELPER FUNCTIONS ====================

def get_priority_threshold_config():
    """Return priority threshold configuration"""
    return {
        'rssi_weak': RSSI_WEAK_THRESHOLD,
        'rssi_strong': RSSI_STRONG_THRESHOLD,
        'time_critical': TIME_CRITICAL_THRESHOLD,
        'time_stale': TIME_STALE_THRESHOLD
    }

def get_map_config():
    """Return map configuration"""
    return {
        'center': [DEFAULT_MAP_CENTER_LAT, DEFAULT_MAP_CENTER_LON],
        'zoom': DEFAULT_MAP_ZOOM,
        'api_key': GOOGLE_MAPS_API_KEY
    }

def get_serial_config():
    """Return serial port configuration"""
    return {
        'port': DEFAULT_SERIAL_PORT,  # Will be None initially
        'baudrate': DEFAULT_BAUD_RATE,
        'timeout': SERIAL_TIMEOUT,
        'available_baudrates': AVAILABLE_BAUD_RATES
    }

def validate_api_key():
    """Check if Google Maps API key is configured"""
    return bool(GOOGLE_MAPS_API_KEY and len(GOOGLE_MAPS_API_KEY) > 10)

# ==================== CONFIGURATION VALIDATION ====================

def validate_configuration():
    """Validate all configuration settings"""
    issues = []
    
    # Check API key
    if not validate_api_key():
        issues.append("Google Maps API key not configured or invalid")
    
    # Check data directory
    if not os.path.exists('data'):
        try:
            os.makedirs('data')
        except Exception as e:
            issues.append(f"Cannot create data directory: {e}")
    
    # Check thresholds
    if RSSI_WEAK_THRESHOLD >= RSSI_STRONG_THRESHOLD:
        issues.append("RSSI thresholds are misconfigured")
    
    if TIME_CRITICAL_THRESHOLD >= TIME_STALE_THRESHOLD:
        issues.append("Time thresholds are misconfigured")
    
    return issues

# Run validation on import
_config_issues = validate_configuration()
if _config_issues and DEBUG_MODE:
    print("Configuration Issues:")
    for issue in _config_issues:
        print(f"  - {issue}")