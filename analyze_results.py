import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Parse CPU Speed
def parse_cpu_speed(content):
    pattern = r'events per second:\s+([\d.]+)'
    matches = re.findall(pattern, content)
    return [float(x) for x in matches]

# Parse Memory Access
def parse_memory_access(content):
    memcpy_pattern = r'Method: MEMCPY.*?Copy:\s+([\d.]+)'
    dumb_pattern = r'Method: DUMB.*?Copy:\s+([\d.]+)'
    mcblock_pattern = r'Method: MCBLOCK.*?Copy:\s+([\d.]+)'
    
    memcpy = [float(x) for x in re.findall(memcpy_pattern, content)]
    dumb = [float(x) for x in re.findall(dumb_pattern, content)]
    mcblock = [float(x) for x in re.findall(mcblock_pattern, content)]
    
    return {
        'MEMCPY': memcpy,
        'DUMB': dumb,
        'MCBLOCK': mcblock
    }

# Parse Disk Read Speed
def parse_disk_speed(content):
    pattern = r'Read BW:\s+(\d+)\s+KB/s'
    matches = re.findall(pattern, content)
    return [float(x) / 1024 for x in matches]  # Convert to MB/s

# Parse Network Speed
def parse_network_speed(content):
    pattern = r'\[\s+\d+\].*?sec\s+[\d.]+\s+GBytes\s+([\d.]+)\s+Gbits/sec'
    matches = re.findall(pattern, content)
    return [float(x) for x in matches]

# Parse Forksum Process Speed (real time)
def parse_forksum(content):
    pattern = r'real\s+0m([\d.]+)s'
    matches = re.findall(pattern, content)
    return [float(x) for x in matches]

# Load all result files
results_dir = Path('/Users/adamyuan/Documents/UofG/Yr 4/Courses/Cloud Systems/results')
files = {
    'Native': 'results_native.txt',
    'Docker': 'docker.txt',
    'QEMU+HW': 'QEMU With Hardware enabled.txt',
    'QEMU-HW': 'QEMU Without Hardware enabled.txt'
}

data = {}
for name, filename in files.items():
    with open(results_dir / filename, 'r') as f:
        content = f.read()
        data[name] = {
            'cpu': parse_cpu_speed(content),
            'memory': parse_memory_access(content),
            'disk': parse_disk_speed(content),
            'network': parse_network_speed(content),
            'forksum': parse_forksum(content)
        }

methods = ['MEMCPY', 'DUMB', 'MCBLOCK']
x_pos = np.arange(len(files))

# 1. CPU Speed Comparison
fig1 = plt.figure(figsize=(10, 6))
ax1 = fig1.add_subplot(111)
cpu_data = [np.mean(data[env]['cpu']) for env in files.keys()]
cpu_std = [np.std(data[env]['cpu']) for env in files.keys()]
bars = ax1.bar(x_pos, cpu_data, yerr=cpu_std, capsize=5, alpha=0.7, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
ax1.set_ylabel('Events per Second', fontsize=11)
ax1.set_title('CPU Speed (Sysbench)', fontsize=13, fontweight='bold')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(files.keys(), rotation=15, ha='right')
ax1.grid(axis='y', alpha=0.3)
for i, (v, s) in enumerate(zip(cpu_data, cpu_std)):
    ax1.text(i, v + s + 1000, f'{v:.0f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(results_dir / 'cpu_speed_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Memory Access Comparison
fig2 = plt.figure(figsize=(10, 6))
ax2 = fig2.add_subplot(111)
x = np.arange(len(files))
width = 0.25
colors = ['#2E86AB', '#A23B72', '#F18F01']
for i, method in enumerate(methods):
    means = [np.mean(data[env]['memory'][method]) for env in files.keys()]
    ax2.bar(x + i*width, means, width, label=method, alpha=0.7, color=colors[i])
ax2.set_ylabel('Memory Bandwidth (MiB/s)', fontsize=11)
ax2.set_title('Memory Access Speed', fontsize=13, fontweight='bold')
ax2.set_xticks(x + width)
ax2.set_xticklabels(files.keys(), rotation=15, ha='right')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(results_dir / 'memory_speed_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Disk Read Speed
fig3 = plt.figure(figsize=(10, 6))
ax3 = fig3.add_subplot(111)
disk_data = [np.mean(data[env]['disk']) for env in files.keys()]
disk_std = [np.std(data[env]['disk']) for env in files.keys()]
bars = ax3.bar(x_pos, disk_data, yerr=disk_std, capsize=5, alpha=0.7, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
ax3.set_ylabel('Read Speed (MB/s)', fontsize=11)
ax3.set_title('Disk Read Speed', fontsize=13, fontweight='bold')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(files.keys(), rotation=15, ha='right')
ax3.grid(axis='y', alpha=0.3)
for i, (v, s) in enumerate(zip(disk_data, disk_std)):
    ax3.text(i, v + s + 5, f'{v:.1f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(results_dir / 'disk_speed_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Network Speed
fig4 = plt.figure(figsize=(10, 6))
ax4 = fig4.add_subplot(111)
net_data = [np.mean(data[env]['network']) for env in files.keys()]
net_std = [np.std(data[env]['network']) for env in files.keys()]
bars = ax4.bar(x_pos, net_data, yerr=net_std, capsize=5, alpha=0.7, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
ax4.set_ylabel('Throughput (Gbits/sec)', fontsize=11)
ax4.set_title('Network Speed (iperf3)', fontsize=13, fontweight='bold')
ax4.set_xticks(x_pos)
ax4.set_xticklabels(files.keys(), rotation=15, ha='right')
ax4.grid(axis='y', alpha=0.3)
for i, (v, s) in enumerate(zip(net_data, net_std)):
    ax4.text(i, v + s + 0.5, f'{v:.1f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(results_dir / 'network_speed_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Forksum Process Speed
fig5 = plt.figure(figsize=(10, 6))
ax5 = fig5.add_subplot(111)
fork_data = [np.mean(data[env]['forksum']) for env in files.keys()]
fork_std = [np.std(data[env]['forksum']) for env in files.keys()]
bars = ax5.bar(x_pos, fork_data, yerr=fork_std, capsize=5, alpha=0.7, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
ax5.set_ylabel('Time (seconds)', fontsize=11)
ax5.set_title('Process Creation Speed (Forksum) - Lower is Better', fontsize=13, fontweight='bold')
ax5.set_xticks(x_pos)
ax5.set_xticklabels(files.keys(), rotation=15, ha='right')
ax5.grid(axis='y', alpha=0.3)
for i, (v, s) in enumerate(zip(fork_data, fork_std)):
    ax5.text(i, v + s + 0.005, f'{v:.3f}s', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(results_dir / 'forksum_speed_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Overall Performance Summary
fig6 = plt.figure(figsize=(10, 6))
ax6 = fig6.add_subplot(111)
native_cpu = np.mean(data['Native']['cpu'])
native_mem_avg = np.mean([np.mean(data['Native']['memory'][m]) for m in methods])
native_disk = np.mean(data['Native']['disk'])
native_net = np.mean(data['Native']['network'])
native_fork = np.mean(data['Native']['forksum'])

normalized_scores = []
for env in files.keys():
    cpu_score = np.mean(data[env]['cpu']) / native_cpu
    mem_score = np.mean([np.mean(data[env]['memory'][m]) for m in methods]) / native_mem_avg
    disk_score = np.mean(data[env]['disk']) / native_disk
    net_score = np.mean(data[env]['network']) / native_net
    fork_score = native_fork / np.mean(data[env]['forksum'])
    overall = (cpu_score + mem_score + disk_score + net_score + fork_score) / 5
    normalized_scores.append(overall)

bars = ax6.bar(x_pos, normalized_scores, alpha=0.7, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
ax6.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Native Baseline')
ax6.set_ylabel('Normalized Performance', fontsize=11)
ax6.set_title('Overall Performance (Normalized to Native)', fontsize=13, fontweight='bold')
ax6.set_xticks(x_pos)
ax6.set_xticklabels(files.keys(), rotation=15, ha='right')
ax6.legend()
ax6.grid(axis='y', alpha=0.3)
for i, v in enumerate(normalized_scores):
    ax6.text(i, v + 0.02, f'{v:.2f}x', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(results_dir / 'overall_performance_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"✓ CPU speed comparison saved to: {results_dir / 'cpu_speed_comparison.png'}")
print(f"✓ Memory speed comparison saved to: {results_dir / 'memory_speed_comparison.png'}")
print(f"✓ Disk speed comparison saved to: {results_dir / 'disk_speed_comparison.png'}")
print(f"✓ Network speed comparison saved to: {results_dir / 'network_speed_comparison.png'}")
print(f"✓ Forksum speed comparison saved to: {results_dir / 'forksum_speed_comparison.png'}")
print(f"✓ Overall performance comparison saved to: {results_dir / 'overall_performance_comparison.png'}")

# Print summary statistics
print("\n" + "="*80)
print("PERFORMANCE SUMMARY STATISTICS")
print("="*80)

for env in files.keys():
    print(f"\n{env}:")
    print(f"  CPU Speed:       {np.mean(data[env]['cpu']):8.2f} ± {np.std(data[env]['cpu']):6.2f} events/sec")
    print(f"  Memory (avg):    {np.mean([np.mean(data[env]['memory'][m]) for m in methods]):8.2f} MiB/s")
    print(f"  Disk Read:       {np.mean(data[env]['disk']):8.2f} ± {np.std(data[env]['disk']):6.2f} MB/s")
    print(f"  Network:         {np.mean(data[env]['network']):8.2f} ± {np.std(data[env]['network']):6.2f} Gbits/sec")
    print(f"  Forksum:         {np.mean(data[env]['forksum']):8.3f} ± {np.std(data[env]['forksum']):6.3f} seconds")
    print(f"  Overall Score:   {normalized_scores[list(files.keys()).index(env)]:.3f}x (normalized)")

print("\n" + "="*80)
print("KEY OBSERVATIONS:")
print("="*80)

print(f"\n1. CPU Performance:")
for env in list(files.keys())[1:]:
    diff = (np.mean(data[env]['cpu']) / np.mean(data['Native']['cpu']) - 1) * 100
    print(f"   {env} vs Native: {diff:+.1f}%")

print(f"\n2. Process Creation (Forksum):")
for env in list(files.keys())[1:]:
    diff = (np.mean(data[env]['forksum']) / np.mean(data['Native']['forksum']) - 1) * 100
    print(f"   {env} vs Native: {diff:+.1f}% (negative is better)")

print(f"\n3. Disk I/O:")
for env in list(files.keys())[1:]:
    diff = (np.mean(data[env]['disk']) / np.mean(data['Native']['disk']) - 1) * 100
    print(f"   {env} vs Native: {diff:+.1f}%")

print(f"\n4. Network Throughput:")
for env in list(files.keys())[1:]:
    diff = (np.mean(data[env]['network']) / np.mean(data['Native']['network']) - 1) * 100
    print(f"   {env} vs Native: {diff:+.1f}%")

print("\n" + "="*80)
