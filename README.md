# node-info
Code for fetching node information

## Step 1: Install requirements

```bash
# Create a conda environment:
module load miniforge
conda create -n node_info
conda install --file requirements.txt

# Download and install pdsh:
git clone git@github.com:chaos/pdsh.git

```

## Step 1: Pull node information via Slurm

```bash
# All nodes:
sinfo -o %P,%N,%c,%m,%G,%f > all_nodes.csv
# List of nodes with GPUs:
sinfo -p sched_system_all -N -o %N,%G |grep gpu |awk -F , '{print $1}' > hostname.gpu
# GPU specs for GPU nodes:
pdsh ... ##
```

## Step 3: Summarize node information for CPU and GPU nodes

This creates `cpu_node_summary.csv` within the `cpu` directory.
```bash
python summarize_data.py
```
