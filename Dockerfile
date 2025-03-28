# Description: Dockerfile for building the CM PurplePill container image

# Use CUDA base image based on Red Hat UBI
# Check https://catalog.ngc.nvidia.com/orgs/nvidia/containers/cuda/tags for the latest version
FROM nvcr.io/nvidia/cuda:12.8.1-base-ubi9

# Install Python - use the latest available in UBI 9 repositories
RUN dnf install -y \
    python3 \
    python3-pip \
    && dnf clean all

# Install CM PurplePill
WORKDIR /app

# Copy CM PurplePill files
COPY cmpp/ /app/cmpp/
COPY setup.py MANIFEST.in README.md requirements.txt /app/

# Install the package
RUN pip3 install --no-cache-dir .

# Create runtime directories
RUN mkdir -p /var/log/cm-purplepill

# Set up entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment variables for configuration
ENV CM_PURPLEPILL_PORT=9531 \
    CM_PURPLEPILL_INTERVAL=15 \
    CM_PURPLEPILL_HOSTNAME_OVERRIDE=""

# Default port for Prometheus metrics
EXPOSE ${CM_PURPLEPILL_PORT}

# Default command
ENTRYPOINT ["docker-entrypoint.sh"]
CMD sh -c 'cmpp \
    --port=${CM_PURPLEPILL_PORT} \
    --interval=${CM_PURPLEPILL_INTERVAL} \
    $([ -n "${CM_PURPLEPILL_HOSTNAME_OVERRIDE}" ] && echo "--hostname-override=${CM_PURPLEPILL_HOSTNAME_OVERRIDE}") \
    --log-file=/var/log/cm-purplepill/cm-purplepill.log'