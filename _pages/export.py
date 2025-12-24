"""
Export Page - Data Export and Reporting
Professional data export interface with multiple formats and filters
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import io

from modules import Analytics
import config


def render_export():
    """Render the export page"""
    
    # Get instances from session state
    data_manager = st.session_state.data_manager
    analytics = Analytics(data_manager)
    
    # Page header
    st.title("Data Export & Reporting")
    st.markdown("Export victim data and generate operation reports")
    
    # Check if data exists
    victims = data_manager.get_all_victims()
    
    if not victims:
        st.warning("No data available to export")
        st.info("Data will be available once victims are detected by the system")
        return
    
    # Overview statistics
    render_export_overview(data_manager)
    
    st.divider()
    
    # Export options
    render_export_options(data_manager, analytics)
    
    st.divider()
    
    # Data preview
    render_data_preview(data_manager)


def render_export_overview(data_manager):
    """Render export overview with statistics"""
    
    stats = data_manager.get_statistics()
    
    st.subheader("Export Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Records", stats['total'])
    
    with col2:
        st.metric("Stranded", stats['stranded'])
    
    with col3:
        st.metric("En-Route", stats['enroute'])
    
    with col4:
        st.metric("Rescued", stats['rescued'])
    
    with col5:
        operation_time = datetime.now() - st.session_state.operation_start_time
        hours = int(operation_time.total_seconds() / 3600)
        st.metric("Operation Time", f"{hours}h")


def render_export_options(data_manager, analytics):
    """Render export options and buttons"""
    
    st.subheader("Export Options")
    
    # Create tabs for different export types
    tab1, tab2, tab3, tab4 = st.tabs([
        "CSV Exports",
        "JSON Exports",
        "Operation Report",
        "Rescue Log"
    ])
    
    with tab1:
        render_csv_exports(data_manager)
    
    with tab2:
        render_json_exports(data_manager)
    
    with tab3:
        render_operation_report(data_manager, analytics)
    
    with tab4:
        render_rescue_log(data_manager)


def render_csv_exports(data_manager):
    """Render CSV export options"""
    
    st.markdown("### CSV Data Exports")
    st.markdown("Export victim data in CSV format for analysis in Excel, databases, or other tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Filtered Exports")
        
        # All victims
        st.markdown("**All Victims**")
        st.caption("Complete dataset with all victim records")
        
        all_victims = data_manager.get_all_victims()
        if all_victims:
            csv_all = generate_csv(list(all_victims.values()))
            st.download_button(
                label="Download All Data (CSV)",
                data=csv_all,
                file_name=f"all_victims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No data available")
        
        st.markdown("---")
        
        # Stranded only
        st.markdown("**Stranded Victims**")
        st.caption("Victims currently awaiting rescue")
        
        stranded = data_manager.get_victims_by_status(config.STATUS_STRANDED)
        if stranded:
            csv_stranded = generate_csv(list(stranded.values()))
            st.download_button(
                label="Download Stranded (CSV)",
                data=csv_stranded,
                file_name=f"stranded_victims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption(f"{len(stranded)} record(s)")
        else:
            st.info("No stranded victims")
    
    with col2:
        st.markdown("#### Status-Based Exports")
        
        # En-route
        st.markdown("**En-Route Victims**")
        st.caption("Rescue teams dispatched")
        
        enroute = data_manager.get_victims_by_status(config.STATUS_EN_ROUTE)
        if enroute:
            csv_enroute = generate_csv(list(enroute.values()))
            st.download_button(
                label="Download En-Route (CSV)",
                data=csv_enroute,
                file_name=f"enroute_victims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption(f"{len(enroute)} record(s)")
        else:
            st.info("No en-route victims")
        
        st.markdown("---")
        
        # Rescued
        st.markdown("**Rescued Victims**")
        st.caption("Successfully rescued individuals")
        
        rescued = data_manager.get_victims_by_status(config.STATUS_RESCUED)
        if rescued:
            csv_rescued = generate_csv(list(rescued.values()))
            st.download_button(
                label="Download Rescued (CSV)",
                data=csv_rescued,
                file_name=f"rescued_victims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption(f"{len(rescued)} record(s)")
        else:
            st.info("No rescued victims")
    
    # Priority exports
    st.markdown("---")
    st.markdown("#### Priority-Based Exports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**High Priority Cases**")
        st.caption("Victims requiring immediate attention")
        
        priority_victims = data_manager.get_priority_victims(
            rssi_strong_threshold=st.session_state.rssi_strong_threshold,
            rssi_weak_threshold=st.session_state.rssi_weak_threshold,
            time_critical_threshold=st.session_state.time_critical_threshold
        )
        if priority_victims:
            csv_priority = generate_csv(list(priority_victims.values()))
            st.download_button(
                label="Download High Priority (CSV)",
                data=csv_priority,
                file_name=f"priority_victims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption(f"{len(priority_victims)} record(s)")
        else:
            st.success("No high priority cases")


def render_json_exports(data_manager):
    """Render JSON export options"""
    
    st.markdown("### JSON Data Exports")
    st.markdown("Export data in JSON format for API integration or backup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Complete Dataset (JSON)**")
        st.caption("Full victim data with all metadata")
        
        all_data = data_manager.get_all_victims()
        if all_data:
            json_data = json.dumps(all_data, indent=2, default=str)
            st.download_button(
                label="Download All Data (JSON)",
                data=json_data,
                file_name=f"victims_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("No data available")
    
    with col2:
        st.markdown("**Backup Package**")
        st.caption("Complete system backup including configuration")
        
        backup_data = {
            'export_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'operation_start': st.session_state.operation_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'operator': st.session_state.operator_name,
            'victims': data_manager.get_all_victims(),
            'statistics': data_manager.get_statistics()
        }
        
        json_backup = json.dumps(backup_data, indent=2, default=str)
        st.download_button(
            label="Download Backup Package (JSON)",
            data=json_backup,
            file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def render_operation_report(data_manager, analytics):
    """Render comprehensive operation report"""
    
    st.markdown("### Operation Report")
    st.markdown("Comprehensive summary report with analytics and insights")
    
    # Generate report
    report_content = generate_operation_report(data_manager, analytics)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display report preview
        st.markdown("#### Report Preview")
        with st.expander("View Report Content", expanded=False):
            st.text(report_content)
    
    with col2:
        st.markdown("#### Download Options")
        
        # Text report
        st.download_button(
            label="Download Report (TXT)",
            data=report_content,
            file_name=f"operation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Summary statistics
        stats = data_manager.get_statistics()
        st.metric("Report Sections", "6")
        st.metric("Total Records", stats['total'])
        st.caption(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def render_rescue_log(data_manager):
    """Render rescue log export"""
    
    st.markdown("### Rescue Event Log")
    st.markdown("Historical log of all rescue operations")
    
    rescued_victims = data_manager.get_victims_by_status(config.STATUS_RESCUED)
    
    if rescued_victims:
        # Create rescue log DataFrame
        rescue_log = []
        
        for vid, victim in rescued_victims.items():
            rescue_log.append({
                'Victim_ID': vid,
                'Rescued_Time': victim.get('RESCUED_TIME', ''),
                'Rescued_By': victim.get('RESCUED_BY', ''),
                'Location_Lat': victim['LAT'],
                'Location_Lon': victim['LON'],
                'First_Detected': victim['FIRST_DETECTED'],
                'Total_Updates': victim.get('UPDATE_COUNT', 0),
                'Final_Signal_RSSI': victim['RSSI'],
                'Notes': victim.get('NOTES', '')
            })
        
        df = pd.DataFrame(rescue_log)
        
        # Display preview
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download button
        csv_log = df.to_csv(index=False)
        st.download_button(
            label="Download Rescue Log (CSV)",
            data=csv_log,
            file_name=f"rescue_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.success(f"Log contains {len(rescue_log)} rescue event(s)")
    
    else:
        st.info("No rescue events recorded yet")


def render_data_preview(data_manager):
    """Render data preview table"""
    
    st.subheader("Data Preview")
    st.markdown("Live preview of current victim data")
    
    victims = data_manager.get_all_victims()
    
    if victims:
        # Convert to DataFrame
        df = pd.DataFrame(list(victims.values()))
        
        # Select and reorder columns for display
        display_columns = ['ID', 'STATUS', 'LAT', 'LON', 'RSSI', 'LAST_UPDATE', 'UPDATE_COUNT']
        available_columns = [col for col in display_columns if col in df.columns]
        df_display = df[available_columns]
        
        # Format columns
        if 'LAT' in df_display.columns:
            df_display['LAT'] = df_display['LAT'].apply(lambda x: f"{x:.6f}")
        if 'LON' in df_display.columns:
            df_display['LON'] = df_display['LON'].apply(lambda x: f"{x:.6f}")
        
        # Display with filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + config.ALL_STATUSES
            )
        
        with col2:
            sort_column = st.selectbox(
                "Sort by",
                display_columns
            )
        
        with col3:
            sort_order = st.selectbox(
                "Order",
                ["Ascending", "Descending"]
            )
        
        # Apply filters
        if status_filter != "All":
            df_display = df_display[df_display['STATUS'] == status_filter]
        
        # Apply sorting
        ascending = (sort_order == "Ascending")
        df_display = df_display.sort_values(by=sort_column, ascending=ascending)
        
        # Display table
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "STATUS": st.column_config.TextColumn("Status", width="medium"),
                "LAT": st.column_config.TextColumn("Latitude", width="medium"),
                "LON": st.column_config.TextColumn("Longitude", width="medium"),
                "RSSI": st.column_config.NumberColumn("Signal (dBm)", width="small"),
                "LAST_UPDATE": st.column_config.TextColumn("Last Update", width="large"),
                "UPDATE_COUNT": st.column_config.NumberColumn("Updates", width="small")
            }
        )
        
        st.caption(f"Showing {len(df_display)} of {len(df)} record(s)")
    
    else:
        st.info("No data to preview")


def generate_csv(victims_list):
    """Generate CSV content from victims list"""
    
    df = pd.DataFrame(victims_list)
    
    # Select columns based on config
    columns = [col for col in config.EXPORT_COLUMNS if col in df.columns]
    df = df[columns]
    
    return df.to_csv(index=False)


def generate_operation_report(data_manager, analytics):
    """Generate comprehensive operation report"""
    
    stats = data_manager.get_statistics()
    rescue_metrics = analytics.calculate_rescue_rate()
    efficiency = analytics.calculate_rescue_efficiency()
    signal_analysis = analytics.analyze_signal_trends()
    time_patterns = analytics.analyze_time_patterns()
    coverage = analytics.get_coverage_area(
        rescue_centre_lat=st.session_state.get('rescue_centre_lat', 13.022),
        rescue_centre_lon=st.session_state.get('rescue_centre_lon', 77.587)
    )
    
    report = f"""
================================================================================
                    DISASTER MANAGEMENT OPERATION REPORT
================================================================================

Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Operator: {st.session_state.operator_name}
Operation Start: {st.session_state.operation_start_time.strftime("%Y-%m-%d %H:%M:%S")}
Operation Duration: {time_patterns['operation_duration_hours']:.2f} hours

================================================================================
                         EXECUTIVE SUMMARY
================================================================================

Total Victims Detected:     {stats['total']}
Currently Stranded:         {stats['stranded']} ({stats['stranded_pct']:.1f}%)
Rescue Teams En-Route:      {stats['enroute']} ({stats['enroute_pct']:.1f}%)
Successfully Rescued:       {stats['rescued']} ({stats['rescued_pct']:.1f}%)

Operation Efficiency:       {efficiency['efficiency_percentage']:.1f}% ({efficiency['grade']})

================================================================================
                       RESCUE PERFORMANCE METRICS
================================================================================

Rescue Rate:                {rescue_metrics['rescues_per_hour']:.2f} victims/hour
Average Rescue Time:        {rescue_metrics['average_rescue_time_minutes']:.1f} minutes
Fastest Rescue:             {rescue_metrics['fastest_rescue_minutes']:.1f} minutes
Slowest Rescue:             {rescue_metrics['slowest_rescue_minutes']:.1f} minutes

================================================================================
                      GEOGRAPHIC COVERAGE ANALYSIS
================================================================================

Coverage Distance:          {coverage.get('distance_km', 0):.2f} km (Rescue Station to First Beacon)
Coverage Area:              {coverage['area_km2']:.2f} km²
Latitude Range:             {coverage['min_lat']:.6f} to {coverage['max_lat']:.6f}
Longitude Range:            {coverage['min_lon']:.6f} to {coverage['max_lon']:.6f}

================================================================================
                       SIGNAL STRENGTH ANALYSIS
================================================================================

Average Signal Strength:    {signal_analysis['average_rssi']:.1f} dBm
Median Signal Strength:     {signal_analysis['median_rssi']:.1f} dBm

Signal Distribution:
  - Strong Signals:         {signal_analysis['strong_signals']} victims
  - Medium Signals:         {signal_analysis['medium_signals']} victims
  - Weak Signals:           {signal_analysis['weak_signals']} victims

Deteriorating Signals:      {len(signal_analysis['deteriorating_signals'])} victims

================================================================================
                         TIME-BASED ANALYSIS
================================================================================

Detection Rate:             {time_patterns['detections_per_hour']:.2f} victims/hour
Stale Data Instances:       {time_patterns['stale_data_count']} victims
(No update for >{time_patterns['no_update_threshold_minutes']} minutes)

================================================================================
                              RECOMMENDATIONS
================================================================================

"""
    
    # Add recommendations based on data
    if stats['stranded'] > stats['rescued']:
        report += "1. PRIORITY: Increase rescue team deployment - more victims stranded than rescued\n"
    
    if signal_analysis['weak_signals'] > 5:
        report += f"2. ALERT: {signal_analysis['weak_signals']} victims with weak signals - batteries may be dying\n"
    
    if time_patterns['stale_data_count'] > 0:
        report += f"3. WARNING: {time_patterns['stale_data_count']} victims with stale data - verify status\n"
    
    if efficiency['efficiency_percentage'] < 60:
        report += "4. ATTENTION: Operation efficiency below 60% - review rescue procedures\n"
    
    if len(signal_analysis['deteriorating_signals']) > 0:
        report += f"5. URGENT: {len(signal_analysis['deteriorating_signals'])} victims with deteriorating signals\n"
    
    report += "\n================================================================================\n"
    report += "                           END OF REPORT\n"
    report += "================================================================================\n"
    
    return report