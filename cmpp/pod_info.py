"""
Kubernetes pod information utilities for CM PurplePill

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

import logging
import os
import re
from typing import Dict, Optional


logger = logging.getLogger("cmpp")


def get_container_id(pid: int) -> Optional[str]:
    """
    Extract container ID from process cgroup file
    
    Args:
        pid: Process ID
        
    Returns:
        Container ID or None if not found
    """
    cgroup_file = f"/proc/{pid}/cgroup"
    
    if not os.path.exists(cgroup_file):
        return None
    
    try:
        with open(cgroup_file, 'r') as f:
            cgroup_content = f.read()
        
        # Try containerd format with cri prefix (K8s 1.23+)
        match = re.search(r'cri-containerd-([a-f0-9]{64})', cgroup_content)
        if match:
            return match.group(1)
        
        # Try standard containerd format
        match = re.search(r'containerd://([a-f0-9]{64})', cgroup_content)
        if match:
            return match.group(1)
        
        # Try docker format
        match = re.search(r'docker-([a-f0-9]{64})', cgroup_content)
        if match:
            return match.group(1)
        
        # Try CRI-O format
        match = re.search(r'crio-([a-f0-9]{64})', cgroup_content)
        if match:
            return match.group(1)
        
        # Try direct cgroup path extraction for newer k8s
        if 'kubepods' in cgroup_content:
            match = re.search(r'([a-f0-9]{64})\.scope', cgroup_content)
            if match:
                return match.group(1)
        
        return None
    except Exception as e:
        logger.debug(f"Error reading cgroup file for PID {pid}: {e}")
        return None


def get_pod_info(pid: int) -> str:
    """
    Extract Kubernetes pod information from process environment
    
    Args:
        pid: Process ID
        
    Returns:
        Prometheus labels string with pod information, or empty string if not found
    """
    environ_file = f"/proc/{pid}/environ"
    
    if not os.path.exists(environ_file):
        return ""
    
    pod_name = ""
    namespace = ""
    stack_id = ""
    
    try:
        with open(environ_file, 'rb') as f:
            env_vars = f.read().split(b'\0')
        
        # Convert to string and split by '='
        env_dict = {}
        for var in env_vars:
            if var:
                try:
                    key, value = var.decode('utf-8', errors='ignore').split('=', 1)
                    env_dict[key] = value
                except ValueError:
                    continue
        
        # Extract pod name (HOSTNAME variable in Kubernetes)
        pod_name = env_dict.get('HOSTNAME', '')
        
        # Extract namespace (try various methods)
        namespace = env_dict.get('KUBERNETES_NAMESPACE', env_dict.get('POD_NAMESPACE', ''))
        
        # If namespace not found, try to infer from service account path
        if not namespace and 'KUBERNETES_SERVICE_HOST' in env_dict:
            # Try to get namespace from various kubernetes env vars
            for key in env_dict:
                if '_SERVICE_' in key:
                    namespace_candidate = key.split('_')[0].lower()
                    if namespace_candidate and namespace_candidate != 'kubernetes':
                        namespace = namespace_candidate
                        break
        
        # Try to get the stackId or app label which often holds the service ID
        stack_id_keys = ['SERVICE_NAME', 'APP_NAME', 'STACK_ID']
        for key in stack_id_keys:
            if key in env_dict:
                stack_id = env_dict[key]
                break
        
        # If no stack_id found but there's a pod name, use the first part before dash
        if not stack_id and pod_name:
            stack_id = pod_name.split('-')[0]
        
        # Build Prometheus labels
        if pod_name and namespace:
            return f'pod="{pod_name}",namespace="{namespace}",stack_id="{stack_id}"'
        elif pod_name:
            return f'pod="{pod_name}",stack_id="{stack_id}"'
            
        return ""
    except Exception as e:
        logger.debug(f"Error reading environment for PID {pid}: {e}")
        return ""
