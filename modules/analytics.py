"""
Analytics Module
Advanced statistics, calculations, and data analysis
Provides insights for rescue operations
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

import config


class Analytics:
    """
    Advanced analytics and statistics for victim data
    
    Features:
    - Rescue rate calculations
    - Geographic density analysis
    - Signal strength trends
    - Time-based analytics
    - Performance metrics
    """
    
    def __init__(self, data_manager):
        """
        Initialize analytics with data manager
        
        Args:
            data_manager: DataManager instance
        """
        self.data_manager = data_manager
    
    def calculate_rescue_rate(self, time_window_hours: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate rescue rate statistics
        
        Args:
            time_window_hours: Time window for calculation (None = all time)
            
        Returns:
            Dict with rescue rate metrics
        """
        
        rescued_victims = self.data_manager.get_victims_by_status(config.STATUS_RESCUED)
        
        if not rescued_victims:
            return {
                'total_rescued': 0,
                'rescues_per_hour': 0.0,
                'average_rescue_time_minutes': 0.0,
                'fastest_rescue_minutes': 0.0,
                'slowest_rescue_minutes': 0.0
            }
        
        rescue_times = []
        current_time = datetime.now()
        
        for victim in rescued_victims.values():
            try:
                first_detected = datetime.strptime(victim['FIRST_DETECTED'], "%Y-%m-%d %H:%M:%S")
                rescued_time = datetime.strptime(victim['RESCUED_TIME'], "%Y-%m-%d %H:%M:%S")
                
                # Calculate time to rescue
                time_to_rescue = (rescued_time - first_detected).total_seconds() / 60  # minutes
                rescue_times.append(time_to_rescue)
                
            except (KeyError, ValueError, TypeError):
                continue
        
        # Calculate operation duration
        all_victims = self.data_manager.get_all_victims()
        if all_victims:
            detection_times = []
            for victim in all_victims.values():
                try:
                    detected = datetime.strptime(victim['FIRST_DETECTED'], "%Y-%m-%d %H:%M:%S")
                    detection_times.append(detected)
                except (KeyError, ValueError):
                    continue
            
            if detection_times:
                operation_start = min(detection_times)
                operation_duration_hours = (current_time - operation_start).total_seconds() / 3600
            else:
                operation_duration_hours = 1.0
        else:
            operation_duration_hours = 1.0
        
        # Calculate metrics
        total_rescued = len(rescued_victims)
        rescues_per_hour = total_rescued / operation_duration_hours if operation_duration_hours > 0 else 0
        
        avg_rescue_time = np.mean(rescue_times) if rescue_times else 0.0
        fastest_rescue = np.min(rescue_times) if rescue_times else 0.0
        slowest_rescue = np.max(rescue_times) if rescue_times else 0.0
        
        return {
            'total_rescued': total_rescued,
            'rescues_per_hour': round(rescues_per_hour, 2),
            'average_rescue_time_minutes': round(avg_rescue_time, 2),
            'fastest_rescue_minutes': round(fastest_rescue, 2),
            'slowest_rescue_minutes': round(slowest_rescue, 2)
        }
    
    def analyze_geographic_density(self) -> Dict[str, Any]:
        """
        Analyze geographic distribution and density of victims
        
        Returns:
            Dict with density analysis
        """
        
        victims = self.data_manager.get_all_victims()
        
        if not victims:
            return {
                'total_sectors': 0,
                'sectors': {},
                'highest_density_sector': None,
                'highest_density_count': 0
            }
        
        # Get geographic clusters
        clusters = self.data_manager.get_geographic_clusters()
        
        # Analyze each sector
        sector_analysis = {}
        max_count = 0
        max_sector = None
        
        for sector_id, victim_ids in clusters.items():
            stranded = 0
            rescued = 0
            enroute = 0
            
            for vid in victim_ids:
                victim = victims.get(vid)
                if victim:
                    status = victim['STATUS']
                    if status == config.STATUS_STRANDED:
                        stranded += 1
                    elif status == config.STATUS_RESCUED:
                        rescued += 1
                    elif status == config.STATUS_EN_ROUTE:
                        enroute += 1
            
            total = len(victim_ids)
            
            sector_analysis[sector_id] = {
                'total': total,
                'stranded': stranded,
                'rescued': rescued,
                'enroute': enroute,
                'rescue_percentage': (rescued / total * 100) if total > 0 else 0
            }
            
            if total > max_count:
                max_count = total
                max_sector = sector_id
        
        return {
            'total_sectors': len(clusters),
            'sectors': sector_analysis,
            'highest_density_sector': max_sector,
            'highest_density_count': max_count
        }
    
    def analyze_signal_trends(self) -> Dict[str, Any]:
        """
        Analyze signal strength trends and patterns
        
        Returns:
            Dict with signal analysis
        """
        
        victims = self.data_manager.get_all_victims()
        
        if not victims:
            return {
                'average_rssi': 0,
                'median_rssi': 0,
                'weak_signals': 0,
                'medium_signals': 0,
                'strong_signals': 0,
                'deteriorating_signals': []
            }
        
        all_rssi = []
        deteriorating = []
        
        for vid, victim in victims.items():
            rssi = victim.get('RSSI', -999)
            if rssi != -999:
                all_rssi.append(rssi)
            
            # Check for deteriorating signal
            rssi_history = victim.get('RSSI_HISTORY', [])
            if len(rssi_history) >= 5:
                # Check if signal is getting weaker (more negative)
                recent_avg = np.mean(rssi_history[-3:])
                older_avg = np.mean(rssi_history[-6:-3])
                
                if recent_avg < older_avg - 5:  # Signal weakened by 5 dBm
                    deteriorating.append({
                        'id': vid,
                        'current_rssi': rssi,
                        'trend': 'weakening'
                    })
        
        # Get signal distribution
        signal_dist = self.data_manager.get_signal_distribution()
        
        return {
            'average_rssi': round(np.mean(all_rssi), 2) if all_rssi else 0,
            'median_rssi': round(np.median(all_rssi), 2) if all_rssi else 0,
            'weak_signals': signal_dist.get('weak', 0),
            'medium_signals': signal_dist.get('medium', 0),
            'strong_signals': signal_dist.get('strong', 0),
            'deteriorating_signals': deteriorating
        }
    
    def analyze_time_patterns(self) -> Dict[str, Any]:
        """
        Analyze time-based patterns in victim detection and rescue
        
        Returns:
            Dict with time analysis
        """
        
        victims = self.data_manager.get_all_victims()
        
        if not victims:
            return {
                'operation_duration_hours': 0,
                'detections_per_hour': 0,
                'stale_data_count': 0,
                'no_update_threshold_minutes': config.TIME_STALE_THRESHOLD
            }
        
        current_time = datetime.now()
        detection_times = []
        stale_count = 0
        
        for victim in victims.values():
            try:
                # First detection time
                detected = datetime.strptime(victim['FIRST_DETECTED'], "%Y-%m-%d %H:%M:%S")
                detection_times.append(detected)
                
                # Check for stale data
                last_update = datetime.strptime(victim['LAST_UPDATE'], "%Y-%m-%d %H:%M:%S")
                time_since_update = (current_time - last_update).total_seconds() / 60
                
                if time_since_update > config.TIME_STALE_THRESHOLD:
                    stale_count += 1
                    
            except (KeyError, ValueError, TypeError):
                continue
        
        if detection_times:
            operation_start = min(detection_times)
            operation_duration = (current_time - operation_start).total_seconds() / 3600
            detections_per_hour = len(victims) / operation_duration if operation_duration > 0 else 0
        else:
            operation_duration = 0
            detections_per_hour = 0
        
        return {
            'operation_duration_hours': round(operation_duration, 2),
            'detections_per_hour': round(detections_per_hour, 2),
            'stale_data_count': stale_count,
            'no_update_threshold_minutes': config.TIME_STALE_THRESHOLD
        }
    
    def calculate_priority_distribution(self, rssi_strong_threshold=None, rssi_weak_threshold=None,
                                       time_critical_threshold=None) -> Dict[str, int]:
        """
        Calculate distribution of victims by priority level
        
        Args:
            rssi_strong_threshold: Strong signal threshold (optional)
            rssi_weak_threshold: Weak signal threshold (optional)
            time_critical_threshold: Critical time threshold in minutes (optional)
        
        Returns:
            Dict with priority counts
        """
        
        from utils.helpers import calculate_priority
        
        victims = self.data_manager.get_victims_by_status(config.STATUS_STRANDED)
        
        high = 0
        medium = 0
        low = 0
        
        for victim in victims.values():
            priority, _ = calculate_priority(
                victim,
                rssi_strong_threshold=rssi_strong_threshold,
                rssi_weak_threshold=rssi_weak_threshold,
                time_critical_threshold=time_critical_threshold
            )
            
            if priority == "HIGH":
                high += 1
            elif priority == "MEDIUM":
                medium += 1
            else:
                low += 1
        
        return {
            'high': high,
            'medium': medium,
            'low': low
        }
    
    def get_coverage_area(self, rescue_centre_lat=None, rescue_centre_lon=None) -> Dict[str, float]:
        """
        Calculate the coverage distance from rescue station to first victim beacon
        
        Args:
            rescue_centre_lat: Rescue centre/station latitude
            rescue_centre_lon: Rescue centre/station longitude
        
        Returns:
            Dict with coverage metrics (distance from station to first beacon)
        """
        
        victims = self.data_manager.get_all_victims()
        
        if not victims:
            return {
                'min_lat': 0,
                'max_lat': 0,
                'min_lon': 0,
                'max_lon': 0,
                'area_km2': 0,
                'distance_km': 0
            }
        
        # Get all victims with valid coordinates
        victims_with_coords = [v for v in victims.values() if v['LAT'] != 0 and v['LON'] != 0]
        
        if not victims_with_coords:
            return {
                'min_lat': 0,
                'max_lat': 0,
                'min_lon': 0,
                'max_lon': 0,
                'area_km2': 0,
                'distance_km': 0
            }
        
        # Get the first victim (earliest ping)
        first_victim = min(victims_with_coords, key=lambda v: v.get('FIRST_PING', v.get('LAST_UPDATE', '9999-12-31')))
        
        # Use provided rescue centre or default values
        if rescue_centre_lat is None:
            rescue_centre_lat = 13.022
        if rescue_centre_lon is None:
            rescue_centre_lon = 77.587
        
        # Calculate distance from rescue centre to first victim using Haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = radians(rescue_centre_lat), radians(rescue_centre_lon)
        lat2, lon2 = radians(first_victim['LAT']), radians(first_victim['LON'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance_km = R * c
        
        # Calculate lat/lon range from rescue centre to first victim
        min_lat = min(rescue_centre_lat, first_victim['LAT'])
        max_lat = max(rescue_centre_lat, first_victim['LAT'])
        min_lon = min(rescue_centre_lon, first_victim['LON'])
        max_lon = max(rescue_centre_lon, first_victim['LON'])
        
        # Area is the bounding box from rescue centre to first victim
        lat_diff_km = (max_lat - min_lat) * 111
        lon_diff_km = (max_lon - min_lon) * 111 * np.cos(np.radians((min_lat + max_lat) / 2))
        area_km2 = lat_diff_km * lon_diff_km
        
        return {
            'min_lat': round(min_lat, 6),
            'max_lat': round(max_lat, 6),
            'min_lon': round(min_lon, 6),
            'max_lon': round(max_lon, 6),
            'area_km2': round(area_km2, 2),
            'distance_km': round(distance_km, 2)
        }
    
    def generate_operation_summary(self, rssi_strong_threshold=None, rssi_weak_threshold=None,
                                  time_critical_threshold=None, rescue_centre_lat=None, 
                                  rescue_centre_lon=None) -> Dict[str, Any]:
        """
        Generate comprehensive operation summary
        
        Args:
            rssi_strong_threshold: Strong signal threshold (optional)
            rssi_weak_threshold: Weak signal threshold (optional)
            time_critical_threshold: Critical time threshold in minutes (optional)
            rescue_centre_lat: Rescue centre latitude (optional)
            rescue_centre_lon: Rescue centre longitude (optional)
        
        Returns:
            Dict with complete operation summary
        """
        
        stats = self.data_manager.get_statistics()
        rescue_rate = self.calculate_rescue_rate()
        density = self.analyze_geographic_density()
        signals = self.analyze_signal_trends()
        time_patterns = self.analyze_time_patterns()
        priority = self.calculate_priority_distribution(
            rssi_strong_threshold=rssi_strong_threshold,
            rssi_weak_threshold=rssi_weak_threshold,
            time_critical_threshold=time_critical_threshold
        )
        coverage = self.get_coverage_area(
            rescue_centre_lat=rescue_centre_lat,
            rescue_centre_lon=rescue_centre_lon
        )
        
        return {
            'basic_stats': stats,
            'rescue_metrics': rescue_rate,
            'geographic_analysis': {
                'total_sectors': density['total_sectors'],
                'highest_density': density['highest_density_count'],
                'coverage_area_km2': coverage['area_km2'],
                'coverage_distance_km': coverage.get('distance_km', 0)
            },
            'signal_analysis': {
                'average_rssi': signals['average_rssi'],
                'weak_signals': signals['weak_signals'],
                'deteriorating_count': len(signals['deteriorating_signals'])
            },
            'time_analysis': time_patterns,
            'priority_distribution': priority
        }
    
    def identify_critical_victims(self) -> List[Dict[str, Any]]:
        """
        Identify victims requiring immediate attention
        
        Returns:
            List of critical victim information
        """
        
        from utils.helpers import calculate_priority
        
        victims = self.data_manager.get_victims_by_status(config.STATUS_STRANDED)
        critical = []
        
        current_time = datetime.now()
        
        for vid, victim in victims.items():
            priority, _ = calculate_priority(victim)
            
            # Check if high priority
            if priority == "HIGH":
                try:
                    last_update = datetime.strptime(victim['LAST_UPDATE'], "%Y-%m-%d %H:%M:%S")
                    minutes_since_update = (current_time - last_update).total_seconds() / 60
                except:
                    minutes_since_update = 999
                
                critical.append({
                    'id': vid,
                    'lat': victim['LAT'],
                    'lon': victim['LON'],
                    'rssi': victim['RSSI'],
                    'minutes_since_update': round(minutes_since_update, 1),
                    'priority': priority,
                    'reason': self._get_critical_reason(victim)
                })
        
        # Sort by severity (weakest signal or longest time)
        critical.sort(key=lambda x: (x['rssi'], -x['minutes_since_update']))
        
        return critical
    
    def _get_critical_reason(self, victim: Dict[str, Any]) -> str:
        """
        Determine reason for critical status
        
        Args:
            victim: Victim data dict
            
        Returns:
            String describing reason
        """
        
        reasons = []
        
        rssi = victim.get('RSSI', -999)
        if rssi < config.RSSI_WEAK_THRESHOLD:
            reasons.append(f"Weak signal ({rssi} dBm)")
        
        try:
            last_update = datetime.strptime(victim['LAST_UPDATE'], "%Y-%m-%d %H:%M:%S")
            minutes = (datetime.now() - last_update).total_seconds() / 60
            
            if minutes > config.TIME_CRITICAL_THRESHOLD:
                reasons.append(f"No update for {int(minutes)} minutes")
        except:
            pass
        
        return ", ".join(reasons) if reasons else "Unknown"
    
    def calculate_rescue_efficiency(self) -> Dict[str, float]:
        """
        Calculate overall rescue operation efficiency metrics
        
        Returns:
            Dict with efficiency metrics
        """
        
        stats = self.data_manager.get_statistics()
        rescue_rate = self.calculate_rescue_rate()
        
        total = stats['total']
        rescued = stats['rescued']
        
        efficiency_score = (rescued / total * 100) if total > 0 else 0
        
        # Grade efficiency
        if efficiency_score >= 80:
            grade = "Excellent"
        elif efficiency_score >= 60:
            grade = "Good"
        elif efficiency_score >= 40:
            grade = "Fair"
        else:
            grade = "Needs Improvement"
        
        return {
            'efficiency_percentage': round(efficiency_score, 2),
            'grade': grade,
            'total_detected': total,
            'total_rescued': rescued,
            'average_rescue_time_minutes': rescue_rate['average_rescue_time_minutes'],
            'rescues_per_hour': rescue_rate['rescues_per_hour']
        }
    
    def get_sector_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for which sectors to prioritize
        
        Returns:
            List of sector recommendations
        """
        
        density = self.analyze_geographic_density()
        sectors = density.get('sectors', {})
        
        recommendations = []
        
        for sector_id, data in sectors.items():
            stranded = data['stranded']
            rescue_pct = data['rescue_percentage']
            
            # High stranded count and low rescue percentage = priority
            if stranded > 0:
                priority_score = stranded * (1 - rescue_pct / 100)
                
                recommendations.append({
                    'sector_id': sector_id,
                    'stranded_count': stranded,
                    'rescue_percentage': round(rescue_pct, 1),
                    'priority_score': round(priority_score, 2),
                    'recommendation': self._get_sector_recommendation(stranded, rescue_pct)
                })
        
        # Sort by priority score (descending)
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return recommendations
    
    def _get_sector_recommendation(self, stranded: int, rescue_pct: float) -> str:
        """
        Generate recommendation text for a sector
        
        Args:
            stranded: Number of stranded victims
            rescue_pct: Rescue percentage
            
        Returns:
            Recommendation string
        """
        
        if stranded >= 5 and rescue_pct < 30:
            return "HIGH PRIORITY - Many victims, low rescue rate"
        elif stranded >= 3 and rescue_pct < 50:
            return "MEDIUM PRIORITY - Deploy rescue team"
        elif stranded > 0 and rescue_pct < 70:
            return "LOW PRIORITY - Monitor situation"
        else:
            return "Under control"