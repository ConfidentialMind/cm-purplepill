#!/usr/bin/env python3
"""
ConfidentialMind Container GPU Monitor (CM PurplePill)
Main executable script

Usage:
    cmpp [options]

Options:
    --port PORT             Port to expose HTTP metrics server [default: 9531]
    --interval SECONDS      Interval between metric collections [default: 15]
    --log-file FILE         Log file path [default: /var/log/cm-purplepill.log]
    --metrics-file FILE     File to store metrics [default: /tmp/cmpp_metrics.prom]
    --hostname-override HOSTNAME     Override the system hostname used in metrics labels
    --help                  Show this help message and exit
    --version               Show version and exit
"""

import argparse
import logging
import os
import signal
import sys
import time
from typing import Any, Dict, Optional

from cmpp import __version__, __logo__
from cmpp.collector import MetricsCollector
from cmpp.server import MetricsServer
from cmpp.utils import setup_logging, check_nvidia_tools


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="ConfidentialMind Container GPU Monitor (CM PurplePill)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9531,
        help="Port to expose HTTP metrics server [default: 9531]"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Interval between metric collections in seconds [default: 15]"
    )
    parser.add_argument(
        "--log-file",
        default="/var/log/cm-purplepill.log",
        help="Log file path [default: /var/log/cm-purplepill.log]"
    )
    parser.add_argument(
        "--metrics-file",
        default="/tmp/cmpp_metrics.prom",
        help="File to store metrics [default: /tmp/cmpp_metrics.prom]"
    )
    parser.add_argument(
        "--hostname-override",
        default=None,
        help="Override the system hostname used in metrics labels"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"CM PurplePill {__version__}"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.log_file, level=logging.INFO)
    logger.info(f"ConfidentialMind PurplePill starting")
    
    # Check for NVIDIA tools
    if not check_nvidia_tools():
        logger.error("NVIDIA tools (nvidia-smi) not found, exiting")
        sys.exit(1)
    
    # Create PID file for systemd management
    pid_file = "/tmp/cmpp-exporter.pid"
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Initialize components
    collector = MetricsCollector(
        metrics_file=args.metrics_file,
        interval=args.interval,
        hostname_override=args.hostname_override
    )
    
    server = MetricsServer(
        collector=collector,
        port=args.port
    )
    
    # Setup signal handling for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received, stopping...")
        server.stop()
        collector.stop()
        try:
            os.unlink(pid_file)
        except:
            pass
        logger.info("Shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start collector
        if not collector.start():
            logger.error("Failed to start metrics collector")
            sys.exit(1)
        
        # Start HTTP server
        if not server.start():
            logger.error("Failed to start HTTP server")
            collector.stop()
            sys.exit(1)
        
    
        # Display logo to console
        print(f"\n{__logo__}", file=sys.stderr)
        
        logger.info(f"CM PurplePill v{__version__} initialised successfully; listening on 0.0.0.0:{args.port}; refresh interval: {args.interval}s")
        
        # Main loop - keep the process alive and monitor components
        while True:
            # Check if collector thread is alive
            if collector.thread and not collector.thread.is_alive():
                logger.warning("Metrics collector died, restarting...")
                collector.start()
            
            # Check if server thread is alive
            if server.thread and not server.thread.is_alive():
                logger.warning("HTTP server died, restarting...")
                server.start()
            
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        server.stop()
        collector.stop()
        try:
            os.unlink(pid_file)
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()