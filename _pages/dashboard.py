"""
Dashboard Page - Active Rescue Operations
Real-time monitoring and victim management interface
"""

import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime

from modules import MapManager, Analytics
from utils.helpers import calculate_priority, format_time_ago, get_signal_color
import config

# ===== REAL-TIME UPDATE CHECK - MUST BE AT TOP =====
# Check if we need to rerun due to new packet
if st.session_state.get('force_rerun', False):
    st.session_state.force_rerun = False
    st.rerun()


def render_dashboard():
    """Render the main dashboard page"""
    
    # Get instances from session state
    data_manager = st.session_state.data_manager
    map_manager = MapManager()
    analytics = Analytics(data_manager)
    
    # Page header
    st.title("FalconResQ Dashboard")
    st.title("Active Rescue Operations")
    st.markdown("Real-time victim tracking and rescue coordination")
    
    # Top metrics bar (always show)
    render_metrics_bar(data_manager)
    
    st.divider()
    
    # Main content: Map and Management Panel
    render_main_content(data_manager, map_manager, analytics)


def render_metrics_bar(data_manager):
    """Render top metrics dashboard"""
    
    stats = data_manager.get_statistics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Detected",
            value=stats['total'],
            help="Total victims detected since operation start"
        )
    
    with col2:
        delta = -stats['stranded'] if stats['stranded'] > 0 else None
        st.metric(
            label="Stranded",
            value=stats['stranded'],
            delta=delta,
            delta_color="normal",
            help="Victims awaiting rescue"
        )
    
    with col3:
        st.metric(
            label="En-Route",
            value=stats['enroute'],
            help="Rescue teams dispatched"
        )
    
    with col4:
        delta = f"+{stats['rescued']}" if stats['rescued'] > 0 else None
        st.metric(
            label="Rescued",
            value=stats['rescued'],
            delta=delta,
            delta_color="normal",
            help="Successfully rescued victims"
        )
    
    with col5:
        rescue_pct = stats['rescued_pct']
        st.metric(
            label="Success Rate",
            value=f"{rescue_pct:.1f}%",
            help="Percentage of victims rescued"
        )


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


def render_main_content(data_manager, map_manager, analytics):
    """Render main dashboard content"""
    
    # Create two columns: Map (larger) and Management Panel (smaller)
    # For now, show map full width to debug data reception
    st.markdown("")  # Spacing
    
    # Render data preview table with rescue checkbox
    render_victim_table_with_rescue(data_manager)
    
    st.divider()
    
    render_map_section(data_manager, map_manager)
    
    # TODO: Re-enable management panel after fixing key conflicts
    # with panel_col:
    #     render_management_panel(data_manager, analytics)


def render_map_section(data_manager, map_manager):
    """Render the map section"""
    
    st.subheader("Live Victim Map")
    
    # Map controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    
    with ctrl_col1:
        show_rescued = st.checkbox(
            "Show Rescued",
            value=st.session_state.show_rescued,
            help="Display rescued victims on map",
            key="map_show_rescued_v2"
        )
        st.session_state.show_rescued = show_rescued
    
    with ctrl_col2:
        show_priority = st.checkbox(
            "Priority Only",
            value=st.session_state.show_priority_only,
            help="Show only high-priority victims",
            key="map_show_priority_v2"
        )
        st.session_state.show_priority_only = show_priority
    
    with ctrl_col3:
        show_heatmap = st.checkbox(
            "Density Heatmap",
            value=st.session_state.show_heatmap,
            help="Show victim density overlay",
            key="map_show_heatmap_v2"
        )
        st.session_state.show_heatmap = show_heatmap
    
    # Get victims
    victims = data_manager.get_all_victims()
    
    if victims:
        # Create map with rescue station at user's detected location
        rescue_centre = [
            float(st.session_state.get('rescue_centre_lat', 13.022)),
            float(st.session_state.get('rescue_centre_lon', 77.587))
        ]

        victim_map = map_manager.create_victim_map(
            victims=victims,
            center=rescue_centre,
            show_rescued=show_rescued,
            show_priority_only=show_priority,
            show_heatmap=show_heatmap,
            rssi_strong_threshold=st.session_state.rssi_strong_threshold,
            rssi_weak_threshold=st.session_state.rssi_weak_threshold,
            time_critical_threshold=st.session_state.time_critical_threshold
        )
        
        # Display map
        st_folium(victim_map, width=None, height=550, returned_objects=[])
        
        # Map statistics
        visible_count = len(victims)
        if show_priority:
            priority_victims = data_manager.get_priority_victims(
                rssi_strong_threshold=st.session_state.rssi_strong_threshold,
                rssi_weak_threshold=st.session_state.rssi_weak_threshold,
                time_critical_threshold=st.session_state.time_critical_threshold
            )
            visible_count = len(priority_victims)
        
        st.caption(f"Displaying {visible_count} victim(s) on map")
        
    else:
        # Empty state
        st.info("Waiting for victim signals... Map will appear when data is received.")
        st.markdown("**Status:** Monitoring COM port for incoming data packets")


def render_management_panel(data_manager, analytics):
    """Render victim management panel"""
    
    st.subheader("Victim Management")
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["All Victims", "Priority Cases", "Recently Updated"])
    
    with tab1:
        render_victim_list(data_manager, filter_type="all")
    
    with tab2:
        render_victim_list(data_manager, filter_type="priority")
    
    with tab3:
        render_victim_list(data_manager, filter_type="recent")


def render_victim_list(data_manager, filter_type="all"):
    """Render list of victims with actions"""
    
    victims = data_manager.get_all_victims()
    
    if not victims:
        st.info("No victims to display")
        return
    
    # Filter victims based on type
    if filter_type == "priority":
        victims = data_manager.get_priority_victims(
            rssi_strong_threshold=st.session_state.rssi_strong_threshold,
            rssi_weak_threshold=st.session_state.rssi_weak_threshold,
            time_critical_threshold=st.session_state.time_critical_threshold
        )
        if not victims:
            st.info("No high-priority victims currently")
            return
    
    elif filter_type == "recent":
        # Sort by last update (most recent first)
        victims = dict(sorted(
            victims.items(),
            key=lambda x: x[1].get('LAST_UPDATE', ''),
            reverse=True
        ))
        # Take only top 10 most recent
        victims = dict(list(victims.items())[:10])
    
    # Status filter for "all" tab
    if filter_type == "all":
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Stranded", "En-Route", "Rescued"],
            label_visibility="collapsed"
        )
        
        if status_filter != "All":
            status_map = {
                "Stranded": config.STATUS_STRANDED,
                "En-Route": config.STATUS_EN_ROUTE,
                "Rescued": config.STATUS_RESCUED
            }
            victims = {
                k: v for k, v in victims.items()
                if v['STATUS'] == status_map[status_filter]
            }
    
    # Display victim cards
    st.caption(f"Showing {len(victims)} victim(s)")
    
    # Scrollable container
    container = st.container(height=450)
    
    with container:
        for vid, victim in victims.items():
            render_victim_card(vid, victim, data_manager)


def render_victim_card(victim_id, victim, data_manager):
    """Render individual victim card with actions"""
    
    priority, priority_label = calculate_priority(victim)
    signal_label, signal_color = get_signal_color(victim['RSSI'])
    status = victim['STATUS']
    
    # Status color
    status_color = config.STATUS_COLORS[status]
    
    # Card container
    with st.expander(
        f"ID: {victim_id} | {status}",
        expanded=False
    ):
        # Header with priority badge
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Status:** `{status}`")
        
        with col2:
            if priority == "HIGH":
                st.markdown(
                    f'<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">HIGH</span>',
                    unsafe_allow_html=True
                )
            elif priority == "MEDIUM":
                st.markdown(
                    f'<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">MED</span>',
                    unsafe_allow_html=True
                )
        
        # Victim information
        st.markdown(f"**Location:** {victim['LAT']:.6f}, {victim['LON']:.6f}")
        
        st.markdown(
            f"**Signal:** <span style='color: {signal_color}; font-weight: bold;'>{victim['RSSI']} dBm</span> ({signal_label})",
            unsafe_allow_html=True
        )
        
        st.markdown(f"**Last Update:** {format_time_ago(victim['LAST_UPDATE'])}")
        st.markdown(f"**Packets Received:** {victim.get('UPDATE_COUNT', 0)}")
        
        # Action buttons based on status
        st.markdown("---")
        
        if status == config.STATUS_STRANDED:
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button(
                    "Dispatch Team",
                    key=f"enroute_{victim_id}",
                    use_container_width=True
                ):
                    data_manager.mark_enroute(victim_id)
                    st.success(f"Team dispatched for ID {victim_id}")
                    time.sleep(0.5)
                    st.rerun()
            
            with col_b:
                if st.button(
                    "Mark Rescued",
                    key=f"rescued_{victim_id}",
                    use_container_width=True,
                    type="primary"
                ):
                    # Use session state operator name
                    operator = st.session_state.operator_name
                    data_manager.mark_rescued(victim_id, operator, "")
                    st.success(f"Victim {victim_id} marked as rescued!")
                    time.sleep(0.5)
                    st.rerun()
        
        elif status == config.STATUS_EN_ROUTE:
            if st.button(
                "Confirm Rescue",
                key=f"rescued_{victim_id}",
                use_container_width=True,
                type="primary"
            ):
                operator = st.session_state.operator_name
                data_manager.mark_rescued(victim_id, operator, "")
                st.success(f"Victim {victim_id} rescued!")
                time.sleep(0.5)
                st.rerun()
        
        elif status == config.STATUS_RESCUED:
            rescued_by = victim.get('RESCUED_BY', 'Unknown')
            rescued_time = format_time_ago(victim.get('RESCUED_TIME', ''))
            
            st.success(f"Rescued by {rescued_by}")
            st.caption(f"Rescue time: {rescued_time}")
            
            if victim.get('NOTES'):
                st.info(f"Notes: {victim['NOTES']}")


def render_quick_stats(analytics):
    """Render quick statistics panel"""
    
    st.markdown("### Quick Statistics")
    
    # Rescue rate
    rescue_rate = analytics.calculate_rescue_rate()
    
    if rescue_rate['total_rescued'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Rescue Rate",
                f"{rescue_rate['rescues_per_hour']:.1f}/hr"
            )
        
        with col2:
            st.metric(
                "Avg Time",
                f"{rescue_rate['average_rescue_time_minutes']:.1f} min"
            )
    
    # Signal distribution
    signal_dist = analytics.analyze_signal_trends()
    
    st.markdown("**Signal Distribution**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Strong", signal_dist['strong_signals'])
    
    with col2:
        st.metric("Medium", signal_dist['medium_signals'])
    
    with col3:
        st.metric("Weak", signal_dist['weak_signals'])


# Run the dashboard
if __name__ == "__main__" or True:  # Always run in Streamlit
    render_dashboard()