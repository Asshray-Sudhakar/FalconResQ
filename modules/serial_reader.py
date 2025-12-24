"""
Serial Reader Module
Handles serial port communication with ground station hardware
Reads and parses JSON packets from COM port
"""

import serial
import serial.tools.list_ports
import json
import threading
import time
from typing import Callable, Optional, Dict, Any
from datetime import datetime

import config


class SerialReader:
    """
    Manages serial port communication for receiving victim data packets
    
    Features:
    - Background thread for continuous reading
    - JSON packet parsing
    - Error handling and reconnection
    - Callback pattern for data processing
    """
    
    def __init__(self):
        """Initialize the serial reader"""
        self.serial_port: Optional[serial.Serial] = None
        self.is_reading: bool = False
        self.read_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_packet_received: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Statistics
        self.packets_received: int = 0
        self.errors_encountered: int = 0
        self.last_packet_time: Optional[datetime] = None
        
        # Configuration
        self.port_name: str = config.DEFAULT_SERIAL_PORT
        self.baud_rate: int = config.DEFAULT_BAUD_RATE
        self.timeout: int = config.SERIAL_TIMEOUT
    
    def start_reading(
        self,
        port: str,
        baudrate: int,
        on_packet_received: Callable[[Dict[str, Any]], None],
        on_error: Optional[Callable[[], None]] = None
    ) -> bool:
        """
        Start reading from serial port in background thread
        
        Args:
            port: Serial port name (e.g., 'COM20')
            baudrate: Baud rate (e.g., 115200)
            on_packet_received: Callback function for valid packets
            on_error: Optional callback for errors
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        
        if self.is_reading:
            print("Serial reader already running")
            return False
        
        try:
            # Open serial port
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=self.timeout
            )
            
            # Store configuration
            self.port_name = port
            self.baud_rate = baudrate
            self.on_packet_received = on_packet_received
            self.on_error = on_error
            
            # Start reading thread
            self.is_reading = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            print(f"Serial reader started on {port} at {baudrate} baud")
            return True
            
        except serial.SerialException as e:
            print(f"Failed to open serial port: {e}")
            self.is_reading = False
            return False
        except Exception as e:
            print(f"Unexpected error starting serial reader: {e}")
            self.is_reading = False
            return False
    
    def stop_reading(self):
        """Stop reading from serial port and close connection"""
        
        print("Stopping serial reader...")
        self.is_reading = False
        
        # Wait for thread to finish
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        
        # Close serial port
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("Serial port closed")
        
        self.serial_port = None
        self.read_thread = None
    
    def _read_loop(self):
        """
        Main reading loop (runs in background thread)
        Continuously reads and processes data from serial port
        """
        
        while self.is_reading:
            try:
                if self.serial_port and self.serial_port.is_open:
                    # Check if data is available
                    if self.serial_port.in_waiting > 0:
                        # Read line from serial port
                        line = self.serial_port.readline()
                        
                        # Decode bytes to string
                        try:
                            line_str = line.decode('utf-8').strip()
                        except UnicodeDecodeError:
                            # Try alternate encoding
                            line_str = line.decode('latin-1').strip()
                        
                        # Skip empty lines
                        if not line_str:
                            continue
                        
                        # Parse and process packet
                        packet = self._parse_packet(line_str)
                        
                        if packet:
                            # Valid packet received
                            self.packets_received += 1
                            self.last_packet_time = datetime.now()
                            
                            # Call callback with packet data
                            if self.on_packet_received:
                                self.on_packet_received(packet)
                        # Note: Don't call on_error for parsing failures - those are normal
                        # (debug messages, partial packets, etc.)
                        # Only call on_error for actual serial/communication errors
                    else:
                        # No data available, small sleep to prevent CPU spinning
                        time.sleep(0.01)
                else:
                    # Serial port not open
                    print("Serial port not open, stopping reader")
                    self.is_reading = False

            except serial.SerialException as e:
                print(f"Serial error: {e}")
                self.errors_encountered += 1
                if self.on_error:
                    self.on_error()
                
                # Try to reconnect after error
                time.sleep(1)
                
            except Exception as e:
                print(f"Unexpected error in read loop: {e}")
                self.errors_encountered += 1
                if self.on_error:
                    self.on_error()
                time.sleep(0.1)
    
    def _parse_packet(self, data_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON packet from string
        
        Expected format from Ground Station:
        {"ID": 1, "LAT": 13.022456, "LON": 77.587123, "TIME": "15:42", "RSSI": -65}
        
        Args:
            data_string: Raw string data from serial port
            
        Returns:
            Dict with packet data if valid, None otherwise
        """
        
        try:
            # Clean the data string (remove any whitespace)
            data_string = data_string.strip()
            
            # Skip non-JSON lines (status messages from Arduino)
            if not data_string.startswith('{'):
                return None
            
            # Parse JSON
            packet = json.loads(data_string)
            
            # Validate required fields
            required_fields = ['ID', 'LAT', 'LON', 'TIME']
            
            if not all(field in packet for field in required_fields):
                print(f"Packet missing required fields: {packet}")
                return None
            
            # Validate data types
            try:
                packet['ID'] = int(packet['ID'])
                packet['LAT'] = float(packet['LAT'])
                packet['LON'] = float(packet['LON'])
                packet['TIME'] = str(packet['TIME'])
                
                # RSSI is optional but expected from ground station
                if 'RSSI' in packet:
                    packet['RSSI'] = int(packet['RSSI'])
                else:
                    packet['RSSI'] = -999  # Default value for missing RSSI
                    
            except (ValueError, TypeError) as e:
                print(f"Invalid data types in packet: {e}")
                return None
            
            # Basic validation
            if not self._validate_packet(packet):
                print(f"Packet failed validation: {packet}")
                return None
            
            return packet
            
        except json.JSONDecodeError as e:
            # Not a JSON line, ignore (Arduino debug messages)
            return None
        except Exception as e:
            print(f"Unexpected error parsing packet: {e}")
            return None
    
    def _validate_packet(self, packet: Dict[str, Any]) -> bool:
        """
        Validate packet data
        
        Args:
            packet: Parsed packet dictionary
            
        Returns:
            bool: True if valid, False otherwise
        """
        
        # Validate victim ID
        if packet['ID'] < config.MIN_VICTIM_ID or packet['ID'] > config.MAX_VICTIM_ID:
            return False
        
        # Validate coordinates
        lat, lon = packet['LAT'], packet['LON']
        
        if not (config.VALID_LAT_RANGE[0] <= lat <= config.VALID_LAT_RANGE[1]):
            return False
        
        if not (config.VALID_LON_RANGE[0] <= lon <= config.VALID_LON_RANGE[1]):
            return False
        
        # Accept any RSSI value (no validation) - live data can have any signal strength
        # This allows the app to display points regardless of signal quality
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get reader statistics
        
        Returns:
            Dict with statistics
        """
        return {
            'packets_received': self.packets_received,
            'errors_encountered': self.errors_encountered,
            'last_packet_time': self.last_packet_time,
            'is_reading': self.is_reading,
            'port': self.port_name,
            'baudrate': self.baud_rate
        }
    
    def is_connected(self) -> bool:
        """Check if serial port is connected and reading"""
        return self.is_reading and self.serial_port and self.serial_port.is_open
    
    @staticmethod
    def list_available_ports() -> list:
        """
        List all available serial ports
        
        Returns:
            List of port names
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    @staticmethod
    def get_port_info(port_name: str) -> Optional[Dict[str, str]]:
        """
        Get detailed information about a specific port
        
        Args:
            port_name: Port name (e.g., 'COM20')
            
        Returns:
            Dict with port information or None
        """
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            if port.device == port_name:
                return {
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid,
                    'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else 'Unknown'
                }
        
        return None
    
    def __del__(self):
        """Destructor - ensure serial port is closed"""
        if self.is_reading:
            self.stop_reading()