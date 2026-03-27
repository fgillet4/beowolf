# Beowolf

**Distributed OpenFOAM cluster toolkit for heterogeneous machines.**

Profile your nodes, auto-balance MPI slots by real benchmark scores, and run parallel CFD simulations across any mix of Mac, Linux, and Windows (WSL) machines.

---

## What it does

- **Benchmarks** each node (CPU, memory bandwidth, network latency)
- **Auto-generates** an optimal MPI hostfile weighted by actual performance
- **Suggests** `decomposeParDict` settings for your total slot count
- **R benchmark** script for quick cross-node comparison

---

## Quickstart

### 1. Profile your local machine

```bash
python3 cluster_profile.py --benchmark
```

### 2. Profile the whole cluster (from head node)

Set up passwordless SSH to all nodes first, then:

```bash
cp cluster_profile.example.json cluster_profile.json
# edit cluster_profile.json with your node hostnames/IPs
python3 cluster_profile.py --cluster
```

This SSHs into each node, runs the benchmark, collects results, and writes:
- `cluster_profile.json` — full results
- `~/openfoam_hostfile` — ready-to-use MPI hostfile

### 3. Run OpenFOAM

```bash
cd ~/OpenFOAM-Cases/myCase
blockMesh
decomposePar
mpirun -np <total_slots> --hostfile ~/openfoam_hostfile simpleFoam -parallel
reconstructPar
```

---

## Cluster setup

See [OPENFOAM_CLUSTER.md](OPENFOAM_CLUSTER.md) for full step-by-step:
- Installing OpenFOAM + MPI on Mac / Linux / Windows (WSL)
- Passwordless SSH setup
- NFS shared filesystem
- Monitoring and troubleshooting

---

## Files

| File | Description |
|------|-------------|
| `cluster_profile.py` | Benchmark + MPI hostfile generator |
| `cluster_profile.example.json` | Template — copy to `cluster_profile.json` |
| `benchmark.R` | R benchmark for cross-node comparison |
| `OPENFOAM_CLUSTER.md` | Full cluster setup guide |

`cluster_profile.json` is gitignored — it contains your real hostnames and IPs.

---

## Requirements

- Python 3.9+
- OpenMPI (`brew install open-mpi` / `apt install openmpi-bin`)
- OpenFOAM
- Passwordless SSH between nodes

---

## Tested on

- Apple M1 / M2 (macOS)
- Raspberry Pi (Linux aarch64)
- Intel i9 (Ubuntu / WSL2)
