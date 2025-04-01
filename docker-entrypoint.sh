#!/bin/bash

# Copyright 2025 ConfidentialMind Oy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Check for nvidia-smi
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not found. This container requires NVIDIA drivers to be installed on the host."
    echo "Please ensure the container is run with the NVIDIA Container Toolkit enabled."
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p /var/log/cm-purplepill

# Execute the provided command
exec "$@"