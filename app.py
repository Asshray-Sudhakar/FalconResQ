"""
Disaster Management Ground Station - Main Application Entry Point
Handles navigation, sidebar, and global state initialization
"""

import streamlit as st
from datetime import datetime
import threading
import time

# Import configuration
import config

# Import modules
from modules.serial_reader import SerialReader
from modules.data_manager import DataManager
from modules.websocket_server import start_websocket_server, broadcast_packet
from utils.helpers import format_time_ago

# Page Configuration
st.set_page_config(
    page_title="FalconResQ: Disaster Management Ground Station",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
FalconResQ: Disaster Management System using Drone Technology

By: Asshray Sudhakara ECE'27 
\n Student of EvRe Domain & Aviation Coordinator @ MARVEL, UVCE
        """
    }
)

# ==================== GEOLOCATION DETECTION ====================

def get_user_location():
    """Get user's current location using browser geolocation"""
    
    # JavaScript to get geolocation
    location_js = """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        lat: position.coords.latitude,
                        lon: position.coords.longitude
                    }, '*');
                },
                function(error) {
                    console.log('Geolocation error:', error);
                }
            );
        }
    }
    getLocation();
    </script>
    """
    return location_js

# ==================== SESSION STATE INITIALIZATION ====================

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Data Manager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    # Serial Reader
    if 'serial_reader' not in st.session_state:
        st.session_state.serial_reader = SerialReader()
    
    # Connection State
    if 'serial_connected' not in st.session_state:
        st.session_state.serial_connected = False
    
    # Operator Info
    if 'operator_name' not in st.session_state:
        st.session_state.operator_name = "Operator"
    
    # Operation Tracking
    if 'operation_start_time' not in st.session_state:
        st.session_state.operation_start_time = datetime.now()
    
    # Statistics
    if 'packet_count' not in st.session_state:
        st.session_state.packet_count = 0
    
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0
    
    if 'last_packet_time' not in st.session_state:
        st.session_state.last_packet_time = None
    
    # UI State
    if 'show_rescued' not in st.session_state:
        st.session_state.show_rescued = True
    
    if 'show_heatmap' not in st.session_state:
        st.session_state.show_heatmap = False
    
    if 'show_priority_only' not in st.session_state:
        st.session_state.show_priority_only = False
    
    # Serial Port Settings - NO DEFAULTS
    if 'serial_port' not in st.session_state:
        st.session_state.serial_port = None  # User must select
    
    if 'baud_rate' not in st.session_state:
        st.session_state.baud_rate = 115200  # Default but user can change
    
    # Map Settings - Use geolocation or fallback
    if 'map_center' not in st.session_state:
        # Try to get user's location, fallback to default
        st.session_state.map_center = [13.022, 77.587]  # Fallback
        st.session_state.location_detected = False
    
    # Rescue Centre Location - dynamically loaded from browser geolocation
    if 'rescue_centre_lat' not in st.session_state:
        st.session_state.rescue_centre_lat = 13.022
    
    if 'rescue_centre_lon' not in st.session_state:
        st.session_state.rescue_centre_lon = 77.587
    
    # Check if user has allowed geolocation via settings
    # The JavaScript in settings.py stores location in browser localStorage
    if 'location_detected' not in st.session_state:
        st.session_state.location_detected = False
    
    if 'map_zoom' not in st.session_state:
        st.session_state.map_zoom = 14
    
    # ==================== DYNAMIC THRESHOLD SETTINGS ====================
    # RSSI Thresholds
    if 'rssi_strong_threshold' not in st.session_state:
        st.session_state.rssi_strong_threshold = config.RSSI_STRONG_THRESHOLD
    
    if 'rssi_weak_threshold' not in st.session_state:
        st.session_state.rssi_weak_threshold = config.RSSI_WEAK_THRESHOLD
    
    # Time-based Thresholds
    if 'time_critical_threshold' not in st.session_state:
        st.session_state.time_critical_threshold = config.TIME_CRITICAL_THRESHOLD
    
    # Force rerun flag for real-time updates
    if 'force_rerun' not in st.session_state:
        st.session_state.force_rerun = False
    
    # WebSocket Server for real-time updates
    if 'ws_server_started' not in st.session_state:
        start_websocket_server()
        st.session_state.ws_server_started = True

# Initialize session state
initialize_session_state()

# Check if we need to rerun due to new packet - do this EARLY for fast updates
if st.session_state.get('force_rerun', False):
    st.session_state.force_rerun = False
    st.rerun()

# ==================== AUTO-LOAD GEOLOCATION FROM BROWSER ====================
# Read geolocation from browser localStorage (set by settings page)
import streamlit.components.v1 as components

# This component reads from browser localStorage and updates rescue centre location
auto_geolocation_component = """
<script>
// Try to get saved location from browser localStorage
(function() {
    try {
        const userLat = parseFloat(localStorage.getItem('user_lat'));
        const userLon = parseFloat(localStorage.getItem('user_lon'));
        
        if (userLat && userLon && !isNaN(userLat) && !isNaN(userLon)) {
            // Found valid geolocation, mark it as detected
            sessionStorage.setItem('geo_lat', userLat.toString());
            sessionStorage.setItem('geo_lon', userLon.toString());
        }
    } catch(e) {
        // Geolocation not available
    }
})();
</script>
"""

# Try to load geolocation from browser
try:
    components.html(auto_geolocation_component, height=0)
    
    # Create a container to check geolocation status
    if st.session_state.location_detected:
        # User has clicked to detect location in settings
        # Try to update from browser's detected location
        geolocation_check = """
        <script>
        (function() {
            try {
                const userLat = parseFloat(localStorage.getItem('user_lat'));
                const userLon = parseFloat(localStorage.getItem('user_lon'));
                
                if (userLat && userLon && !isNaN(userLat) && !isNaN(userLon)) {
                    // Update parent window (Streamlit) about the new location
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        data: {lat: userLat, lon: userLon}
                    }, '*');
                }
            } catch(e) {}
        })();
        </script>
        """
        try:
            components.html(geolocation_check, height=0)
        except:
            pass
except:
    pass

# ==================== SIDEBAR ====================

def render_sidebar():
    """Render the sidebar with navigation and status"""
    
    with st.sidebar:
        st.title("FalconResQ Ground Station Control")
        
        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Select Page",
            ["Dashboard", "Analytics", "Export Data", "Settings"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Connection Status
        st.subheader("Connection Status")
        
        serial_reader = st.session_state.serial_reader
        data_manager = st.session_state.data_manager
        
        # Check if port is selected
        if st.session_state.serial_port is None:
            st.warning("No COM port selected")
            st.info("Go to Settings to select COM port")
        
        elif st.session_state.serial_connected:
            st.success(f"Connected to {st.session_state.serial_port}")
            st.caption(f"Baud: {st.session_state.baud_rate}")
            
            if st.button("Disconnect", use_container_width=True):
                serial_reader.stop_reading()
                st.session_state.serial_connected = False
                st.rerun()
        else:
            st.error("Disconnected")
            
            if st.button("Connect to Serial", use_container_width=True, type="primary", 
                        disabled=(st.session_state.serial_port is None)):
                try:
                    # Start serial reading in background thread
                    def serial_callback(packet):
                        try:
                            data_manager.add_or_update_victim(packet)
                            # Safely update session state counters
                            try:
                                st.session_state.packet_count += 1
                                st.session_state.last_packet_time = datetime.now()
                            except:
                                pass  # Session state not ready yet
                            # Broadcast to WebSocket clients
                            broadcast_packet(packet)
                            # Trigger rerun on new packet
                            st.session_state.force_rerun = True
                        except Exception as e:
                            print(f"Error in serial callback: {e}")
                    
                    def error_callback():
                        try:
                            # Safely update error counter (ignore if not ready)
                            try:
                                st.session_state.error_count += 1
                            except:
                                pass
                        except Exception as e:
                            print(f"Error in error callback: {e}")
                    
                    success = serial_reader.start_reading(
                        port=st.session_state.serial_port,
                        baudrate=st.session_state.baud_rate,
                        on_packet_received=serial_callback,
                        on_error=error_callback
                    )
                    
                    if success:
                        st.session_state.serial_connected = True
                        st.success("Connected successfully!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to connect")
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
        
        st.divider()
        
        # Quick Statistics
        st.subheader("Quick Statistics")
        
        stats = data_manager.get_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats['total'])
            st.metric("Stranded", stats['stranded'])
        with col2:
            st.metric("Rescued", stats['rescued'])
            st.metric("En-Route", stats['enroute'])
        
        st.divider()
        
        # Data Stream Info
        st.subheader("Data Stream")
        
        st.metric("Packets", st.session_state.packet_count)
        st.metric("Errors", st.session_state.error_count)
        
        if st.session_state.last_packet_time:
            seconds_ago = (datetime.now() - st.session_state.last_packet_time).total_seconds()
            st.metric("Last Packet", f"{int(seconds_ago)}s ago")
        else:
            st.metric("Last Packet", "Never")
        
        st.divider()
        
        # Operation Duration
        duration = datetime.now() - st.session_state.operation_start_time
        hours = int(duration.total_seconds() / 3600)
        minutes = int((duration.total_seconds() % 3600) / 60)
        st.metric("Operation Time", f"{hours}h {minutes}m")
        
        return page

# ==================== MAIN APPLICATION ====================

def main():
    """Main application logic"""
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Route to appropriate page
    if selected_page == "Dashboard":
        from _pages import dashboard
        dashboard.render_dashboard()
    
    elif selected_page == "Analytics":
        from _pages import analytics
        analytics.render_analytics()
    
    elif selected_page == "Export Data":
        from _pages import export
        export.render_export()
    
    elif selected_page == "Settings":
        from _pages import settings
        settings.render_settings()

# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    main()