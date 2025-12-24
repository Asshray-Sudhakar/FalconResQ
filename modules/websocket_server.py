"""
WebSocket Server for Real-Time Data Streaming
Broadcasts victim data to all connected clients in real-time
Replaces polling with push-based updates
"""

import asyncio
import json
import threading
from typing import Set, Dict, Any, Callable
from datetime import datetime

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class WebSocketServer:
    """
    WebSocket server for broadcasting real-time victim data
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize WebSocket server
        
        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.server = None
        self.loop = None
        self.thread = None
        self.running = False
        
        if not WEBSOCKETS_AVAILABLE:
            print("[!] WebSockets not installed. Install with: pip install websockets")
    
    def start(self):
        """Start the WebSocket server in background thread"""
        if not WEBSOCKETS_AVAILABLE:
            print("[!] WebSockets library not available")
            return False
        
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        self.running = True
        print(f"✓ WebSocket server starting on ws://{self.host}:{self.port}")
        return True
    
    def stop(self):
        """Stop the WebSocket server"""
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        print("✓ WebSocket server stopped")
    
    def _run_server(self):
        """Run the async WebSocket server"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._start_server())
        except Exception as e:
            print(f"[!] WebSocket server error: {e}")
        finally:
            self.loop.close()
    
    async def _start_server(self):
        """Start listening for WebSocket connections"""
        async with websockets.serve(self._handle_connection, self.host, self.port):
            print(f"✓ WebSocket server listening on ws://{self.host}:{self.port}")
            # Keep server running
            while self.running:
                await asyncio.sleep(0.1)
    
    async def _handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        self.clients.add(websocket)
        print(f"✓ Client connected. Total: {len(self.clients)}")
        
        try:
            async for message in websocket:
                # Receive messages from client if needed
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"✓ Client disconnected. Total: {len(self.clients)}")
    
    def broadcast(self, data: Dict[str, Any]):
        """
        Broadcast packet to all connected clients
        
        Args:
            data: Packet data to broadcast
        """
        if not self.running or not self.clients:
            return
        
        # Prepare message
        message = json.dumps({
            'type': 'victim_update',
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to all connected clients
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast_to_clients(message),
                self.loop
            )
    
    async def _broadcast_to_clients(self, message: str):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )


# Global WebSocket server instance
ws_server = None


def get_websocket_server() -> WebSocketServer:
    """Get or create global WebSocket server"""
    global ws_server
    if ws_server is None:
        ws_server = WebSocketServer()
    return ws_server


def start_websocket_server() -> bool:
    """Start the global WebSocket server"""
    server = get_websocket_server()
    return server.start()


def stop_websocket_server():
    """Stop the global WebSocket server"""
    global ws_server
    if ws_server:
        ws_server.stop()


def broadcast_packet(packet: Dict[str, Any]):
    """Broadcast packet to all WebSocket clients"""
    server = get_websocket_server()
    if server.running:
        server.broadcast(packet)
