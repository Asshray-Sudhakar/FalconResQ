"""
Map Manager Module
Handles map creation and rendering with Google Maps integration
Creates interactive maps with victim markers and overlays
"""

import folium
from folium import plugins
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

import config
from utils.helpers import calculate_priority, get_signal_color, format_time_ago


class MapManager:
    """
    Manages map creation and visualization
    
    Features:
    - Google Maps integration
    - Color-coded victim markers
    - Popup information cards
    - Heatmap overlays
    - Sector grid visualization
    - Custom styling
    """
    
    def __init__(self):
        """Initialize the map manager"""
        self.default_center = config.get_map_config()['center']
        self.default_zoom = config.get_map_config()['zoom']
    
    def create_victim_map(
        self,
        victims: Dict[int, Dict[str, Any]],
        center: Optional[List[float]] = None,
        zoom: Optional[int] = None,
        show_rescued: bool = True,
        show_priority_only: bool = False,
        show_heatmap: bool = False,
        show_sectors: bool = False,
        rssi_strong_threshold: int = None,
        rssi_weak_threshold: int = None,
        time_critical_threshold: int = None
    ) -> folium.Map:
        """
        Create interactive map with victim markers
        
        Args:
            victims: Dictionary of victim data
            center: Map center [lat, lon] (auto-calculated if None)
            zoom: Zoom level (default from config if None)
            show_rescued: Include rescued victims on map
            show_priority_only: Show only high-priority victims
            show_heatmap: Add density heatmap overlay
            show_sectors: Add sector grid overlay
            rssi_strong_threshold: Strong signal threshold (optional)
            rssi_weak_threshold: Weak signal threshold (optional)
            time_critical_threshold: Critical time threshold in minutes (optional)
            
        Returns:
            Folium map object
        """
        
        # Calculate center if not provided
        if center is None and victims:
            center = self._calculate_map_center(victims)
        elif center is None:
            center = self.default_center
        
        if zoom is None:
            zoom = self.default_zoom
        
        # Create base map with Google tiles
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles=None  # We'll add custom tiles
        )
        
        # Add Google Maps tiles
        folium.TileLayer(
            tiles=config.MAP_TILE_PROVIDERS['google_roadmap'],
            attr='Google Maps',
            name='Google Roadmap',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add satellite view option
        folium.TileLayer(
            tiles=config.MAP_TILE_PROVIDERS['google_satellite'],
            attr='Google Satellite',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add victim markers
        if victims:
            self._add_victim_markers(
                m, 
                victims, 
                show_rescued, 
                show_priority_only,
                rssi_strong_threshold=rssi_strong_threshold,
                rssi_weak_threshold=rssi_weak_threshold,
                time_critical_threshold=time_critical_threshold,
                station_location=center
            )
        
        # Add rescue station (computer location) with home icon
        self._add_rescue_station(m, center)
        
        # Add heatmap overlay if requested
        if show_heatmap and victims:
            self._add_heatmap_layer(m, victims, show_rescued)
        
        # Add sector grid if requested
        if show_sectors and victims:
            self._add_sector_grid(m, victims)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add legend with thresholds
        self._add_legend(m, rssi_strong_threshold, rssi_weak_threshold, time_critical_threshold)
        
        return m
    
    def _add_victim_markers(
        self,
        map_obj: folium.Map,
        victims: Dict[int, Dict[str, Any]],
        show_rescued: bool,
        show_priority_only: bool,
        station_location: List[float] = None,
        rssi_strong_threshold: int = None,
        rssi_weak_threshold: int = None,
        time_critical_threshold: int = None
    ):
        """
        Add victim markers to map
        
        Args:
            map_obj: Folium map object
            victims: Victim data dictionary
            show_rescued: Include rescued victims
            show_priority_only: Show only high-priority victims
            station_location: Rescue station location
            rssi_strong_threshold: Strong signal threshold (optional)
            rssi_weak_threshold: Weak signal threshold (optional)
            time_critical_threshold: Critical time threshold in minutes (optional)
        """
        
        for vid, victim in victims.items():
            # Skip invalid coordinates
            if victim['LAT'] == 0 and victim['LON'] == 0:
                continue
            
            status = victim['STATUS']
            
            # Skip rescued if not showing them
            if status == config.STATUS_RESCUED and not show_rescued:
                continue
            
            # Filter by priority if needed
            if show_priority_only:
                priority, _ = calculate_priority(
                    victim,
                    rssi_strong_threshold=rssi_strong_threshold,
                    rssi_weak_threshold=rssi_weak_threshold,
                    time_critical_threshold=time_critical_threshold
                )
                if priority != "HIGH":
                    continue
            
            # Determine marker properties
            marker_color, icon_name, opacity = self._get_marker_properties(victim)
            
            # Create popup content
            popup_html = self._create_popup_html(victim, station_location)
            
            # Create marker
            folium.Marker(
                location=[victim['LAT'], victim['LON']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"ID: {vid} - {status}",
                icon=folium.Icon(
                    color=marker_color,
                    icon=icon_name,
                    prefix='fa'
                ),
                opacity=opacity
            ).add_to(map_obj)
    
    def _get_marker_properties(self, victim: Dict[str, Any]) -> Tuple[str, str, float]:
        """
        Get marker color, icon, and opacity based on victim status
        
        Args:
            victim: Victim data dictionary
            
        Returns:
            Tuple of (color, icon_name, opacity)
        """
        
        status = victim['STATUS']
        
        if status == config.STATUS_STRANDED:
            return config.MARKER_COLORS[status], 'exclamation-circle', 1.0
        
        elif status == config.STATUS_EN_ROUTE:
            return config.MARKER_COLORS[status], 'ambulance', 1.0
        
        elif status == config.STATUS_RESCUED:
            return config.MARKER_COLORS[status], 'check-circle', 0.6
        
        return 'gray', 'question-circle', 1.0
    
    def _create_popup_html(self, victim: Dict[str, Any], station_location: List[float] = None) -> str:
        """
        Create HTML content for marker popup
        
        Args:
            victim: Victim data dictionary
            station_location: Rescue station coordinates [lat, lon]
            
        Returns:
            HTML string for popup
        """
        
        # Calculate priority and signal strength
        priority, priority_label = calculate_priority(victim)
        signal_label, signal_color = get_signal_color(victim['RSSI'])
        
        # Format time
        last_update_str = format_time_ago(victim['LAST_UPDATE'])
        
        # Calculate distance from rescue station
        distance_html = ""
        if station_location:
            distance = self._calculate_distance(
                station_location[0], station_location[1],
                victim['LAT'], victim['LON']
            )
            distance_html = f"""
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Distance:</td>
                    <td style="padding: 4px 0;"><strong style="color: #d9534f;">{distance:.2f} km</strong></td>
                </tr>
            """
        
        # Build HTML
        html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; min-width: 250px;">
            <h4 style="margin: 0 0 10px 0; padding: 0; color: #333; border-bottom: 2px solid {config.STATUS_COLORS[victim['STATUS']]};">
                Victim ID: {victim['ID']}
            </h4>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 4px 0; font-weight: bold; width: 40%;">Status:</td>
                    <td style="padding: 4px 0; color: {config.STATUS_COLORS[victim['STATUS']]};">
                        <strong>{victim['STATUS']}</strong>
                    </td>
                </tr>
                
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Priority:</td>
                    <td style="padding: 4px 0;">
                        <span style="background: {self._get_priority_color(priority)}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">
                            {priority}
                        </span>
                    </td>
                </tr>
                
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Location:</td>
                    <td style="padding: 4px 0; font-family: monospace; font-size: 11px;">
                        {victim['LAT']:.6f}, {victim['LON']:.6f}
                    </td>
                </tr>
                
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Signal:</td>
                    <td style="padding: 4px 0;">
                        <span style="color: {signal_color}; font-weight: bold;">{victim['RSSI']} dBm</span>
                        <span style="font-size: 11px; color: #666;">({signal_label})</span>
                    </td>
                </tr>
                
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Last Update:</td>
                    <td style="padding: 4px 0; color: #666;">{last_update_str}</td>
                </tr>
                
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Updates:</td>
                    <td style="padding: 4px 0;">{victim.get('UPDATE_COUNT', 0)} packets</td>
                </tr>
                {distance_html}
        """
        
        # Add rescue information if rescued
        if victim['STATUS'] == config.STATUS_RESCUED:
            rescued_by = victim.get('RESCUED_BY', 'Unknown')
            rescued_time = format_time_ago(victim.get('RESCUED_TIME', ''))
            
            html += f"""
                <tr>
                    <td colspan="2" style="padding: 8px 0 4px 0; border-top: 1px solid #ddd;">
                        <strong style="color: {config.STATUS_COLORS[config.STATUS_RESCUED]};">Rescue Information</strong>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Rescued By:</td>
                    <td style="padding: 4px 0;">{rescued_by}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Rescued:</td>
                    <td style="padding: 4px 0; color: #666;">{rescued_time}</td>
                </tr>
            """
            
            if victim.get('NOTES'):
                html += f"""
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Notes:</td>
                    <td style="padding: 4px 0; font-style: italic; color: #555;">{victim['NOTES']}</td>
                </tr>
                """
        
        html += """
            </table>
        </div>
        """
        
        return html
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority level"""
        if priority == "HIGH":
            return "#dc3545"  # Red
        elif priority == "MEDIUM":
            return "#ffc107"  # Yellow
        else:
            return "#28a745"  # Green
    
    def _add_heatmap_layer(
        self,
        map_obj: folium.Map,
        victims: Dict[int, Dict[str, Any]],
        show_rescued: bool
    ):
        """
        Add heatmap overlay showing victim density
        
        Args:
            map_obj: Folium map object
            victims: Victim data dictionary
            show_rescued: Include rescued victims in heatmap
        """
        
        heat_data = []
        
        for victim in victims.values():
            # Skip invalid coordinates
            if victim['LAT'] == 0 and victim['LON'] == 0:
                continue
            
            # Skip rescued if not showing them
            if victim['STATUS'] == config.STATUS_RESCUED and not show_rescued:
                continue
            
            heat_data.append([victim['LAT'], victim['LON']])
        
        if heat_data:
            plugins.HeatMap(
                heat_data,
                name='Density Heatmap',
                min_opacity=0.3,
                max_opacity=0.8,
                radius=15,
                blur=20,
                gradient={
                    0.0: 'blue',
                    0.5: 'yellow',
                    1.0: 'red'
                }
            ).add_to(map_obj)
    
    def _add_sector_grid(
        self,
        map_obj: folium.Map,
        victims: Dict[int, Dict[str, Any]]
    ):
        """
        Add sector grid overlay with statistics
        
        Args:
            map_obj: Folium map object
            victims: Victim data dictionary
        """
        
        # Get coverage area
        lats = [v['LAT'] for v in victims.values() if v['LAT'] != 0]
        lons = [v['LON'] for v in victims.values() if v['LON'] != 0]
        
        if not lats or not lons:
            return
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Expand bounds slightly
        padding = 0.005
        min_lat -= padding
        max_lat += padding
        min_lon -= padding
        max_lon += padding
        
        sector_size = config.SECTOR_SIZE_LAT
        
        # Create grid
        lat = min_lat
        while lat < max_lat:
            lon = min_lon
            while lon < max_lon:
                # Count victims in this sector
                sector_victims = 0
                for v in victims.values():
                    if (lat <= v['LAT'] < lat + sector_size and
                        lon <= v['LON'] < lon + sector_size):
                        sector_victims += 1
                
                # Draw rectangle if there are victims
                if sector_victims > 0:
                    folium.Rectangle(
                        bounds=[[lat, lon], [lat + sector_size, lon + sector_size]],
                        color='blue',
                        fill=True,
                        fillColor='blue',
                        fillOpacity=0.1,
                        weight=1,
                        popup=f"Sector: {sector_victims} victim(s)"
                    ).add_to(map_obj)
                
                lon += sector_size
            lat += sector_size
    
    def _calculate_map_center(self, victims: Dict[int, Dict[str, Any]]) -> List[float]:
        """
        Calculate optimal map center based on victim locations
        
        Args:
            victims: Victim data dictionary
            
        Returns:
            [lat, lon] center coordinates
        """
        
        lats = [v['LAT'] for v in victims.values() if v['LAT'] != 0]
        lons = [v['LON'] for v in victims.values() if v['LON'] != 0]
        
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            return [center_lat, center_lon]
        
        return self.default_center
    
    def _add_legend(self, map_obj: folium.Map, rssi_strong_threshold: int = None, 
                    rssi_weak_threshold: int = None, time_critical_threshold: int = None):
        """
        Add map legend explaining marker colors and thresholds
        
        Args:
            map_obj: Folium map object
            rssi_strong_threshold: Strong signal threshold (optional)
            rssi_weak_threshold: Weak signal threshold (optional)
            time_critical_threshold: Critical time threshold in minutes (optional)
        """
        
        # Use config defaults if not provided
        if rssi_strong_threshold is None:
            rssi_strong_threshold = config.RSSI_STRONG_THRESHOLD
        if rssi_weak_threshold is None:
            rssi_weak_threshold = config.RSSI_WEAK_THRESHOLD
        if time_critical_threshold is None:
            time_critical_threshold = config.TIME_CRITICAL_THRESHOLD
        
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; 
                    width: 220px; 
                    background-color: white; 
                    border: 2px solid grey; 
                    border-radius: 5px;
                    z-index: 9999; 
                    font-size: 12px;
                    padding: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 10px 0; padding: 0; font-size: 13px; color: black;">Status Legend</h4>
            
            <div style="margin: 5px 0;">
                <i class="fa fa-map-marker" style="color: red; margin-right: 5px;"></i>
                <span style="color: black;">Stranded</span>
            </div>
            
            <div style="margin: 5px 0;">
                <i class="fa fa-map-marker" style="color: orange; margin-right: 5px;"></i>
                <span style="color: black;">En-Route</span>
            </div>
            
            <div style="margin: 5px 0;">
                <i class="fa fa-map-marker" style="color: green; margin-right: 5px;"></i>
                <span style="color: black;">Rescued</span>
            </div>
            
            <hr style="margin: 10px 0;">
            
            <h4 style="margin: 10px 0 5px 0; padding: 0; font-size: 13px; color: black;">Signal Strength</h4>
            
            <div style="margin: 5px 0; font-size: 11px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: #28a745; margin-right: 5px; border-radius: 2px;"></span>
                <span style="color: black;">Strong (&gt; {rssi_strong_threshold} dBm)</span>
            </div>
            
            <div style="margin: 5px 0; font-size: 11px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: #ffc107; margin-right: 5px; border-radius: 2px;"></span>
                <span style="color: black;">Medium ({rssi_weak_threshold} to {rssi_strong_threshold})</span>
            </div>
            
            <div style="margin: 5px 0; font-size: 11px;">
                <span style="display: inline-block; width: 12px; height: 12px; background: #dc3545; margin-right: 5px; border-radius: 2px;"></span>
                <span style="color: black;">Weak (&lt; {rssi_weak_threshold} dBm)</span>
            </div>
            
            <hr style="margin: 10px 0;">
            
            <h4 style="margin: 10px 0 5px 0; padding: 0; font-size: 13px; color: black;">Priority Thresholds</h4>
            <div style="margin: 5px 0; font-size: 11px; color: #555;">
                Critical: {time_critical_threshold} min no update
            </div>
        </div>
        """
        
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def _add_rescue_station(self, map_obj: folium.Map, center: List[float]):
        """
        Add rescue station marker (computer location) with small home icon
        
        Args:
            map_obj: Folium map object
            center: Center coordinates [lat, lon]
        """
        
        # Add small rescue station marker - using CircleMarker to minimize overlap with victim markers
        folium.CircleMarker(
            location=center,
            radius=6,  # Small size to avoid obscuring victim markers
            popup=folium.Popup(
                "<div style='font-family: Arial; font-size: 13px; color: black;'>"
                "<h4 style='color: #0066cc; margin: 0 0 5px 0;'>🏠 Rescue Station</h4>"
                "<p style='margin: 0;'><strong>Coordination Center</strong></p>"
                "<p style='margin: 5px 0 0 0; font-size: 11px; color: #666;'>Your Location</p>"
                "</div>",
                max_width=250
            ),
            tooltip="Rescue Station (Your Location)",
            color='#0066cc',  # Border color
            fill=True,
            fillColor='#0066cc',  # Blue fill
            fillOpacity=0.8,
            weight=2,
            opacity=1.0
        ).add_to(map_obj)
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lon1: First coordinate pair
            lat2, lon2: Second coordinate pair
            
        Returns:
            Distance in kilometers
        """
        
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def create_simple_map(
        self,
        center: Optional[List[float]] = None,
        zoom: Optional[int] = None
    ) -> folium.Map:
        """
        Create a simple base map without markers
        
        Args:
            center: Map center [lat, lon]
            zoom: Zoom level
            
        Returns:
            Folium map object
        """
        
        if center is None:
            center = self.default_center
        
        if zoom is None:
            zoom = self.default_zoom
        
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles=None
        )
        
        # Add Google Maps tiles
        folium.TileLayer(
            tiles=config.MAP_TILE_PROVIDERS['google_roadmap'],
            attr='Google Maps',
            name='Google Roadmap',
            overlay=False,
            control=True
        ).add_to(m)
        
        return m
    
    def calculate_optimal_zoom(self, victims: Dict[int, Dict[str, Any]]) -> int:
        """
        Calculate optimal zoom level based on victim spread
        
        Args:
            victims: Victim data dictionary
            
        Returns:
            Optimal zoom level (int)
        """
        
        if not victims:
            return self.default_zoom
        
        lats = [v['LAT'] for v in victims.values() if v['LAT'] != 0]
        lons = [v['LON'] for v in victims.values() if v['LON'] != 0]
        
        if not lats or not lons:
            return self.default_zoom
        
        # Calculate spread
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        # Determine zoom level based on spread
        if max_range > 0.5:
            return 10
        elif max_range > 0.1:
            return 12
        elif max_range > 0.05:
            return 13
        elif max_range > 0.01:
            return 14
        else:
            return 15