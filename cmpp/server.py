"""
HTTP server for CM PurplePill

Copyright 2025 ConfidentialMind Oy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import http.server
import logging
import socketserver
import threading
from typing import Any, Dict, Optional, Union

# ThreadingMixIn allows handling requests concurrently
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """HTTP server that handles requests in separate threads"""
    daemon_threads = True


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for Prometheus metrics"""
    
    # This will be set by the MetricsServer class
    collector = None
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/metrics' or self.path == '/':
            self._serve_metrics()
        elif self.path == '/health':
            self._serve_health()
        else:
            self.send_error(404, "Not Found")
    
    def _serve_metrics(self):
        """Serve metrics in Prometheus format"""
        if not self.collector:
            self.send_error(500, "Metrics collector not configured")
            return
        
        # Get current metrics
        metrics = self.collector.get_current_metrics()
        
        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(metrics)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(metrics.encode('utf-8'))
    
    def _serve_health(self):
        """Serve health check response"""
        health_status = "OK"
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(health_status)))
        self.end_headers()
        self.wfile.write(health_status.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger = logging.getLogger("cmpp")
        logger.debug(f"{self.client_address[0]} - {format % args}")


class MetricsServer:
    """HTTP server for exposing Prometheus metrics"""
    
    def __init__(self, collector, host: str = '0.0.0.0', port: int = 9531):
        """
        Initialize the metrics server
        
        Args:
            collector: MetricsCollector instance
            host: Host to bind the server to
            port: Port to listen on
        """
        self.logger = logging.getLogger("cmpp")
        self.host = host
        self.port = port
        self.collector = collector
        self.server = None
        self.thread = None
        self.running = False
    
    def start(self) -> bool:
        """
        Start the HTTP server in a background thread
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning(f"HTTP server already running on {self.host}:{self.port}")
            return False
        
        try:
            # Set collector instance to be used by request handler
            MetricsHandler.collector = self.collector
            
            # Create server instance
            self.server = ThreadingHTTPServer((self.host, self.port), MetricsHandler)
            
            # Start server in a background thread
            self.thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True,
                name="CMPurplePillServer"
            )
            self.thread.start()
            
            self.running = True
            self.logger.info(f"HTTP server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start HTTP server: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the HTTP server"""
        if self.running and self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5.0)
            self.running = False
            self.logger.info("HTTP server stopped")
