#!/bin/bash

module load miniforge
conda activate node_info

WORKDIR="$(dirname "$(realpath "$0")")"
cd $WORKDIR
mkdir -p tmp
mkdir -p data

# Add PDSH to path:
export PATH="$HOME/software/lib/pdsh/bin:$PATH"
export PDSH_RCMD_TYPE="ssh"
export PDSH_MODULE_DIR="$HOME/software/lib/pdsh/lib/pdsh"

# All nodes (excluding nodes with "drained*" or "down*" state):
sinfo -o %P,%N,%c,%m,%G,%T,%f > data/all_nodes.csv
# List of nodes with GPUs:
cat data/all_nodes.csv | grep gpu | awk -F , '{print $2}' | sort | uniq > tmp/hostname.gpu
# GPU specs for GPU nodes (may have to ^C this operation but it will still get data):
pdsh -u 30 -w ^tmp/hostname.gpu nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > tmp/gpu_info.txt
# Convert gpu_info.txt to gpu_info.csv:
sed 's/:/,/; s/, */,/g' "tmp/gpu_info.txt" > "tmp/gpu_info.csv"
# Make note of nodes that were not successfully queried:
awk -F, '{print $1}' tmp/gpu_info.csv > tmp/queried_gpu_nodes.txt
grep -Fxv -f tmp/queried_gpu_nodes.txt tmp/hostname.gpu > data/unchecked_gpu_nodes.txt
# You may need to manually check these nodes

python create_confluence_tables.py
