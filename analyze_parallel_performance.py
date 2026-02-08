import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def parse_parallel_scaling(content):
    """Parse parallel scaling data with thread counts"""
    thread_data = {}
    
    # Split into sections by "Threads: X"
    lines = content.split('\n')
    current_thread_count = None
    
    for line in lines:
        # Check if this is a thread count line
        thread_match = re.match(r'Threads:\s+(\d+)', line)
        if thread_match:
            current_thread_count = int(thread_match.group(1))
            thread_data[current_thread_count] = []
        # Check if this is an events per second line
        elif current_thread_count is not None:
            event_match = re.search(r'events per second:\s+([\d.]+)', line)
            if event_match:
                thread_data[current_thread_count].append(float(event_match.group(1)))
    
    return thread_data

# Load all result files
results_dir = Path('/Users/adamyuan/Documents/UofG/Yr 4/Courses/Cloud Systems/results')
files = {
    'Native': 'results_native.txt',
    'Docker': 'docker.txt',
    'QEMU+HW': 'QEMU With Hardware enabled.txt',
    'QEMU-HW': 'QEMU Without Hardware enabled.txt'
}

parallel_data = {}
for name, filename in files.items():
    with open(results_dir / filename, 'r') as f:
        content = f.read()
        parallel_data[name] = parse_parallel_scaling(content)

# Create individual graphs for each deployment
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
deployment_names = list(files.keys())

for idx, (deployment, ax) in enumerate(zip(deployment_names, axes)):
    data = parallel_data[deployment]
    
    if not data:
        ax.text(0.5, 0.5, f'No parallel data\nfor {deployment}', 
                ha='center', va='center', fontsize=14)
        ax.set_title(deployment, fontsize=14, fontweight='bold')
        continue
    
    # Sort by thread count
    thread_counts = sorted(data.keys())
    means = [np.mean(data[t]) for t in thread_counts]
    stds = [np.std(data[t]) for t in thread_counts]
    
    # Plot with error bars
    ax.errorbar(thread_counts, means, yerr=stds, marker='o', markersize=8, 
                linewidth=2, capsize=5, capthick=2, color=colors[idx], 
                label='Performance')
    
    # Add data point labels
    for t, m, s in zip(thread_counts, means, stds):
        ax.text(t, m + s + 1000, f'{m:.0f}', ha='center', va='bottom', fontsize=9)
    
    # Calculate and display speedup
    if len(thread_counts) > 1 and thread_counts[0] == 1:
        baseline = means[0]
        speedups = [m / baseline for m in means]
        
        # Create secondary axis for speedup
        ax2 = ax.twinx()
        ax2.plot(thread_counts, speedups, 'r--', marker='s', markersize=6, 
                linewidth=1.5, alpha=0.7, label='Speedup')
        ax2.set_ylabel('Speedup (vs 1 thread)', fontsize=11, color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.grid(False)
        
        # Add speedup labels
        for t, sp in zip(thread_counts, speedups):
            ax2.text(t, sp + 0.02, f'{sp:.2f}x', ha='center', va='bottom', 
                    fontsize=8, color='red')
    
    ax.set_xlabel('Thread Count', fontsize=12)
    ax.set_ylabel('Events per Second', fontsize=12, color=colors[idx])
    ax.set_title(f'{deployment} - Parallel Scaling', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(thread_counts)
    
    # Calculate efficiency (speedup / threads)
    if len(thread_counts) > 1 and thread_counts[0] == 1:
        efficiencies = [speedups[i] / thread_counts[i] * 100 for i in range(len(thread_counts))]
        efficiency_text = '\n'.join([f'{t}T: {eff:.1f}%' for t, eff in zip(thread_counts, efficiencies)])
        ax.text(0.02, 0.98, f'Efficiency:\n{efficiency_text}', 
                transform=ax.transAxes, fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig(results_dir / 'parallel_performance_individual.png', dpi=300, bbox_inches='tight')
print(f"✓ Individual parallel performance graphs saved to: {results_dir / 'parallel_performance_individual.png'}")

# Create a combined comparison graph
fig2, ax = plt.subplots(figsize=(14, 8))

for idx, deployment in enumerate(deployment_names):
    data = parallel_data[deployment]
    if not data:
        continue
    
    thread_counts = sorted(data.keys())
    means = [np.mean(data[t]) for t in thread_counts]
    stds = [np.std(data[t]) for t in thread_counts]
    
    ax.errorbar(thread_counts, means, yerr=stds, marker='o', markersize=8,
                linewidth=2, capsize=5, capthick=2, color=colors[idx],
                label=deployment, alpha=0.8)

ax.set_xlabel('Thread Count', fontsize=13, fontweight='bold')
ax.set_ylabel('Events per Second', fontsize=13, fontweight='bold')
ax.set_title('Parallel Scaling Comparison - All Deployments', fontsize=15, fontweight='bold')
ax.legend(fontsize=11, loc='best')
ax.grid(True, alpha=0.3)
if parallel_data[deployment_names[0]]:
    ax.set_xticks(sorted(parallel_data[deployment_names[0]].keys()))

plt.tight_layout()
plt.savefig(results_dir / 'parallel_performance_combined.png', dpi=300, bbox_inches='tight')
print(f"✓ Combined parallel performance graph saved to: {results_dir / 'parallel_performance_combined.png'}")

# Print summary statistics
print("\n" + "="*80)
print("PARALLEL SCALING SUMMARY")
print("="*80)

for deployment in deployment_names:
    data = parallel_data[deployment]
    if not data:
        print(f"\n{deployment}: No parallel scaling data found")
        continue
    
    print(f"\n{deployment}:")
    thread_counts = sorted(data.keys())
    
    for t in thread_counts:
        events = data[t]
        mean_events = np.mean(events)
        std_events = np.std(events)
        
        if t == 1:
            print(f"  {t} Thread:  {mean_events:9.2f} ± {std_events:6.2f} events/sec (baseline)")
            baseline = mean_events
        else:
            speedup = mean_events / baseline
            efficiency = (speedup / t) * 100
            print(f"  {t} Threads: {mean_events:9.2f} ± {std_events:6.2f} events/sec | "
                  f"Speedup: {speedup:.2f}x | Efficiency: {efficiency:.1f}%")

print("\n" + "="*80)
print("KEY INSIGHTS:")
print("="*80)

for deployment in deployment_names:
    data = parallel_data[deployment]
    if not data or len(data) < 2:
        continue
    
    thread_counts = sorted(data.keys())
    if 1 not in thread_counts:
        continue
    
    baseline = np.mean(data[1])
    max_threads = thread_counts[-1]
    max_perf = np.mean(data[max_threads])
    speedup = max_perf / baseline
    efficiency = (speedup / max_threads) * 100
    
    print(f"\n{deployment}:")
    print(f"  Best speedup: {speedup:.2f}x with {max_threads} threads")
    print(f"  Parallel efficiency: {efficiency:.1f}%")
    
    # Check for scaling degradation
    if len(thread_counts) > 2:
        perf_2_threads = np.mean(data[2])
        speedup_2 = perf_2_threads / baseline
        if speedup < speedup_2 * 1.1:  # Less than 10% improvement
            print(f"  ⚠️  Scaling plateaus after 2 threads")

print("\n" + "="*80)
