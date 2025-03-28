#!/bin/bash
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