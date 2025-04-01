# CM PurplePill: Kubernetes GPU Monitoring Solution

## 1. Main Problem Being Solved

- Standard Kubernetes GPU monitoring tools only track pods with explicit `nvidia.com/gpu` resource requests
- Some applications utilise GPUs without declaring these resource requests
- Creates significant monitoring gaps where GPU usage is effectively "invisible" and/or untraceable. 

## 2. What is CM PurplePill?

**Definition:**
A lightweight Prometheus exporter for GPU metrics in Kubernetes environments that tracks pod-level GPU usage **without** requiring explicit GPU resource declarations.

**Key Features:**
- Identifies GPU usage by containers with no explicit `nvidia.com/gpu` resource declarations
- Maps GPU processes to Kubernetes pods across various K8s distributions (K3s, AKS, GKE)
- Exposes metrics in Prometheus format for seamless integration
- Uses only `nvidia-smi` directly with no additional software dependencies
- Implementation in ~500 lines of Python code

**Core Metrics:**
- `CM_PURPLEPILL_GPU_MEMORY_TOTAL_MIB` - Total GPU memory
- `CM_PURPLEPILL_GPU_MEMORY_USED_TOTAL_MIB` - Total used memory
- `CM_PURPLEPILL_GPU_MEMORY_FREE_MIB` - Free memory
- `CM_PURPLEPILL_GPU_UTILIZATION` - GPU utilisation percentage
- `CM_PURPLEPILL_GPU_MEMORY_USED_POD_MIB` - Pod-specific memory usage

**Startup Example:**
```
[2025-03-22 02:47:21] INFO: ConfidentialMind Container GPU Monitor (CM PurplePill) v1.0.0 starting
[2025-03-22 02:47:21] INFO: Metrics collector started with interval 15s
[2025-03-22 02:47:21] INFO: HTTP server started on 0.0.0.0:9531
[2025-03-22 02:47:21] INFO: CM PurplePill running - press Ctrl+C to stop
```

**Command-Line Options:**
```
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
```

## 3. Deployment Options

1. **Kubernetes DaemonSet (Recommended)**
   - All-in-one container deployment in K8s
   - Runs on GPU nodes with node selector: `feature.node.kubernetes.io/pci-10de.present: "true"`
   - Requires hostPID access to monitor processes
   - Works with Prometheus Operator's ScrapeConfig
   - Uses standard NVIDIA software for K8s hosts

2. **Direct Host Installation**
   - Deployable as a systemd service or Docker container
   - Installable via pip or from source
   - **Minimal Dependencies:**
     - Python 3.7+ 
     - NVIDIA drivers with `nvidia-smi` tool
     - No external Python packages (standard library only)

## 4. CM PurplePill vs NVIDIA DCGM

**Digital Sovereignty Benefits:**

| Factor | CM PurplePill | NVIDIA DCGM |
|--------|-----------|-------------|
| **Implementation Control** | Open architecture with visibility into monitoring logic | Proprietary black-box solution |
| **Vendor Independence** | Adaptable for non-NVIDIA GPUs by modifying collection layer | NVIDIA-specific solution only |
| **Customisability** | Easily modifiable for specific environments | Configuration limited to provided options |

**Technical Comparison:**

| Feature | CM PurplePill | NVIDIA DCGM |
|---------|-----------|-------------|
| **Core Dependencies** | Uses only `nvidia-smi` directly | Requires full DCGM stack installation |
| **Pod Detection** | Works without explicit GPU resource requests | Requires standard resource allocation |
| **Installation** | Simple Python script or container | Complex setup with NVIDIA Container Toolkit |
| **Metrics Coverage** | Core metrics with easy extension | Comprehensive metrics (temperature, power, etc.) |

## 5. Conclusion

**Key Value:**
- Complete visibility into all GPU workloads, including those without resource declarations
- Lightweight solution with small operational footprint
- Full control over monitoring stack
- Simple deployment as a DaemonSet on GPU-enabled nodes
