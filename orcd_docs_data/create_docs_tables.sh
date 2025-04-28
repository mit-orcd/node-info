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

# Put all node names into a file:
NODE_INFO_PATH="/home/secorey/projects/resource_chart/node-info/confluence_data/data/all_nodes.csv"
cat $NODE_INFO_PATH | awk -F , '{print $2}' | grep -v "NODELIST" | sort | uniq > tmp/hostname.all
# Get CPU specs for all nodes (used in ORCD docs table, not Confluence):
pdsh -u 30 -w ^tmp/hostname.all lscpu | grep -E 'Model name|Core\(s\) per socket|Socket\(s\)' > tmp/cpu_info.txt
# Convert cpu_info.txt to cpu_info.csv:
sed 's/:/,/g; s/, */,/g; s/ *,/,/g; s/(//g; s/)//g' "tmp/cpu_info.txt" > "tmp/cpu_info.csv"

python create_docs_tables.py

for file in $WORKDIR/data/orcd_docs_node_info*.csv; do
    base_filename=$WORKDIR/data/$(basename "$file" .csv)
    csv2md ${base_filename}.csv > ${base_filename}.txt
done
