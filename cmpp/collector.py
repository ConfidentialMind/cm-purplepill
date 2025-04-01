"""
GPU Metrics Collector for CM PurplePill

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

import csv
import io
import logging
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple, Any

from cmpp.pod_info import get_pod_info
from cmpp.utils import execute_command, write_atomic, is_numeric


class MetricsCollector:
    """Collect GPU metrics and format them for Prometheus"""
    
    def __init__(self, 
                 metrics_file: str = "/tmp/cmpp_metrics.prom",
                 interval: int = 15,
                 hostname_override: str = None):
        """
        Initialize the metrics collector
        
        Args:
            metrics_file: Path to write metrics in Prometheus format
            interval: Collection interval in seconds
            hostname_override: Custom hostname to use in metrics (defaults to system hostname)
        """
        self.logger = logging.getLogger("cmpp")
        self.metrics_file = metrics_file
        self.interval = interval
        self.hostname = hostname_override if hostname_override else socket.gethostname()
        self.running = False
        self.thread = None
        self.metrics_lock = threading.Lock()
        self.current_metrics = ""
    
    def start(self) -> bool:
        """
        Start the metrics collection thread
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Metrics collector is already running")
            return False
            
        self.running = True
        self.thread = threading.Thread(
            target=self._collection_loop,
            daemon=True,
            name="CMPurplePillCollector"
        )
        self.thread.start()
        self.logger.info(f"Metrics collector started with interval {self.interval}s")
        return True
    
    def stop(self) -> None:
        """Stop the metrics collection thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
            self.logger.info("Metrics collector stopped")
    
    def get_current_metrics(self) -> str:
        """
        Get the current metrics
        
        Returns:
            Current metrics in Prometheus format
        """
        with self.metrics_lock:
            return self.current_metrics
    
    def _collection_loop(self) -> None:
        """Main metrics collection loop"""
        while self.running:
            try:
                # Collect and format metrics
                metrics = self._collect_and_format_metrics()
                
                # Update the current metrics with thread safety
                with self.metrics_lock:
                    self.current_metrics = metrics
                
                # Write to file
                write_atomic(self.metrics_file, metrics)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {str(e)}")
            
            # Wait for next collection cycle
            time_to_sleep = self.interval
            while time_to_sleep > 0 and self.running:
                time.sleep(min(1, time_to_sleep))
                time_to_sleep -= 1
    
    def _collect_and_format_metrics(self) -> str:
        """
        Collect metrics from nvidia-smi and format them for Prometheus
        
        Returns:
            Metrics in Prometheus format
        """
        metrics = []
        gpu_data = []
        
        # Get GPU information
        gpu_info = self._get_gpu_info()
        
        # Format total memory metrics
        metrics.append("# HELP CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB Total GPU memory in MiB.")
        metrics.append("# TYPE CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB gauge")
        
        for gpu in gpu_info:
            # Store for later use
            gpu_data.append(gpu)
            
            # Add total memory metrics
            labels = f'gpu="{gpu["index"]}",UUID="{gpu["uuid"]}",modelName="{gpu["name"]}",Hostname="{self.hostname}"'
            metrics.append(f'CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB{{{labels}}} {gpu["memory_total"]}')
        
        # Format used memory metrics
        metrics.append("# HELP CM_PURPLEPILL_GPU_MEMORY_USED_TOTAL_MIB Total used GPU memory in MiB.")
        metrics.append("# TYPE CM_PURPLEPILL_GPU_MEMORY_USED_TOTAL_MIB gauge")
        
        for gpu in gpu_data:
            labels = f'gpu="{gpu["index"]}",UUID="{gpu["uuid"]}",modelName="{gpu["name"]}",Hostname="{self.hostname}"'
            metrics.append(f'CM_PURPLEPILL_GPU_MEMORY_USED_TOTAL_MIB{{{labels}}} {gpu["memory_used"]}')
        
        # Format free memory metrics
        metrics.append("# HELP CM_PURPLEPILL_GPU_MEMORY_FREE_MIB Free GPU memory in MiB.")
        metrics.append("# TYPE CM_PURPLEPILL_GPU_MEMORY_FREE_MIB gauge")
        
        for gpu in gpu_data:
            labels = f'gpu="{gpu["index"]}",UUID="{gpu["uuid"]}",modelName="{gpu["name"]}",Hostname="{self.hostname}"'
            metrics.append(f'CM_PURPLEPILL_GPU_MEMORY_FREE_MIB{{{labels}}} {gpu["memory_free"]}')
        
        # Format utilization metrics
        metrics.append("# HELP CM_PURPLEPILL_GPU_UTILIZATION GPU utilization percentage.")
        metrics.append("# TYPE CM_PURPLEPILL_GPU_UTILIZATION gauge")
        
        for gpu in gpu_data:
            labels = f'gpu="{gpu["index"]}",UUID="{gpu["uuid"]}",modelName="{gpu["name"]}",Hostname="{self.hostname}"'
            metrics.append(f'CM_PURPLEPILL_GPU_UTILIZATION{{{labels}}} {gpu["utilization"]}')
        
        # Get process information and format pod metrics
        metrics.append("# HELP CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB Pod GPU memory usage in MiB.")
        metrics.append("# TYPE CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB gauge")
        
        processes = self._get_gpu_processes()
        for process in processes:
            # Find GPU data for this UUID
            gpu_idx = None
            for gpu in gpu_data:
                if gpu["uuid"] == process["gpu_uuid"]:
                    gpu_idx = gpu["index"]
                    break
            
            if gpu_idx is None:
                continue
                
            # Get pod information
            pod_labels = get_pod_info(process["pid"])
            
            if pod_labels:
                # Add process metrics with pod information
                device_name = f"nvidia{gpu_idx}"
                labels = f'gpu="{gpu_idx}",UUID="{process["gpu_uuid"]}",Hostname="{self.hostname}",device="{device_name}",{pod_labels}'
                metrics.append(f'CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB{{{labels}}} {process["memory_used"]}')
        
        return "\n".join(metrics)
    
    def _get_gpu_info(self) -> List[Dict[str, Any]]:
        """
        Get GPU information from nvidia-smi
        
        Returns:
            List of dictionaries with GPU information
        """
        success, output = execute_command([
            "nvidia-smi", 
            "--query-gpu=index,gpu_uuid,name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader"
        ])
        
        if not success:
            self.logger.error(f"Failed to get GPU information: {output}")
            return []
        
        gpus = []
        
        for row in csv.reader(io.StringIO(output)):
            if len(row) < 7:
                continue
                
            # Clean up values
            idx = row[0].strip()
            uuid = row[1].strip()
            name = row[2].strip()
            total_mem = row[3].strip().replace(' MiB', '')
            used_mem = row[4].strip().replace(' MiB', '')
            free_mem = row[5].strip().replace(' MiB', '')
            util = row[6].strip().replace(' %', '')
            
            if not is_numeric(total_mem) or not is_numeric(used_mem) or \
               not is_numeric(free_mem) or not is_numeric(util):
                self.logger.warning(f"Non-numeric values in GPU data: {row}")
                continue
            
            # Add GPU information
            gpus.append({
                "index": idx,
                "uuid": uuid,
                "name": name,
                "memory_total": total_mem,
                "memory_used": used_mem,
                "memory_free": free_mem,
                "utilization": util
            })
        
        return gpus
    
    def _get_gpu_processes(self) -> List[Dict[str, Any]]:
        """
        Get GPU process information from nvidia-smi
        
        Returns:
            List of dictionaries with process information
        """
        success, output = execute_command([
            "nvidia-smi",
            "--query-compute-apps=pid,gpu_uuid,used_memory",
            "--format=csv,noheader"
        ])
        
        if not success:
            self.logger.error(f"Failed to get GPU processes: {output}")
            return []
        
        processes = []
        
        for row in csv.reader(io.StringIO(output)):
            if len(row) < 3:
                continue
                
            # Clean up values
            pid = row[0].strip()
            uuid = row[1].strip()
            memory = row[2].strip().replace(' MiB', '')
            
            if not pid.isdigit() or not is_numeric(memory):
                self.logger.warning(f"Invalid process data: {row}")
                continue
            
            # Add process information
            processes.append({
                "pid": int(pid),
                "gpu_uuid": uuid,
                "memory_used": memory
            })
        
        return processes
