# Distributed OpenFOAM Cluster Setup

## Your Cluster

Edit `cluster_profile.json` (copy from `cluster_profile.example.json`) with your nodes:

| Role | Hostname | IP |
|------|----------|----|
| Head node | node1 | 192.168.1.X |
| Compute | node2 | 192.168.1.X |
| Compute | node3 | 192.168.1.X |
| Compute | node4 | 192.168.1.X |

Run `python3 cluster_profile.py` on each machine to auto-detect specs and generate a recommended hostfile.

## Step 1: Install OpenFOAM on All Machines

### Mac:
```bash
brew install openfoam
# OR use Docker:
docker pull openfoam/openfoam-dev
```

### Ubuntu/Linux:
```bash
sudo apt-get update
sudo apt-get install openfoam
```

### Windows:
```bash
# Use WSL2 + Docker
wsl --install
docker pull openfoam/openfoam-dev
```

## Step 2: Install MPI on All Machines

### Mac:
```bash
brew install open-mpi
```

### Linux:
```bash
sudo apt-get install openmpi-bin libopenmpi-dev
```

## Step 3: Setup SSH Keys (Passwordless SSH)

On head node:
```bash
ssh-keygen -t rsa -b 4096
# Copy public key to each compute node:
ssh-copy-id user@<node2-ip>
ssh-copy-id user@<node3-ip>
ssh-copy-id user@<node4-ip>
# Test:
ssh user@<node2-ip> 'hostname'
```

## Step 4: Shared Filesystem

All nodes need access to the same case files.

### Option A: NFS (Best performance)

**On head node:**
```bash
sudo nano /etc/exports
# Add:
/home/user/OpenFOAM-Cases 192.168.1.0/24(rw,sync,no_subtree_check)
sudo exportfs -ra
```

**On compute nodes:**
```bash
sudo mount <head-node-ip>:/home/user/OpenFOAM-Cases /mnt/openfoam
# Add to /etc/fstab for auto-mount:
<head-node-ip>:/home/user/OpenFOAM-Cases /mnt/openfoam nfs defaults 0 0
```

### Option B: rsync (Simpler, slower)
```bash
rsync -avz myCase/ user@<node2-ip>:~/OpenFOAM/myCase/
```

## Step 5: Create MPI Hostfile

Use `cluster_profile.py` to auto-generate, or create `~/hostfile` manually:
```
<node1-ip> slots=8  # Head node
<node2-ip> slots=8  # Compute node 2
<node3-ip> slots=4  # Compute node 3
<node4-ip> slots=8  # Compute node 4
```

## Step 6: Prepare OpenFOAM Case

```bash
cd ~/OpenFOAM-Cases/myCase
blockMesh
```

Edit `system/decomposeParDict`:
```c
numberOfSubdomains 28;  // Total cores across cluster

method          scotch;  // or hierarchical, simple

hierarchicalCoeffs  // if using hierarchical
{
    n           (7 2 2);  // Decompose in X, Y, Z
}
```

Decompose the mesh:
```bash
decomposePar
```

## Step 7: Run Distributed OpenFOAM

```bash
mpirun -np 28 \
  --hostfile ~/hostfile \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  simpleFoam -parallel
```

## Step 8: Monitor Cluster

Create `cluster_monitor.sh`:
```bash
#!/bin/bash
echo "=== OpenFOAM Cluster Status ==="
for host in <node1-ip> <node2-ip> <node3-ip> <node4-ip>; do
    echo -n "$host: "
    ssh $host "top -bn1 | grep 'Cpu(s)' || uptime" 2>/dev/null || echo "OFFLINE"
done
```

```bash
chmod +x cluster_monitor.sh
watch -n 5 ./cluster_monitor.sh
```

## Step 9: Collect Results

```bash
reconstructPar
paraFoam
```

## Optimization Tips

### 1. Network Performance
```bash
# Test bandwidth between nodes
iperf3 -s          # on head node
iperf3 -c <head-node-ip>  # on compute nodes
```

### 2. Load Balancing
Assign more slots to faster machines — `cluster_profile.py` does this automatically based on benchmark scores.

### 3. Case-Specific Decomposition
```bash
# For flow over a cylinder, decompose in flow direction
hierarchicalCoeffs
{
    n           (12 2 1);  // More divisions along flow
    order       xyz;
}
```

### 4. Reduce Network Communication
- Use larger time steps
- Reduce write frequency
- Use local scratch space for temporary files

## FrankChat Integration

Use [FrankChat](https://github.com/fgillet4/frankChat) to coordinate jobs across nodes:

```json
{
  "triggers": [
    {
      "pattern": "start openfoam",
      "response": "Starting OpenFOAM compute node...",
      "enabled": true
    },
    {
      "pattern": "cluster status",
      "response": "Compute node ready",
      "enabled": true
    }
  ]
}
```

## Advanced: Docker Swarm Alternative

```bash
# Head node (manager):
docker swarm init

# Compute nodes:
docker swarm join --token <token> <head-node-ip>:2377

# Deploy OpenFOAM service:
docker service create \
  --name openfoam-cluster \
  --replicas 4 \
  openfoam/openfoam-dev
```

## Performance Expectations

For a typical CFD case (1M cells):
- Single node: ~4 hours
- 4-node cluster (28 cores): ~30-45 minutes

Network becomes bottleneck with >16 cores on WiFi. Consider:
- Ethernet connections (1Gbps+)
- Larger mesh partitions (reduce communication)
- Infiniband for HPC (expensive)
