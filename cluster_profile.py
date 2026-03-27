#!/usr/bin/env python3
"""
FrankCluster Profiler - Benchmark heterogeneous cluster and suggest optimal load balancing
"""
import subprocess
import json
import time
import platform
import multiprocessing
from pathlib import Path
from datetime import datetime

DEVICES_FILE = Path(__file__).parent / "devices.json"
PROFILE_FILE = Path(__file__).parent / "cluster_profile.json"


def get_local_specs():
    """Get local machine specifications"""
    specs = {
        "hostname": platform.node(),
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cpu_count": multiprocessing.cpu_count(),
        "python_version": platform.python_version(),
    }
    
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                cpu_info = f.read()
                if "model name" in cpu_info:
                    model = [line for line in cpu_info.split('\n') if "model name" in line][0]
                    specs["cpu_model"] = model.split(":")[1].strip()
            
            with open("/proc/meminfo") as f:
                mem_info = f.read()
                mem_total = [line for line in mem_info.split('\n') if "MemTotal" in line][0]
                specs["memory_mb"] = int(mem_total.split()[1]) // 1024
        
        elif platform.system() == "Darwin":
            cpu_brand = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
            specs["cpu_model"] = cpu_brand
            
            mem_bytes = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
            specs["memory_mb"] = int(mem_bytes) // (1024 * 1024)
        
        elif platform.system() == "Windows":
            cpu_info = subprocess.check_output(["wmic", "cpu", "get", "name"]).decode()
            specs["cpu_model"] = cpu_info.split('\n')[1].strip()
            
            mem_info = subprocess.check_output(["wmic", "computersystem", "get", "totalphysicalmemory"]).decode()
            specs["memory_mb"] = int(mem_info.split('\n')[1].strip()) // (1024 * 1024)
    
    except Exception as e:
        specs["error"] = str(e)
    
    return specs


def cpu_benchmark(duration=5):
    """Simple CPU benchmark - matrix multiplication"""
    import random
    
    print(f"  Running CPU benchmark for {duration}s...")
    
    size = 500
    iterations = 0
    start_time = time.time()
    
    while time.time() - start_time < duration:
        A = [[random.random() for _ in range(size)] for _ in range(size)]
        B = [[random.random() for _ in range(size)] for _ in range(size)]
        
        C = [[sum(a*b for a,b in zip(A_row, B_col)) 
              for B_col in zip(*B)] 
             for A_row in A]
        
        iterations += 1
    
    elapsed = time.time() - start_time
    score = iterations / elapsed
    
    print(f"  Score: {score:.2f} iterations/sec")
    return score


def memory_benchmark(duration=3):
    """Simple memory bandwidth test"""
    print(f"  Running memory benchmark for {duration}s...")
    
    size = 10_000_000
    iterations = 0
    start_time = time.time()
    
    while time.time() - start_time < duration:
        data = list(range(size))
        result = sum(data)
        iterations += 1
    
    elapsed = time.time() - start_time
    mb_per_sec = (size * 8 * iterations) / (elapsed * 1024 * 1024)
    
    print(f"  Bandwidth: {mb_per_sec:.2f} MB/s")
    return mb_per_sec


def network_benchmark(target_ip):
    """Test network latency to target"""
    print(f"  Testing network to {target_ip}...")
    
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(["ping", "-n", "10", target_ip], timeout=15).decode()
            lines = result.split('\n')
            for line in lines:
                if "Average" in line:
                    latency = float(line.split('=')[-1].replace('ms', '').strip())
                    print(f"  Latency: {latency:.2f}ms")
                    return latency
        else:
            result = subprocess.check_output(["ping", "-c", "10", target_ip], timeout=15).decode()
            lines = result.split('\n')
            for line in lines:
                if "avg" in line or "round-trip" in line:
                    parts = line.split('=')[1].split('/')
                    latency = float(parts[1])
                    print(f"  Latency: {latency:.2f}ms")
                    return latency
    except Exception as e:
        print(f"  Network test failed: {e}")
        return 999.0
    
    return 999.0


def run_full_benchmark(is_head_node=False, head_ip=None):
    """Run complete benchmark suite"""
    print(f"\n{'='*60}")
    print(f"FrankCluster Profiler - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    print("Gathering system specs...")
    specs = get_local_specs()
    
    print(f"\nSystem: {specs['hostname']}")
    print(f"CPU: {specs.get('cpu_model', 'Unknown')}")
    print(f"Cores: {specs['cpu_count']}")
    print(f"Memory: {specs.get('memory_mb', 'Unknown')} MB")
    print(f"Platform: {specs['platform']} ({specs['architecture']})")
    
    print("\n" + "="*60)
    print("Running Benchmarks...")
    print("="*60)
    
    cpu_score = cpu_benchmark()
    mem_score = memory_benchmark()
    
    network_score = 0.0
    if not is_head_node and head_ip:
        network_score = network_benchmark(head_ip)
    
    profile = {
        "hostname": specs["hostname"],
        "timestamp": datetime.now().isoformat(),
        "specs": specs,
        "benchmarks": {
            "cpu_score": cpu_score,
            "memory_bandwidth": mem_score,
            "network_latency_ms": network_score
        }
    }
    
    print(f"\n{'='*60}")
    print("Benchmark Complete!")
    print(f"{'='*60}\n")
    
    return profile


def ssh_run_benchmark(host, ip, username=None):
    """Run benchmark on remote host via SSH"""
    print(f"\n{'='*60}")
    print(f"Benchmarking remote host: {host} ({ip})")
    print(f"{'='*60}")
    
    script_path = str(Path(__file__).resolve())
    
    ssh_host_map = {
        "MacMini": "frank-local",
        "MacBook": "mac-local",
        "Pi": "powerpi-local",
        "PC-WSL": "pc-wsl-local"
    }
    
    ssh_target = ssh_host_map.get(host, f"{username or host.lower()}@{ip}")
    
    try:
        print(f"Copying script to {host}...")
        subprocess.run(
            ["scp", script_path, f"{ssh_target}:/tmp/cluster_profile.py"],
            check=True,
            timeout=30
        )
        
        print(f"Running benchmark on {host}...")
        result = subprocess.run(
            ["ssh", ssh_target, 
             f"python3 /tmp/cluster_profile.py --benchmark --head-ip {get_local_ip()}"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout
        print(output)
        
        for line in output.split('\n'):
            if line.strip().startswith('{'):
                try:
                    profile = json.loads(line)
                    return profile
                except:
                    pass
        
        return None
    
    except Exception as e:
        print(f"Error benchmarking {host}: {e}")
        return None


def get_local_ip():
    """Get local IP address"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def analyze_cluster(profiles):
    """Analyze cluster and suggest load balancing"""
    print(f"\n{'='*60}")
    print("CLUSTER ANALYSIS")
    print(f"{'='*60}\n")
    
    max_cpu = max(p["benchmarks"]["cpu_score"] for p in profiles)
    total_cores = sum(p["specs"]["cpu_count"] for p in profiles)
    
    print(f"Total Nodes: {len(profiles)}")
    print(f"Total Cores: {total_cores}")
    print(f"\nNode Performance Ranking:")
    print(f"{'-'*60}")
    
    sorted_profiles = sorted(profiles, key=lambda x: x["benchmarks"]["cpu_score"], reverse=True)
    
    for i, profile in enumerate(sorted_profiles, 1):
        hostname = profile["hostname"]
        cpu_score = profile["benchmarks"]["cpu_score"]
        cores = profile["specs"]["cpu_count"]
        relative_perf = (cpu_score / max_cpu) * 100
        
        print(f"{i}. {hostname:20s} | Cores: {cores:2d} | "
              f"Score: {cpu_score:6.2f} | Relative: {relative_perf:5.1f}%")
    
    print(f"\n{'='*60}")
    print("LOAD BALANCING RECOMMENDATIONS")
    print(f"{'='*60}\n")
    
    total_weight = sum(p["benchmarks"]["cpu_score"] * p["specs"]["cpu_count"] 
                       for p in profiles)
    
    print("MPI Hostfile Configuration:")
    print("-" * 60)
    
    hostfile_lines = []
    suggested_slots = {}
    
    for profile in sorted_profiles:
        hostname = profile["hostname"]
        cores = profile["specs"]["cpu_count"]
        cpu_score = profile["benchmarks"]["cpu_score"]
        
        weight = (cpu_score / max_cpu)
        suggested = max(1, int(cores * weight))
        
        suggested_slots[hostname] = suggested
        
        latency = profile["benchmarks"].get("network_latency_ms", 0)
        latency_str = f" (latency: {latency:.1f}ms)" if latency > 0 else ""
        
        line = f"{hostname} slots={suggested} max_slots={cores}{latency_str}"
        hostfile_lines.append(line)
        print(line)
    
    print(f"\nTotal Suggested Slots: {sum(suggested_slots.values())}")
    
    print(f"\n{'='*60}")
    print("OpenFOAM decomposeParDict Suggestion:")
    print(f"{'='*60}\n")
    
    total_slots = sum(suggested_slots.values())
    
    factors = []
    for i in range(2, total_slots + 1):
        if total_slots % i == 0:
            factors.append(i)
    
    if len(factors) >= 3:
        nx = factors[-1]
        ny = factors[len(factors)//2]
        nz = total_slots // (nx * ny)
    elif len(factors) >= 2:
        nx = factors[-1]
        ny = factors[-2]
        nz = total_slots // (nx * ny)
    else:
        nx = total_slots
        ny = 1
        nz = 1
    
    print(f"numberOfSubdomains {total_slots};")
    print(f"\nmethod          hierarchical;")
    print(f"\nhierarchicalCoeffs")
    print(f"{{")
    print(f"    n           ({nx} {ny} {nz});")
    print(f"    order       xyz;")
    print(f"}}")
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "profiles": profiles,
        "recommendations": {
            "total_nodes": len(profiles),
            "total_cores": total_cores,
            "suggested_slots": suggested_slots,
            "total_slots": total_slots,
            "decomposition": {"nx": nx, "ny": ny, "nz": nz},
            "hostfile": hostfile_lines
        }
    }
    
    with open(PROFILE_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Profile saved to: {PROFILE_FILE}")
    print(f"{'='*60}\n")
    
    return result


def generate_hostfile(recommendations):
    """Generate MPI hostfile"""
    hostfile_path = Path.home() / "openfoam_hostfile"
    
    with open(hostfile_path, 'w') as f:
        for line in recommendations["hostfile"]:
            f.write(line.split(' (')[0] + '\n')
    
    print(f"MPI hostfile written to: {hostfile_path}")
    return hostfile_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FrankCluster Profiler")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark only")
    parser.add_argument("--head-ip", type=str, help="Head node IP for network test")
    parser.add_argument("--cluster", action="store_true", help="Profile entire cluster")
    
    args = parser.parse_args()
    
    if args.benchmark:
        profile = run_full_benchmark(
            is_head_node=(args.head_ip is None),
            head_ip=args.head_ip
        )
        print(json.dumps(profile))
    
    elif args.cluster:
        if not DEVICES_FILE.exists():
            print(f"Error: {DEVICES_FILE} not found")
            print("Please configure devices.json first")
            exit(1)
        
        with open(DEVICES_FILE) as f:
            config = json.load(f)
        
        devices = config.get("devices", {})
        
        print("This will benchmark all devices in your cluster.")
        print("Ensure SSH keys are set up for passwordless access.\n")
        
        local_hostname = platform.node().split('.')[0]
        profiles = []
        
        print("Benchmarking local machine...")
        local_profile = run_full_benchmark(is_head_node=True)
        profiles.append(local_profile)
        
        for name, ip in devices.items():
            if name.lower() not in local_hostname.lower():
                profile = ssh_run_benchmark(name, ip)
                if profile:
                    profiles.append(profile)
        
        if profiles:
            analyze_cluster(profiles)
            
            print("\nGenerate MPI hostfile? (y/n): ", end='')
            if input().lower() == 'y':
                result = json.load(open(PROFILE_FILE))
                generate_hostfile(result["recommendations"])
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python cluster_profile.py --benchmark              # Benchmark local machine")
        print("  python cluster_profile.py --cluster                # Profile entire cluster")
