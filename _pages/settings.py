"""
Settings Page - Configuration and System Management
Professional settings interface for system configuration
"""

import streamlit as st
import serial.tools.list_ports
from datetime import datetime
import os
import streamlit.components.v1 as components

import config
from streamlit_js_eval import get_geolocation


def render_settings():
    """Render the settings page"""
    
    # Page header
    st.title("System Settings & Configuration")
    st.markdown("Configure system parameters and manage operation settings")
    
    # Create tabs for different setting categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Serial Port",
        "Map Configuration",
        "Operator Settings",
        "Priority Thresholds",
        "System Management"
    ])
    
    with tab1:
        render_serial_settings()
    
    with tab2:
        render_map_settings()
    
    with tab3:
        render_operator_settings()
    
    with tab4:
        render_threshold_settings()
    
    with tab5:
        render_system_management()


def render_serial_settings():
    """Render serial port configuration settings"""
    
    st.subheader("Serial Port Configuration")
    st.markdown("Configure COM port settings for ground station hardware")
    
    # Current connection status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.session_state.serial_connected:
            st.success(f"Currently connected to {st.session_state.serial_port} at {st.session_state.baud_rate} baud")
        elif st.session_state.serial_port is None:
            st.warning("No COM port selected - Please select below")
        else:
            st.info(f"Port configured: {st.session_state.serial_port} (Not connected)")
    
    with col2:
        if st.session_state.serial_connected:
            if st.button("Disconnect", type="secondary", use_container_width=True):
                st.session_state.serial_reader.stop_reading()
                st.session_state.serial_connected = False
                st.success("Disconnected")
                st.rerun()
    
    st.divider()
    
    # Port selection
    st.markdown("#### Port Selection")
    
    # Refresh ports button
    if st.button("🔄 Refresh Port List", help="Scan for available COM ports"):
        st.rerun()
    
    # List available ports
    available_ports = serial.tools.list_ports.comports()
    port_list = [port.device for port in available_ports]
    
    if not port_list:
        st.error("No COM ports detected on this system")
        st.info("Please ensure your ground station hardware is connected via USB")
        st.markdown("**Troubleshooting:**")
        st.markdown("- Check USB cable connection")
        st.markdown("- Install CH340/CP2102 USB drivers if needed")
        st.markdown("- Try a different USB port")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Port selection
        st.markdown("**Select COM Port:**")
        
        # If no port selected, default to first available
        default_index = 0
        if st.session_state.serial_port and st.session_state.serial_port in port_list:
            default_index = port_list.index(st.session_state.serial_port)
        
        selected_port = st.selectbox(
            "COM Port",
            port_list,
            index=default_index,
            help="Select the COM port connected to ground station hardware",
            label_visibility="collapsed"
        )
        
        # Update session state if changed
        if selected_port != st.session_state.serial_port:
            st.session_state.serial_port = selected_port
            st.success(f"Port set to {selected_port}")
            st.info("Click 'Connect to Serial' in sidebar to connect")
    
    with col2:
        # Baud rate selection
        st.markdown("**Select Baud Rate:**")
        
        baud_rates = config.AVAILABLE_BAUD_RATES
        current_baud_index = baud_rates.index(st.session_state.baud_rate) if st.session_state.baud_rate in baud_rates else 4
        
        selected_baud = st.selectbox(
            "Baud Rate",
            baud_rates,
            index=current_baud_index,
            help="Communication speed (must match ground station configuration: 115200)",
            label_visibility="collapsed"
        )
        
        # Update session state if changed
        if selected_baud != st.session_state.baud_rate:
            st.session_state.baud_rate = selected_baud
            st.success(f"Baud rate set to {selected_baud}")
            if st.session_state.serial_connected:
                st.warning("Disconnect and reconnect for baud rate change to take effect")
    
    # Port information
    st.markdown("#### Connected Devices")
    
    if available_ports:
        for port in available_ports:
            is_selected = (port.device == st.session_state.serial_port)
            with st.expander(
                f"{'✓ ' if is_selected else ''}{port.device} - {port.description}",
                expanded=is_selected
            ):
                st.markdown(f"**Device:** {port.device}")
                st.markdown(f"**Description:** {port.description}")
                st.markdown(f"**Hardware ID:** {port.hwid}")
                if hasattr(port, 'manufacturer') and port.manufacturer:
                    st.markdown(f"**Manufacturer:** {port.manufacturer}")
                
                if is_selected:
                    st.success("This port is currently selected")
    
    # Hardware specifications
    st.divider()
    st.markdown("#### Hardware Specifications")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Victim Device:**")
        st.caption(config.VICTIM_DEVICE)
        
        st.markdown("**Drone Device:**")
        st.caption(config.DRONE_DEVICE)
    
    with col2:
        st.markdown("**Ground Station:**")
        st.caption(config.GROUND_STATION_DEVICE)
        
        st.markdown("**Protocol:**")
        st.caption(config.COMMUNICATION_PROTOCOL)
    
    # Quick connection test
    st.divider()
    st.markdown("#### Quick Connection Test")
    
    if st.session_state.serial_port and not st.session_state.serial_connected:
        if st.button("Test Connection", type="primary"):
            try:
                test_serial = serial.Serial(st.session_state.serial_port, st.session_state.baud_rate, timeout=2)
                test_serial.close()
                st.success(f"✓ {st.session_state.serial_port} is accessible and ready!")
                st.info("Go back to Dashboard and click 'Connect to Serial' in sidebar")
            except Exception as e:
                st.error(f"✗ Connection test failed: {str(e)}")
                st.markdown("**Troubleshooting:**")
                st.markdown("- Close Arduino Serial Monitor if open")
                st.markdown("- Check if another program is using the port")
                st.markdown("- Verify correct COM port is selected")


def render_map_settings():
    """Render map configuration settings with auto-update capability"""
    
    st.subheader("Map Configuration")
    st.markdown("Configure default map settings and visualization options")
    
    # 1. THE GEOLOCATION BRIDGE
    # This must be called at the top level. It returns None until the browser provides data.
    loc = get_geolocation()
    
    st.markdown("#### Detect Your Location")
    st.info("Click 'Detect' to fetch your current GPS coordinates. Once coordinates appear in the green box, the input fields will update.")

    # 2. DETECTION LOGIC
    if st.button("📍 Detect My Location", type="primary", use_container_width=True):
        if loc:
            # Extract coordinates from the JS bridge
            new_lat = float(loc['coords']['latitude'])
            new_lon = float(loc['coords']['longitude'])
            
            # Update the source of truth in session state
            st.session_state.rescue_centre_lat = new_lat
            st.session_state.rescue_centre_lon = new_lon
            st.session_state.location_just_detected = True
            
            st.rerun() 
            # Rerun is vital to push the values into the number_input widgets below
        else:
            st.warning("Requesting browser location... Please wait 2 seconds and click 'Detect' again. Ensure you allow location access in your browser popup.")

    if st.session_state.get('location_just_detected', False):
        st.success(f"✓ Location Detected: {st.session_state.rescue_centre_lat:.6f}, {st.session_state.rescue_centre_lon:.6f}")
    
    st.divider()
    
    # 3. MANUAL OVERRIDE / INPUT BOXES
    st.markdown("#### Rescue Station Location")
    st.caption("These coordinates are used as the center point for the rescue mission.")
    
    col1, col2 = st.columns(2)
    
    # Ensure variables exist in session state so number_input has a starting point
    if 'rescue_centre_lat' not in st.session_state:
        st.session_state.rescue_centre_lat = 13.022000
    if 'rescue_centre_lon' not in st.session_state:
        st.session_state.rescue_centre_lon = 77.587000

    with col1:
        # We bind the 'value' to the session_state we just updated
        res_lat = st.number_input(
            "Rescue Station Latitude",
            value=st.session_state.rescue_centre_lat,
            format="%.6f",
            step=0.000001,
            key="lat_box_input"
        )
        st.session_state.rescue_centre_lat = res_lat

    with col2:
        res_lon = st.number_input(
            "Rescue Station Longitude",
            value=st.session_state.rescue_centre_lon,
            format="%.6f",
            step=0.000001,
            key="lon_box_input"
        )
        st.session_state.rescue_centre_lon = res_lon

    # Status indicator
    st.info(f"📡 Current Active Station: `{st.session_state.rescue_centre_lat:.6f}, {st.session_state.rescue_centre_lon:.6f}`")
    
    st.divider()
    
    # 4. API CONFIGURATION
    st.markdown("#### API Configuration")
    if config.validate_api_key():
        st.success("Google Maps API key is configured")
        st.caption(f"API Key: {config.GOOGLE_MAPS_API_KEY[:10]}...{config.GOOGLE_MAPS_API_KEY[-4:]}")
    else:
        st.error("Google Maps API key not configured")
        st.warning("Please add GOOGLE_MAPS_API_KEY to your .env file")
    
    st.divider()

    # 5. MAP DISPLAY PREFERENCES
    st.markdown("#### Map Display Preferences")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        # Simplified: Use the checkbox to update session state directly
        st.session_state.show_rescued = st.checkbox(
            "Show rescued victims by default",
            value=st.session_state.get('show_rescued', True),
            help="Display rescued victims on map by default"
        )
    
    with col_p2:
        st.session_state.show_heatmap = st.checkbox(
            "Show density heatmap by default",
            value=st.session_state.get('show_heatmap', False),
            help="Display victim density heatmap by default"
        )


def render_operator_settings():
    """Render operator configuration settings"""
    
    st.subheader("Operator Settings")
    st.markdown("Configure operator information and preferences")
    
    # Operator information
    st.markdown("#### Operator Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        operator_name = st.text_input(
            "Operator Name",
            value=st.session_state.operator_name,
            help="Name of the current operator managing this ground station"
        )
        
        if operator_name != st.session_state.operator_name:
            st.session_state.operator_name = operator_name
            st.success("Operator name updated")
    
    with col2:
        operator_id = st.text_input(
            "Operator ID (Optional)",
            value=st.session_state.get('operator_id', ''),
            help="Unique identifier for the operator"
        )
        st.session_state.operator_id = operator_id
    
    st.divider()
    
    # Operation metadata
    st.markdown("#### Current Operation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Operation Start",
            st.session_state.operation_start_time.strftime("%H:%M:%S")
        )
    
    with col2:
        duration = datetime.now() - st.session_state.operation_start_time
        hours = int(duration.total_seconds() / 3600)
        minutes = int((duration.total_seconds() % 3600) / 60)
        st.metric("Duration", f"{hours}h {minutes}m")
    
    with col3:
        st.metric("Ground Station", "Active" if st.session_state.serial_connected else "Standby")


def render_threshold_settings():
    """Render priority threshold configuration"""
    
    st.subheader("Priority Threshold Configuration")
    st.markdown("Configure thresholds for priority classification and alerts")
    
    st.success("✓ Changes apply instantly across the website - no restart needed!")
    st.warning("⚠️ Changing these values affects victim priority calculations")
    
    # RSSI thresholds
    st.markdown("#### Signal Strength (RSSI) Thresholds")
    st.caption("Signal strength measured in dBm (decibel-milliwatts)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Strong Signal Threshold**")
        rssi_strong = st.number_input(
            "Strong Signal (greater than)",
            value=st.session_state.rssi_strong_threshold,
            min_value=-120,
            max_value=-30,
            step=1,
            help="Signals stronger than this are considered 'good'"
        )
        
        # Update session state immediately
        if rssi_strong != st.session_state.rssi_strong_threshold:
            st.session_state.rssi_strong_threshold = rssi_strong
            st.success(f"Strong threshold updated to {rssi_strong} dBm")
        
        st.caption(f"Current: {st.session_state.rssi_strong_threshold} dBm")
        st.caption("Typical range: -60 to -75 dBm")
    
    with col2:
        st.markdown("**Weak Signal Threshold**")
        rssi_weak = st.number_input(
            "Weak Signal (less than)",
            value=st.session_state.rssi_weak_threshold,
            min_value=-120,
            max_value=-30,
            step=1,
            help="Signals weaker than this are considered 'critical'"
        )
        
        # Update session state immediately
        if rssi_weak != st.session_state.rssi_weak_threshold:
            st.session_state.rssi_weak_threshold = rssi_weak
            st.success(f"Weak threshold updated to {rssi_weak} dBm")
        
        st.caption(f"Current: {st.session_state.rssi_weak_threshold} dBm")
        st.caption("Typical range: -85 to -95 dBm")
    
    # Validation
    if st.session_state.rssi_weak_threshold >= st.session_state.rssi_strong_threshold:
        st.error("Error: Weak signal threshold must be less than strong signal threshold")
    
    st.divider()
    
    # Time thresholds
    st.markdown("#### Time-Based Thresholds")
    st.caption("Time limits for detecting stale or critical data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Critical Time Threshold**")
        time_critical = st.number_input(
            "High Priority After (minutes)",
            value=st.session_state.time_critical_threshold,
            min_value=1,
            max_value=60,
            step=1,
            help="No update for this long = high priority"
        )
        
        # Update session state immediately
        if time_critical != st.session_state.time_critical_threshold:
            st.session_state.time_critical_threshold = time_critical
            st.success(f"Critical time threshold updated to {time_critical} minutes")
        
        st.caption(f"Current: {st.session_state.time_critical_threshold} minutes")
    
    st.divider()
    
    # Priority summary
    st.markdown("#### Priority Classification Summary")
    
    st.markdown(f"""
    **HIGH Priority** assigned when:
    - Signal strength < {st.session_state.rssi_weak_threshold} dBm (weak/dying battery), OR
    - No update received for > {st.session_state.time_critical_threshold} minutes
    
    **MEDIUM Priority** assigned when:
    - Signal strength between {st.session_state.rssi_weak_threshold} and {st.session_state.rssi_strong_threshold} dBm, AND
    - Updated within last {st.session_state.time_critical_threshold} minutes
    
    **LOW Priority** assigned when:
    - Signal strength > {st.session_state.rssi_strong_threshold} dBm (strong signal), AND
    - Recently updated
    """)


def render_system_management():
    """Render system management and data operations"""
    
    st.subheader("System Management")
    st.markdown("Manage system data, backups, and perform maintenance operations")
    
    # System information
    st.markdown("#### System Information")
    
    data_manager = st.session_state.data_manager
    stats = data_manager.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", stats['total'])
    
    with col2:
        st.metric("Active Records", stats['stranded'] + stats['enroute'])
    
    with col3:
        st.metric("Packets Received", st.session_state.packet_count)
    
    with col4:
        st.metric("Parse Errors", st.session_state.error_count)
    
    st.divider()
    
    # Data management
    st.markdown("#### Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Backup Operations**")
        
        if st.button("Save Backup Now", type="secondary", use_container_width=True):
            success = data_manager.save_to_file()
            if success:
                st.success(f"Backup saved to {config.BACKUP_FILE_PATH}")
            else:
                st.error("Backup failed")
        
        st.caption("Manual backup of all victim data")
        
        # Check last backup time
        if data_manager.last_backup_time:
            st.info(f"Last backup: {data_manager.last_backup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("No backup performed yet")
    
    with col2:
        st.markdown("**Data Restore**")
        
        if st.button("Load from Backup", type="secondary", use_container_width=True):
            if os.path.exists(config.BACKUP_FILE_PATH):
                success = data_manager.load_from_file()
                if success:
                    st.success("Data restored from backup")
                    st.rerun()
                else:
                    st.error("Restore failed")
            else:
                st.warning("No backup file found")
        
        st.caption("Restore victim data from backup file")
    
    st.divider()
    
    # Dangerous operations
    st.markdown("#### System Reset")
    st.error("⚠️ DANGER ZONE - These operations are irreversible")
    
    with st.expander("Reset Operations (Use with Caution)"):
        st.warning("These operations will permanently delete data")
        
        # Reset all data
        st.markdown("**Reset All Victim Data**")
        st.caption("Permanently deletes all victim records and statistics")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            confirm_reset = st.checkbox(
                "I understand this will delete all data",
                key="confirm_reset_data"
            )
        
        with col2:
            if st.button(
                "Reset All Data",
                type="primary",
                disabled=not confirm_reset,
                use_container_width=True
            ):
                data_manager.reset_all_data()
                st.session_state.packet_count = 0
                st.session_state.error_count = 0
                st.session_state.operation_start_time = datetime.now()
                st.success("All data has been reset")
                st.rerun()
        
        st.divider()
        
        # Reset statistics only
        st.markdown("**Reset Statistics Only**")
        st.caption("Reset packet counters and error counts (keeps victim data)")
        
        if st.button("Reset Statistics", type="secondary", use_container_width=True):
            st.session_state.packet_count = 0
            st.session_state.error_count = 0
            st.success("Statistics reset")
            st.rerun()
    
    st.divider()
    
    # Application information
    st.markdown("#### Application Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Build:** Production")
        st.markdown("**Framework:** Streamlit")
    
    with col2:
        st.markdown("**Developer:** FalconResQ Team")
        st.markdown("**License:** Proprietary")
        st.markdown("**Support:** Technical Support Available")
    
    # File paths
    st.markdown("#### File Locations")
    
    with st.expander("View System Paths"):
        st.code(f"Backup File: {config.BACKUP_FILE_PATH}", language="text")
        st.code(f"Rescue Log: {config.RESCUE_LOG_PATH}", language="text")
        st.code(f"Configuration: config.py", language="text")