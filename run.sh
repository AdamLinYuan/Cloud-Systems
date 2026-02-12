#!/bin/bash
 
# --- 1. SETUP & INSTALLATION ---
echo "Update and Install Tools..."
sudo apt-get update -qq
sudo apt-get install -y sysbench fio iperf3 mbw build-essential git -qq
 
# Compile forksum
if [ -f "forksum.c" ]; then
    gcc -o forksum forksum.c
    echo "Forksum compiled."
else
    echo "Error: forksum.c not found! Please upload it first."
    exit 1
fi
 
# Create output file
OUTPUT_FILE="8gb_4core.txt"
echo "Starting Benchmarks - $(date)" > $OUTPUT_FILE
echo "==============================" >> $OUTPUT_FILE
 
# --- 2. CPU SPEED (Sysbench) ---
echo "Running CPU Benchmark (10 iterations)..."
echo "--- CPU Speed ---" >> $OUTPUT_FILE
for i in {1..10}
do
   # Extract only the "events per second" line to keep it clean
   sysbench cpu --cpu-max-prime=500 --threads=1 run | grep "events per second" >> $OUTPUT_FILE
done
 
# --- 3. MEMORY ACCESS (mbw) ---
echo "Running Memory Benchmark (10 iterations)..."
echo "--- Memory Access (MB/s) ---" >> $OUTPUT_FILE
for i in {1..10}
do
   # Test copying a 1024MB array. Grep for the "AVG" speed.
   mbw 1024 | grep "AVG" >> $OUTPUT_FILE
done
 
# --- 4. DISK READ SPEED (fio) ---
echo "Running Disk Read Benchmark (10 iterations)..."
echo "--- Disk Read Speed ---" >> $OUTPUT_FILE
for i in {1..10}
do
   # Run fio and extract the Read Bandwidth (BW) line
   fio --name=fiotest --size=1G --rw=read --runtime=15 --startdelay=2 \
       --direct=1 --bs=1M --iodepth=16 --minimal | awk -F';' '{print "Read BW: " $7 " KB/s"}' >> $OUTPUT_FILE
   # Clean up the generated file to stop disk filling up
   rm -f fiotest.0.0
done
 
# --- 5. NETWORK SPEED (iPerf3) ---
echo "Running Network Benchmark (Localhost loopback)..."
echo "--- Network Speed ---" >> $OUTPUT_FILE
# Start server in background
iperf3 -s -D
sleep 2
for i in {1..5} # Reduced to 5 as network is usually stable
do
   iperf3 -c localhost -t 5 | grep "sender" >> $OUTPUT_FILE
done
# Kill server
pkill iperf3
 
# --- 6. PROCESS SPEED (Forksum) ---
echo "Running Process Spawn Benchmark (10 iterations)..."
echo "--- Process Speed (Forksum) ---" >> $OUTPUT_FILE
for i in {1..10}
do
   # Use built-in time command, capturing output to file
   (time ./forksum 1 500) 2>> $OUTPUT_FILE
done
 
# --- 7. PARALLEL SCALING ---
echo "Running Parallel Scaling (1 to 4 threads)..."
echo "--- Parallel Scaling ---" >> $OUTPUT_FILE
for threads in 1 2 3 4
do
   echo "Threads: $threads" >> $OUTPUT_FILE
   for i in {1..5}
   do
       sysbench cpu --cpu-max-prime=500 --threads=$threads run | grep "events per second" >> $OUTPUT_FILE
   done
done
 
echo "Done! Results saved to $OUTPUT_FILE"