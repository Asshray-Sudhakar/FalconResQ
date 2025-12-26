"""
Dashboard Page - Active Rescue Operations
Real-time monitoring and victim management interface
"""

import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
import time

from modules import MapManager, Analytics
from utils.helpers import calculate_priority, format_time_ago, get_signal_color
import config

# ===== REAL-TIME UPDATE CHECK =====
if st.session_state.get('force_rerun', False):
    st.session_state.force_rerun = False
    st.rerun()

def render_metrics_bar(data_manager):
    """
    Render top metrics dashboard with live data from the DataManager.
    Shows Total, Stranded, En-Route, Rescued, and Success Rate.
    """
    
    # 1. Fetch the latest stats from your data manager
    stats = data_manager.get_statistics()
    
    # 2. Create 5 columns for a professional monitoring look
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Detected",
            value=stats['total'],
            help="Total unique victim IDs detected by the ground station"
        )
    
    with col2:
        # Show a negative delta if people are still stranded (priority to clear this)
        stranded_val = stats['stranded']
        st.metric(
            label="Stranded",
            value=stranded_val,
            delta=-stranded_val,
            delta_color="normal", 
            help="Victims currently awaiting rescue"
        )
    
    with col3:
        st.metric(
            label="En-Route",
            value=stats['enroute'],
            help="Rescue teams dispatched"
        )
    
    with col4:
        # Show a positive green delta for successful rescues
        rescued_count = stats['rescued']
        st.metric(
            label="Rescued",
            value=rescued_count,
            delta=f"+{rescued_count}" if rescued_count > 0 else None,
            delta_color="normal",
            help="Victims successfully reached and moved to safety"
        )
    
    with col5:
        # Calculate success percentage
        rescue_pct = stats['rescued_pct']
        st.metric(
            label="Success Rate",
            value=f"{rescue_pct:.1f}%",
            help="Overall operation efficiency (Rescued / Total)"
        )

    # Optional: Add a progress bar for visual impact
    if stats['total'] > 0:
        progress_val = stats['rescued'] / stats['total']
        st.progress(progress_val, text=f"Mission Progress: {int(progress_val*100)}%")


def render_victim_table_with_rescue(data_manager):
    """Render victim data preview with rescue checkbox in single-line format"""
    
    st.subheader("Live Data Preview")
    st.markdown("Live preview of current victim data")
    
    victims = data_manager.get_all_victims()
    
    if victims:
        # Convert to DataFrame
        df = pd.DataFrame(list(victims.values()))
        
        # Select and reorder columns for display
        display_columns = ['ID', 'LAT', 'LON', 'RSSI', 'LAST_UPDATE', 'UPDATE_COUNT', 'STATUS']
        available_columns = [col for col in display_columns if col in df.columns]
        df_display = df[available_columns].copy()
        
        # Display with filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + config.ALL_STATUSES,
                key="dashboard_status_filter"
            )
        
        with col2:
            sort_column = st.selectbox(
                "Sort by",
                available_columns,
                index=0,
                key="dashboard_sort_column"
            )
        
        with col3:
            sort_order = st.selectbox(
                "Order",
                ["Ascending", "Descending"],
                key="dashboard_sort_order"
            )
        
        # Apply filters
        if status_filter != "All":
            df_display = df_display[df_display['STATUS'] == status_filter]
        
        # Apply sorting
        ascending = (sort_order == "Ascending")
        df_display = df_display.sort_values(by=sort_column, ascending=ascending)
        
        # Display each victim in single-line format
        for idx, row in df_display.iterrows():
            victim_id = int(row['ID'])
            current_victim = victims[victim_id]
            is_currently_rescued = current_victim['STATUS'] == config.STATUS_RESCUED
            
            # Status text
            status_text = "Rescued" if is_currently_rescued else "Stranded"
            
            # Create single line with checkbox and info
            col_checkbox, col_info = st.columns([0.05, 0.95])
            
            with col_checkbox:
                # Editable checkbox
                new_state = st.checkbox(
                    label="",
                    value=is_currently_rescued,
                    key=f"rescue_cb_{victim_id}_{idx}"
                )
                
                # Handle state change
                if new_state and not is_currently_rescued:
                    # Mark as rescued
                    data_manager.mark_rescued(victim_id, "Dashboard Action")
                    st.rerun()
                elif not new_state and is_currently_rescued:
                    # Undo rescue
                    current_victim['STATUS'] = config.STATUS_STRANDED
                    current_victim['RESCUED_TIME'] = None
                    current_victim['RESCUED_BY'] = None
                    data_manager._auto_save()
                    st.rerun()
            
            with col_info:
                # Format with extra spacing for clarity
                status_color = config.STATUS_COLORS.get(current_victim['STATUS'], '#333')
                info_text = (
                    f"**ID: {int(row['ID'])}**&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"Lat: {row['LAT']:.6f}&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"Lon: {row['LON']:.6f}&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"RSSI: {row['RSSI']} dBm&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"Date & Time: {row['LAST_UPDATE']}&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"Data Packs: {int(row['UPDATE_COUNT'])}&nbsp;&nbsp;&nbsp;&nbsp;"
                    f"<span style='color: {status_color}; font-weight: bold;'>{status_text}</span>"
                )
                st.markdown(info_text, unsafe_allow_html=True)
        
        st.caption(f"Showing {len(df_display)} of {len(victims)} record(s)")
    
    else:
        st.info("No victim data available. Waiting for data reception...")


def render_dashboard():
    """Render the main dashboard page"""
    
    # Get instances
    data_manager = st.session_state.data_manager
    map_manager = MapManager()
    analytics = Analytics(data_manager)
    
    st.title("FalconResQ Dashboard")
    st.markdown("### Active Rescue Operations")
    
    # Top metrics bar
    render_metrics_bar(data_manager)
    st.divider()
    
    # Main content
    render_main_content(data_manager, map_manager, analytics)


def render_main_content(data_manager, map_manager, analytics):
    """Render main dashboard content with synchronized Map"""
    
    # 1. Live Data Table (Top)
    render_victim_table_with_rescue(data_manager)
    
    st.divider()
    
    # 2. Map Section (Bottom)
    render_map_section(data_manager, map_manager)


def render_map_section(data_manager, map_manager):
    """Render the map with Rescue Station synced to Session State"""
    
    st.subheader("Live Victim Map")
    
    # Map controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    
    with ctrl_col1:
        show_rescued = st.checkbox("Show Rescued", value=st.session_state.get('show_rescued', True), key="map_show_rescued_v2")
        st.session_state.show_rescued = show_rescued
    
    with ctrl_col2:
        show_priority = st.checkbox("Priority Only", value=st.session_state.get('show_priority_only', False), key="map_show_priority_v2")
        st.session_state.show_priority_only = show_priority
    
    with ctrl_col3:
        show_heatmap = st.checkbox("Density Heatmap", value=st.session_state.get('show_heatmap', False), key="map_show_heatmap_v2")
        st.session_state.show_heatmap = show_heatmap
    
    # SYNC RESCUE STATION LOCATION
    # We pull the lat/lon that was detected in the Settings page
    rescue_centre = [
        float(st.session_state.get('rescue_centre_lat', 13.022)),
        float(st.session_state.get('rescue_centre_lon', 77.587))
    ]

    victims = data_manager.get_all_victims()
    
    if victims:
        # Generate the map using MapManager
        victim_map = map_manager.create_victim_map(
            victims=victims,
            center=rescue_centre,
            show_rescued=show_rescued,
            show_priority_only=show_priority,
            show_heatmap=show_heatmap,
            rssi_strong_threshold=st.session_state.get('rssi_strong_threshold', config.RSSI_STRONG_THRESHOLD),
            rssi_weak_threshold=st.session_state.get('rssi_weak_threshold', config.RSSI_WEAK_THRESHOLD),
            time_critical_threshold=st.session_state.get('time_critical_threshold', config.TIME_CRITICAL_THRESHOLD)
        )
        
        # Display map - Note: returned_objects=[] prevents unnecessary refreshes
        st_folium(victim_map, width=None, height=550, returned_objects=[])
        st.caption(f"Rescue Station synced to: {rescue_centre[0]:.6f}, {rescue_centre[1]:.6f}")
    else:
        st.info("Waiting for victim signals... Map will appear when data is received.")


# Run the dashboard
if __name__ == "__main__" or True:  # Always run in Streamlit
    render_dashboard()