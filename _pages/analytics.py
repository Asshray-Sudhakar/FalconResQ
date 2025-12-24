"""
Analytics Page - Progress Dashboard and Insights
Comprehensive analytics and operation performance metrics
"""

import streamlit as st
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime

from modules import MapManager, Analytics
from utils.helpers import format_time_ago
import config


def render_analytics():
    """Render the analytics page"""
    
    # Get instances from session state
    data_manager = st.session_state.data_manager
    map_manager = MapManager()
    analytics = Analytics(data_manager)
    
    # Page header
    st.title("Analytics & Progress Dashboard")
    st.markdown("Comprehensive operation insights and performance metrics")
    
    # Top-level metrics (always show)
    render_summary_metrics(data_manager, analytics)
    
    st.divider()
    
    # Main content sections
    render_visual_analytics(data_manager, map_manager, analytics)
    
    st.divider()
    
    render_detailed_analytics(analytics)
    
    # Real-time update: Check if new packet received
    if st.session_state.get('force_rerun', False):
        st.session_state.force_rerun = False
        st.rerun()


def render_summary_metrics(data_manager, analytics):
    """Render summary metrics bar"""
    
    stats = data_manager.get_statistics()
    rescue_metrics = analytics.calculate_rescue_rate()
    efficiency = analytics.calculate_rescue_efficiency()
    time_patterns = analytics.analyze_time_patterns()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            label="Total Victims",
            value=stats['total'],
            help="Total victims detected"
        )
    
    with col2:
        st.metric(
            label="Stranded",
            value=stats['stranded'],
            delta=-stats['stranded_pct'] if stats['stranded'] > 0 else None,
            delta_color="normal",
            help="Victims awaiting rescue"
        )
    
    with col3:
        st.metric(
            label="Rescued",
            value=stats['rescued'],
            delta=f"{stats['rescued_pct']:.0f}%",
            delta_color="normal",
            help="Successfully rescued"
        )
    
    with col4:
        st.metric(
            label="Rescue Rate",
            value=f"{rescue_metrics['rescues_per_hour']:.1f}/hr",
            help="Victims rescued per hour"
        )
    
    with col5:
        st.metric(
            label="Efficiency",
            value=f"{efficiency['efficiency_percentage']:.1f}%",
            help=f"Grade: {efficiency['grade']}"
        )
    
    with col6:
        st.metric(
            label="Operation Time",
            value=f"{time_patterns['operation_duration_hours']:.1f}h",
            help="Time since first detection"
        )


def render_visual_analytics(data_manager, map_manager, analytics):
    """Render visual analytics section"""
    
    # Two-column layout
    map_col, charts_col = st.columns([1.5, 1])
    
    with map_col:
        render_geographic_overview(data_manager, map_manager, analytics)
    
    with charts_col:
        render_progress_charts(data_manager, analytics)


def render_geographic_overview(data_manager, map_manager, analytics):
    """Render geographic overview with map"""
    
    st.subheader("Geographic Distribution")
    
    victims = data_manager.get_all_victims()
    
    if victims:
        # Create comprehensive map with rescue station at center
        overview_map = map_manager.create_victim_map(
            victims=victims,
            center=st.session_state.map_center,
            show_rescued=True,
            show_heatmap=True,
            show_sectors=True,
            rssi_strong_threshold=st.session_state.rssi_strong_threshold,
            rssi_weak_threshold=st.session_state.rssi_weak_threshold,
            time_critical_threshold=st.session_state.time_critical_threshold
        )
        
        st_folium(overview_map, width=None, height=500, returned_objects=[])
        
        # Geographic statistics
        density = analytics.analyze_geographic_density()
        coverage = analytics.get_coverage_area()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Sectors",
                density['total_sectors'],
                help="Number of geographic sectors with victims"
            )
        
        with col2:
            st.metric(
                "Coverage Area",
                f"{coverage['area_km2']:.2f} km²",
                help="Total operational area covered"
            )
        
        with col3:
            st.metric(
                "Max Density",
                density['highest_density_count'],
                help="Maximum victims in single sector"
            )
    
    else:
        st.info("No geographic data available yet")


def render_progress_charts(data_manager, analytics):
    """Render progress and status charts"""
    
    st.subheader("Progress Analytics")
    
    stats = data_manager.get_statistics()
    
    if stats['total'] > 0:
        # Status Distribution Pie Chart
        render_status_pie_chart(stats)
        
        st.markdown("---")
        
        # Signal Strength Analysis
        render_signal_analysis(analytics)
        
        st.markdown("---")
        
        # Priority Distribution
        render_priority_distribution(analytics)
    
    else:
        st.info("Waiting for data to generate charts...")


def render_status_pie_chart(stats):
    """Render status distribution pie chart"""
    
    st.markdown("**Status Distribution**")
    
    fig = go.Figure(data=[go.Pie(
        labels=['Stranded', 'En-Route', 'Rescued'],
        values=[stats['stranded'], stats['enroute'], stats['rescued']],
        marker=dict(colors=[
            config.STATUS_COLORS[config.STATUS_STRANDED],
            config.STATUS_COLORS[config.STATUS_EN_ROUTE],
            config.STATUS_COLORS[config.STATUS_RESCUED]
        ]),
        hole=0.4,
        textinfo='label+percent',
        textfont=dict(size=12),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_signal_analysis(analytics):
    """Render signal strength analysis"""
    
    st.markdown("**Signal Strength Distribution**")
    
    signal_data = analytics.analyze_signal_trends()
    
    # Bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=['Strong', 'Medium', 'Weak'],
            y=[
                signal_data['strong_signals'],
                signal_data['medium_signals'],
                signal_data['weak_signals']
            ],
            marker=dict(color=[
                config.SIGNAL_COLORS['strong'],
                config.SIGNAL_COLORS['medium'],
                config.SIGNAL_COLORS['weak']
            ]),
            text=[
                signal_data['strong_signals'],
                signal_data['medium_signals'],
                signal_data['weak_signals']
            ],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Signal Category",
        yaxis_title="Count",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Average RSSI
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Avg RSSI",
            f"{signal_data['average_rssi']:.1f} dBm"
        )
    with col2:
        st.metric(
            "Median RSSI",
            f"{signal_data['median_rssi']:.1f} dBm"
        )


def render_priority_distribution(analytics):
    """Render priority distribution"""
    
    st.markdown("**Priority Levels**")
    
    priority_dist = analytics.calculate_priority_distribution(
        rssi_strong_threshold=st.session_state.rssi_strong_threshold,
        rssi_weak_threshold=st.session_state.rssi_weak_threshold,
        time_critical_threshold=st.session_state.time_critical_threshold
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "High",
            priority_dist['high'],
            help="Requires immediate attention"
        )
    
    with col2:
        st.metric(
            "Medium",
            priority_dist['medium'],
            help="Standard priority"
        )
    
    with col3:
        st.metric(
            "Low",
            priority_dist['low'],
            help="Stable condition"
        )


def render_detailed_analytics(analytics):
    """Render detailed analytics sections"""
    
    st.subheader("Detailed Analytics")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Rescue Performance",
        "Sector Analysis",
        "Critical Cases",
        "Operation Summary"
    ])
    
    with tab1:
        render_rescue_performance(analytics)
    
    with tab2:
        render_sector_analysis(analytics)
    
    with tab3:
        render_critical_cases(analytics)
    
    with tab4:
        render_operation_summary(analytics)


def render_rescue_performance(analytics):
    """Render rescue performance metrics"""
    
    rescue_metrics = analytics.calculate_rescue_rate()
    efficiency = analytics.calculate_rescue_efficiency()
    
    if rescue_metrics['total_rescued'] > 0:
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Rescued",
                rescue_metrics['total_rescued']
            )
        
        with col2:
            st.metric(
                "Avg Rescue Time",
                f"{rescue_metrics['average_rescue_time_minutes']:.1f} min"
            )
        
        with col3:
            st.metric(
                "Fastest Rescue",
                f"{rescue_metrics['fastest_rescue_minutes']:.1f} min"
            )
        
        with col4:
            st.metric(
                "Slowest Rescue",
                f"{rescue_metrics['slowest_rescue_minutes']:.1f} min"
            )
        
        st.markdown("---")
        
        # Efficiency assessment
        st.markdown("### Efficiency Assessment")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Gauge chart for efficiency
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=efficiency['efficiency_percentage'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Efficiency Score"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': config.STATUS_COLORS[config.STATUS_RESCUED]},
                    'steps': [
                        {'range': [0, 40], 'color': "#ffcccc"},
                        {'range': [40, 60], 'color': "#fff4cc"},
                        {'range': [60, 80], 'color': "#ccffcc"},
                        {'range': [80, 100], 'color': "#ccffee"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown(f"**Overall Grade:** `{efficiency['grade']}`")
            st.markdown(f"**Rescue Rate:** {rescue_metrics['rescues_per_hour']:.2f} victims per hour")
            
            # Performance assessment
            if efficiency['efficiency_percentage'] >= 80:
                st.success("Excellent performance! Operation is highly efficient.")
            elif efficiency['efficiency_percentage'] >= 60:
                st.info("Good performance. Operation proceeding well.")
            elif efficiency['efficiency_percentage'] >= 40:
                st.warning("Fair performance. Consider optimizing rescue strategies.")
            else:
                st.error("Performance needs improvement. Review operational procedures.")
    
    else:
        st.info("No rescue data available yet")


def render_sector_analysis(analytics):
    """Render sector-by-sector analysis"""
    
    density = analytics.analyze_geographic_density()
    recommendations = analytics.get_sector_recommendations()
    
    if recommendations:
        st.markdown("### Sector Priority Recommendations")
        
        # Create DataFrame for better visualization
        df = pd.DataFrame(recommendations)
        
        # Format columns
        df_display = df.copy()
        df_display['rescue_percentage'] = df_display['rescue_percentage'].apply(lambda x: f"{x:.1f}%")
        df_display['priority_score'] = df_display['priority_score'].apply(lambda x: f"{x:.2f}")
        
        # Display table
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "sector_id": st.column_config.TextColumn("Sector", width="small"),
                "stranded_count": st.column_config.NumberColumn("Stranded", width="small"),
                "rescue_percentage": st.column_config.TextColumn("Rescued %", width="small"),
                "priority_score": st.column_config.TextColumn("Priority Score", width="small"),
                "recommendation": st.column_config.TextColumn("Recommendation", width="large")
            }
        )
        
        # Bar chart of stranded by sector
        top_sectors = df.nlargest(5, 'stranded_count')
        
        if not top_sectors.empty:
            fig = go.Figure(data=[
                go.Bar(
                    x=top_sectors['sector_id'],
                    y=top_sectors['stranded_count'],
                    marker=dict(
                        color=top_sectors['stranded_count'],
                        colorscale='Reds',
                        showscale=False
                    ),
                    text=top_sectors['stranded_count'],
                    textposition='auto',
                    hovertemplate='<b>Sector %{x}</b><br>Stranded: %{y}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title="Top 5 Sectors by Stranded Count",
                xaxis_title="Sector ID",
                yaxis_title="Stranded Victims",
                height=300,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No sector data available yet")


def render_critical_cases(analytics):
    """Render critical cases requiring immediate attention"""
    
    critical_victims = analytics.identify_critical_victims()
    
    if critical_victims:
        st.markdown(f"### Critical Cases ({len(critical_victims)})")
        st.warning("These victims require immediate attention")
        
        # Display critical victims
        for idx, victim in enumerate(critical_victims[:10], 1):  # Top 10
            with st.expander(f"#{idx} - ID: {victim['id']} | {victim['reason']}", expanded=idx <= 3):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Location:** {victim['lat']:.6f}, {victim['lon']:.6f}")
                    st.markdown(f"**Signal:** {victim['rssi']} dBm")
                
                with col2:
                    st.markdown(f"**Priority:** {victim['priority']}")
                    st.markdown(f"**Last Update:** {victim['minutes_since_update']:.1f} min ago")
                
                st.markdown(f"**Reason for Alert:** {victim['reason']}")
    
    else:
        st.success("No critical cases at this time")


def render_operation_summary(analytics):
    """Render comprehensive operation summary"""
    
    summary = analytics.generate_operation_summary(
        rssi_strong_threshold=st.session_state.rssi_strong_threshold,
        rssi_weak_threshold=st.session_state.rssi_weak_threshold,
        time_critical_threshold=st.session_state.time_critical_threshold,
        rescue_centre_lat=st.session_state.get('rescue_centre_lat', 13.022),
        rescue_centre_lon=st.session_state.get('rescue_centre_lon', 77.587)
    )
    
    st.markdown("### Operation Summary Report")
    
    # Basic stats
    st.markdown("#### Basic Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total", summary['basic_stats']['total'])
    with col2:
        st.metric("Stranded", summary['basic_stats']['stranded'])
    with col3:
        st.metric("En-Route", summary['basic_stats']['enroute'])
    with col4:
        st.metric("Rescued", summary['basic_stats']['rescued'])
    
    st.markdown("---")
    
    # Rescue metrics
    st.markdown("#### Rescue Performance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Rescues/Hour",
            f"{summary['rescue_metrics']['rescues_per_hour']:.2f}"
        )
    with col2:
        st.metric(
            "Avg Time",
            f"{summary['rescue_metrics']['average_rescue_time_minutes']:.1f} min"
        )
    with col3:
        st.metric(
            "Fastest",
            f"{summary['rescue_metrics']['fastest_rescue_minutes']:.1f} min"
        )
    
    st.markdown("---")
    
    # Geographic analysis
    st.markdown("#### Geographic Coverage")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sectors", summary['geographic_analysis']['total_sectors'])
    with col2:
        st.metric("Max Density", summary['geographic_analysis']['highest_density'])
    with col3:
        st.metric("Coverage Distance", f"{summary['geographic_analysis']['coverage_distance_km']:.2f} km")
    with col4:
        st.metric("Coverage Area", f"{summary['geographic_analysis']['coverage_area_km2']:.2f} km²")
    
    st.markdown("---")
    
    # Signal & Time analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Signal Analysis")
        st.metric("Average RSSI", f"{summary['signal_analysis']['average_rssi']:.1f} dBm")
        st.metric("Weak Signals", summary['signal_analysis']['weak_signals'])
        st.metric("Deteriorating", summary['signal_analysis']['deteriorating_count'])
    
    with col2:
        st.markdown("#### Time Analysis")
        st.metric("Operation Time", f"{summary['time_analysis']['operation_duration_hours']:.1f} hours")
        st.metric("Detection Rate", f"{summary['time_analysis']['detections_per_hour']:.1f}/hr")
        st.metric("Stale Data", summary['time_analysis']['stale_data_count'])