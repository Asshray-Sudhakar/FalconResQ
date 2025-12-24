"""
Data Manager Module
Manages victim data storage, retrieval, and state management
Handles CRUD operations and data persistence
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

import config


class DataManager:
    """
    Manages all victim data operations
    
    Features:
    - Add/Update victims (no duplication by ID)
    - Status management (STRANDED/EN_ROUTE/RESCUED)
    - Data persistence (auto-save to JSON)
    - Statistics calculation
    - Query and filtering
    """
    
    def __init__(self):
        """Initialize the data manager"""
        self.victims: Dict[int, Dict[str, Any]] = {}
        self.last_backup_time: Optional[datetime] = None
        
        # Do NOT load existing data automatically
        # Only data from live serial packets should be displayed
        # Backup is available for manual import only
    
    def add_or_update_victim(self, packet: Dict[str, Any]) -> bool:
        """
        Add new victim or update existing victim data
        No duplication - updates existing record if ID exists
        
        Args:
            packet: Victim data packet from serial port
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        try:
            victim_id = packet['ID']
            
            if victim_id in self.victims:
                # UPDATE existing victim
                self.victims[victim_id].update({
                    'LAT': packet['LAT'],
                    'LON': packet['LON'],
                    'TIME': packet['TIME'],
                    'RSSI': packet.get('RSSI', -999),
                    'LAST_UPDATE': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'UPDATE_COUNT': self.victims[victim_id].get('UPDATE_COUNT', 0) + 1
                })
                
                # Update RSSI history
                rssi_history = self.victims[victim_id].get('RSSI_HISTORY', [])
                rssi_history.append(packet.get('RSSI', -999))
                
                # Keep only last 20 RSSI readings
                if len(rssi_history) > 20:
                    rssi_history = rssi_history[-20:]
                
                self.victims[victim_id]['RSSI_HISTORY'] = rssi_history
                
            else:
                # ADD new victim
                self.victims[victim_id] = {
                    'ID': victim_id,
                    'LAT': packet['LAT'],
                    'LON': packet['LON'],
                    'TIME': packet['TIME'],
                    'RSSI': packet.get('RSSI', -999),
                    'STATUS': config.STATUS_STRANDED,
                    'FIRST_DETECTED': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'LAST_UPDATE': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'RESCUED_TIME': None,
                    'RESCUED_BY': None,
                    'UPDATE_COUNT': 1,
                    'RSSI_HISTORY': [packet.get('RSSI', -999)],
                    'NOTES': ''
                }
            
            # Auto-save periodically
            self._auto_save()
            
            return True
            
        except Exception as e:
            print(f"Error adding/updating victim: {e}")
            return False
    
    def mark_enroute(self, victim_id: int) -> bool:
        """
        Mark victim as EN_ROUTE (rescue team dispatched)
        
        Args:
            victim_id: Victim ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if victim_id not in self.victims:
            print(f"Victim {victim_id} not found")
            return False
        
        try:
            self.victims[victim_id]['STATUS'] = config.STATUS_EN_ROUTE
            self.victims[victim_id]['ENROUTE_TIME'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self._auto_save()
            return True
            
        except Exception as e:
            print(f"Error marking victim as en-route: {e}")
            return False
    
    def mark_rescued(
        self,
        victim_id: int,
        operator_name: str,
        notes: str = ""
    ) -> bool:
        """
        Mark victim as RESCUED
        
        Args:
            victim_id: Victim ID
            operator_name: Name of operator marking rescue
            notes: Optional rescue notes
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if victim_id not in self.victims:
            print(f"Victim {victim_id} not found")
            return False
        
        try:
            self.victims[victim_id]['STATUS'] = config.STATUS_RESCUED
            self.victims[victim_id]['RESCUED_TIME'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.victims[victim_id]['RESCUED_BY'] = operator_name
            self.victims[victim_id]['NOTES'] = notes
            
            # Log rescue event
            self._log_rescue(victim_id, operator_name, notes)
            
            self._auto_save()
            return True
            
        except Exception as e:
            print(f"Error marking victim as rescued: {e}")
            return False
    
    def get_victim(self, victim_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific victim data
        
        Args:
            victim_id: Victim ID
            
        Returns:
            Dict with victim data or None
        """
        return self.victims.get(victim_id)
    
    def get_all_victims(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all victims
        
        Returns:
            Dict of all victims
        """
        return self.victims.copy()
    
    def get_victims_by_status(self, status: str) -> Dict[int, Dict[str, Any]]:
        """
        Get victims filtered by status
        
        Args:
            status: Status to filter by (STRANDED/EN_ROUTE/RESCUED)
            
        Returns:
            Dict of filtered victims
        """
        return {
            vid: data for vid, data in self.victims.items()
            if data['STATUS'] == status
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics across all victims
        
        Returns:
            Dict with statistics
        """
        
        total = len(self.victims)
        
        stranded = len([v for v in self.victims.values() if v['STATUS'] == config.STATUS_STRANDED])
        enroute = len([v for v in self.victims.values() if v['STATUS'] == config.STATUS_EN_ROUTE])
        rescued = len([v for v in self.victims.values() if v['STATUS'] == config.STATUS_RESCUED])
        
        return {
            'total': total,
            'stranded': stranded,
            'enroute': enroute,
            'rescued': rescued,
            'stranded_pct': (stranded / total * 100) if total > 0 else 0,
            'enroute_pct': (enroute / total * 100) if total > 0 else 0,
            'rescued_pct': (rescued / total * 100) if total > 0 else 0
        }
    
    def get_priority_victims(self, rssi_strong_threshold=None, rssi_weak_threshold=None, 
                            time_critical_threshold=None) -> Dict[int, Dict[str, Any]]:
        """
        Get high priority victims
        
        Args:
            rssi_strong_threshold: Strong signal threshold (optional)
            rssi_weak_threshold: Weak signal threshold (optional)
            time_critical_threshold: Critical time threshold in minutes (optional)
        
        Returns:
            Dict of high priority victims
        """
        from utils.helpers import calculate_priority
        
        priority_victims = {}
        
        for vid, data in self.victims.items():
            if data['STATUS'] == config.STATUS_STRANDED:
                priority, _ = calculate_priority(
                    data,
                    rssi_strong_threshold=rssi_strong_threshold,
                    rssi_weak_threshold=rssi_weak_threshold,
                    time_critical_threshold=time_critical_threshold
                )
                if priority == "HIGH":
                    priority_victims[vid] = data
        
        return priority_victims
    
    def get_geographic_clusters(self, sector_size: float = None) -> Dict[str, List[int]]:
        """
        Group victims by geographic sectors
        
        Args:
            sector_size: Size of grid sectors in decimal degrees
            
        Returns:
            Dict mapping sector IDs to list of victim IDs
        """
        
        if sector_size is None:
            sector_size = config.SECTOR_SIZE_LAT
        
        clusters = defaultdict(list)
        
        for vid, data in self.victims.items():
            # Calculate sector coordinates
            sector_lat = int(data['LAT'] / sector_size)
            sector_lon = int(data['LON'] / sector_size)
            sector_id = f"{sector_lat},{sector_lon}"
            
            clusters[sector_id].append(vid)
        
        return dict(clusters)
    
    def get_signal_distribution(self) -> Dict[str, int]:
        """
        Get distribution of signal strengths
        
        Returns:
            Dict with counts for each signal category
        """
        
        strong = 0
        medium = 0
        weak = 0
        
        for victim in self.victims.values():
            rssi = victim.get('RSSI', -999)
            
            if rssi > config.RSSI_STRONG_THRESHOLD:
                strong += 1
            elif rssi >= config.RSSI_WEAK_THRESHOLD:
                medium += 1
            else:
                weak += 1
        
        return {
            'strong': strong,
            'medium': medium,
            'weak': weak
        }
    
    def delete_victim(self, victim_id: int) -> bool:
        """
        Delete a victim record (use with caution)
        
        Args:
            victim_id: Victim ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        
        if victim_id in self.victims:
            del self.victims[victim_id]
            self._auto_save()
            return True
        
        return False
    
    def reset_all_data(self) -> bool:
        """
        Reset all victim data (use with extreme caution)
        
        Returns:
            bool: True if successful
        """
        
        try:
            self.victims = {}
            self._auto_save()
            return True
        except Exception as e:
            print(f"Error resetting data: {e}")
            return False
    
    def save_to_file(self, filepath: str = None) -> bool:
        """
        Save victim data to JSON file
        
        Args:
            filepath: Path to save file (uses default if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if filepath is None:
            filepath = config.BACKUP_FILE_PATH
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save data
            with open(filepath, 'w') as f:
                json.dump(self.victims, f, indent=2)
            
            self.last_backup_time = datetime.now()
            return True
            
        except Exception as e:
            print(f"Error saving to file: {e}")
            return False
    
    def load_from_file(self, filepath: str = None) -> bool:
        """
        Load victim data from JSON file
        
        Args:
            filepath: Path to load file (uses default if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        if filepath is None:
            filepath = config.BACKUP_FILE_PATH
        
        if not os.path.exists(filepath):
            print(f"Backup file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Convert string keys back to integers
            self.victims = {int(k): v for k, v in data.items()}
            
            print(f"Loaded {len(self.victims)} victims from backup")
            return True
            
        except Exception as e:
            print(f"Error loading from file: {e}")
            return False
    
    def export_to_csv(self, filepath: str = None, status_filter: str = None) -> bool:
        """
        Export victim data to CSV file
        
        Args:
            filepath: Path to CSV file
            status_filter: Optional status filter
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        try:
            import pandas as pd
            
            # Filter victims if needed
            if status_filter:
                victims = self.get_victims_by_status(status_filter)
            else:
                victims = self.victims
            
            if not victims:
                print("No victims to export")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(list(victims.values()))
            
            # Select columns
            columns = [col for col in config.EXPORT_COLUMNS if col in df.columns]
            df = df[columns]
            
            # Generate filename if not provided
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                status_str = status_filter.lower() if status_filter else "all"
                filename = config.EXPORT_FILENAME_FORMAT.format(
                    type=status_str,
                    timestamp=timestamp
                )
                filepath = os.path.join('data', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Export to CSV
            df.to_csv(filepath, index=False)
            
            print(f"Exported {len(df)} victims to {filepath}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def _auto_save(self):
        """Auto-save data periodically"""
        
        current_time = datetime.now()
        
        # Check if enough time has passed since last backup
        if self.last_backup_time is None:
            should_save = True
        else:
            time_since_backup = (current_time - self.last_backup_time).total_seconds()
            should_save = time_since_backup >= config.BACKUP_INTERVAL_SECONDS
        
        if should_save:
            self.save_to_file()
    
    def _log_rescue(self, victim_id: int, operator_name: str, notes: str):
        """
        Log rescue event to CSV file
        
        Args:
            victim_id: Victim ID
            operator_name: Operator who performed rescue
            notes: Rescue notes
        """
        
        try:
            import pandas as pd
            
            victim = self.victims[victim_id]
            
            # Prepare log entry
            log_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'victim_id': victim_id,
                'operator': operator_name,
                'location_lat': victim['LAT'],
                'location_lon': victim['LON'],
                'first_detected': victim['FIRST_DETECTED'],
                'last_update': victim['LAST_UPDATE'],
                'rescued_time': victim['RESCUED_TIME'],
                'total_updates': victim['UPDATE_COUNT'],
                'final_rssi': victim['RSSI'],
                'notes': notes
            }
            
            # Append to rescue log
            log_path = config.RESCUE_LOG_PATH
            
            # Check if file exists
            if os.path.exists(log_path):
                df = pd.read_csv(log_path)
                df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
            else:
                df = pd.DataFrame([log_entry])
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            # Save log
            df.to_csv(log_path, index=False)
            
        except Exception as e:
            print(f"Error logging rescue: {e}")
    
    def get_victim_count(self) -> int:
        """Get total number of victims"""
        return len(self.victims)
    
    def get_active_count(self) -> int:
        """Get number of active (stranded + en-route) victims"""
        return len([
            v for v in self.victims.values()
            if v['STATUS'] in [config.STATUS_STRANDED, config.STATUS_EN_ROUTE]
        ])