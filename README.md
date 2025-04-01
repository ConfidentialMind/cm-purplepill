# ConfidentialMind Container GPU Monitor (CM PurplePill)

A GPU metrics exporter, with Kubernetes pod-level GPU usage tracking, not relying on explicit `<vendor.com>/gpu` resource declarations.

## Features

- Collects GPU metrics using NVML
- Maps GPU processes to Kubernetes pods
- Exposes metrics in Prometheus format
- No dependencies beyond Python 3.7+ and NVML
- Compatible with all K8s distributions
- Tracks GPU usage by pods **without** explicit `nvidia.com/gpu` resource requests

## Metrics

The exporter provides the following metrics:

- `CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB` - Total GPU memory in MiB
- `CM_PURPLEPILL_GPU_MEMORY_USED_TOTAL_MIB` - Total used GPU memory in MiB
- `CM_PURPLEPILL_GPU_MEMORY_FREE_MIB` - Free GPU memory in MiB
- `CM_PURPLEPILL_GPU_UTILIZATION` - GPU utilization percentage
- `CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB` - Pod GPU memory usage in MiB

## Deployment Methods

### 1. Kubernetes Deployment (Recommended)

This is the primary deployment method for CM PurplePill, designed to monitor GPU usage across your Kubernetes cluster.

#### Prerequisites

- Kubernetes cluster with NVIDIA GPUs (K3s, AKS, GKE, or other K8s distributions)
- NVIDIA drivers installed on worker nodes
- Prometheus monitoring setup (preferably using Prometheus Operator)

#### DaemonSet Deployment

Deploy CM PurplePill as a DaemonSet that runs on every node with an NVIDIA GPU:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cm-purplepill
  namespace: monitoring
  labels:
    app: cm-purplepill
spec:
  selector:
    matchLabels:
      app: cm-purplepill
  template:
    metadata:
      labels:
        app: cm-purplepill
    spec:
      hostPID: true
      containers:
      - name: cm-purplepill
        image: confidentialmindpub.azurecr.io/cm-purplepill:x.y.z # <-- set the actual tag here
        imagePullPolicy: IfNotPresent
        ports:
        - name: metrics
          containerPort: 9531
          protocol: TCP
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
        volumeMounts:
        - name: log
          mountPath: /var/log/cm-purplepill
        env:
        - name: CM_PURPLEPILL_HOSTNAME_OVERRIDE
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        securityContext:
          privileged: true
      volumes:
      - name: log
        emptyDir: {}
      nodeSelector:
        feature.node.kubernetes.io/pci-10de.present: "true"  # Target NVIDIA GPU nodes
      tolerations:
      - effect: NoSchedule
        operator: Exists
```

#### Prometheus Configuration

**IMPORTANT! All the nodes should have unique names for Prometheus scraper to be able to collect GPU metrics from them.**

For Prometheus Operator (preferred approach), add this ScrapeConfig:

```yaml
apiVersion: monitoring.coreos.com/v1alpha1
kind: ScrapeConfig
metadata:
  labels:
    release: prometheus #IMPORTANT! check your Prometheus 
                        #"scrapeConfigSelector" and "scrapeConfigNamespaceSelector" current values
  name: cm-purplepill
  namespace: monitoring
spec:
  scrapeInterval: 15s
  kubernetesSDConfigs:
    - role: Pod
  relabelings:
    - sourceLabels: [__meta_kubernetes_pod_label_app]
      regex: 'cm-purplepill'
      action: keep
    - sourceLabels: [__meta_kubernetes_namespace]
      regex: 'monitoring'
      action: keep
    - sourceLabels: [__meta_kubernetes_pod_container_port_name]
      regex: 'metrics'
      action: keep
    - sourceLabels: [__meta_kubernetes_pod_node_name]
      targetLabel: node
    - sourceLabels: [__meta_kubernetes_pod_name]
      targetLabel: pod
    - action: labelmap
      regex: __meta_kubernetes_pod_label_(.+)
```

See [ScrapeConfig CRD](https://prometheus-operator.dev/docs/developer/scrapeconfig/) for more details and options.

### 2. Docker or another OCI-compatible container

For environments where you want to run CM PurplePill directly on a host using Docker or another OCI-compatible container runtime.

#### Environment Variables

The Docker container can be configured using the following environment variables:

| Environment Variable           | Default     | Description |
|--------------------------------|-------------|-------------|
| `CM_PURPLEPILL_PORT`              | `9531`      | Port to expose |
| `CM_PURPLEPILL_INTERVAL`          | `15`        | Interval between metric collections in seconds |
| `CM_PURPLEPILL_HOSTNAME_OVERRIDE` | OS hostname | Override the Hostname used in metrics labels. |

#### Example Usage

```bash
# Run with default settings
docker run -d --gpus all -p 9531:9531 confidentialmind/cm-purplepill

# Run with custom settings
docker run -d --gpus all \
  -p 8080:8080 \
  -e CM_PURPLEPILL_PORT=8080 \
  -e CM_PURPLEPILL_INTERVAL=30 \
  -e CM_PURPLEPILL_HOSTNAME_OVERRIDE="gpu-host-01" \
  confidentialmind/cm-purplepill
```

### 3. Direct Host Installation

If you prefer to install CM PurplePill directly on the host without containerization:

#### Prerequisites

- Python 3.7 or higher
- NVIDIA drivers with `nvidia-smi` tool

#### Pip Installation
- directly from GitHub
```bash
# Install directly from git repository
pip install git+https://github.com/ConfidentialMind/cm-purplepill.git

# Install systemd service (may need to download separately)
curl -o /etc/systemd/system/cm-purplepill.service https://raw.githubusercontent.com/ConfidentialMind/cm-purplepill/main/systemd/cm-purplepill.service
```

- by manual cloning from GitHub
```bash
# Clone repository
git clone https://github.com/ConfidentialMind/cm-purplepill.git
cd cm-purplepill

# Install dependencies
pip install .

# Install systemd service
cp systemd/cm-purplepill.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable cm-purplepill
systemctl start cm-purplepill
```

#### Verification

Check if the exporter is running:

```bash
systemctl status cm-purplepill
curl http://localhost:9531/metrics
```

#### Uninstallation

##### Automatic Uninstallation
```bash
# Stop and disable the systemd service
sudo systemctl stop cm-purplepill
sudo systemctl disable cm-purplepill

# Remove the systemd service file
sudo rm /etc/systemd/system/cm-purplepill.service
sudo systemctl daemon-reload

# Uninstall the package
pip uninstall cm-purplepill
```

##### Manual Uninstallation (Cleanup)
```bash
# Stop and disable the systemd service
sudo systemctl stop cm-purplepill
sudo systemctl disable cm-purplepill

# Remove the systemd service file
sudo rm /etc/systemd/system/cm-purplepill.service
sudo systemctl daemon-reload

# Find and remove Python package files
# The location depends on your Python environment
# Common locations:
sudo rm -rf /usr/local/lib/python*/dist-packages/cm_purplepill*
# OR
sudo rm -rf ~/.local/lib/python*/site-packages/cm_purplepill*

# Remove the cmpp entry point
sudo rm /usr/local/bin/cmpp
# OR
sudo rm ~/.local/bin/cmpp

# Clean up log files and temporary data
sudo rm -f /var/log/cm-purplepill.log
sudo rm -f /tmp/cmpp_metrics.prom
sudo rm -f /tmp/cmpp-exporter.pid
```


### 4. LXC or Other Non-OCI Container Environments

For LXC or other non-OCI container environments, you have two options:

**Note:** Similar to Docker deployment, the code would need modifications to correctly identify and label GPU processes for non-Kubernetes environments. Specifically, the container identification logic in `pod_info.py` would need to be extended to properly recognize LXC containers.

#### Option A: Direct Host Installation

Install CM PurplePill directly on the host as described in the "Direct Host Installation" section above. The service will be able to monitor GPUs across all containers.

#### Option B: Dockerfile-Based Approach

Create a container environment similar to the Dockerfile provided with CM PurplePill:

1. Start with a base image that includes CUDA libraries
2. Install Python 3.7+
3. Install CM PurplePill
4. Ensure the container has access to NVIDIA devices and can run `nvidia-smi`

## Configuration

The exporter can be configured using command-line arguments:

```
Usage:
    cmpp [options]

Options:
    --port PORT             Port to expose HTTP metrics server [default: 9531]
    --interval SECONDS      Interval between metric collections [default: 15]
    --log-file FILE         Log file path [default: /var/log/cm-purplepill.log]
    --metrics-file FILE     File to store metrics [default: /tmp/cmpp_metrics.prom]
    --help                  Show this help message and exit
    --version               Show version and exit
```

## Example PromQL Queries

```
# Total GPU memory per node
sum by (instance) (CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB)

# GPU utilization per pod
CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB

# Percentage of GPU memory used by pod
CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB / on (gpu, UUID) CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB * 100
```

## Troubleshooting

Check the logs:

```bash
# For Kubernetes deployment
kubectl logs -n monitoring daemonset/cm-purplepill

# For systemd service
journalctl -u cm-purplepill
# or
cat /var/log/cm-purplepill.log

# For Docker container
docker logs <container_id>
```

## Comparing CM PurplePill vs. NVIDIA DCGM Exporter

See [CMPurplePill-vs-DCGM.md](CMPurplePill-vs-DCGM.md) for a detailed comparison between CM PurplePill and NVIDIA's DCGM Exporter.

Key advantages of CM PurplePill:
1. Tracks GPU usage by containers (Kubernetes pods, Docker containers) that **don't explicitly request GPU resources**
2. Works across multiple container platforms and orchestration systems
3. Lightweight implementation with minimal dependencies
4. Flexibility to extend with additional metrics from nvidia-smi
5. Can be adapted for non-NVIDIA GPUs by modifying the data collection layer

## Future Enhancements (Coming Soon)

- Enable stdout in docker
- Add ConfidentialMind logo to stdout and logs
- Add CM PurplePill name to stdout and logs
- Additional GPU metrics from nvidia-smi
