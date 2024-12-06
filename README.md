# node-info
Code for fetching node information

**NOTES**
- GPU info cannot be gathered when a node is in drain state. Next step is to
create a file that lists the nodes that were not successfully queried so they
can be queried at another time.

## Step 1: Install requirements

```bash
# Create a conda environment:
module load miniforge
conda create -n node_info --file requirements.txt
conda activate node_info

# Download and install pdsh from source:
git clone git@github.com:chaos/pdsh.git
cd pdsh
aclocal
autoconf
libtoolize --automake --copy --force
autoheader
automake --add-missing
./configure --with-ssh --prefix=$HOME/software/lib/pdsh
make
make install
export PATH="$HOME/software/lib/pdsh/bin:$PATH"
export PDSH_RCMD_TYPE=ssh
export PDSH_MODULE_DIR=$HOME/software/lib/pdsh/lib/pdsh
```

## Step 2: Pull node information via Slurm and PDSH

```bash
# All nodes (excluding nodes with "drained*" state):
sinfo -o %P,%N,%c,%m,%G,%f,%T | grep -v "drained\*" > all_nodes.csv
# List of nodes with GPUs:
cat all_nodes.csv | grep gpu | awk -F , '{print $2}' | sort | uniq > hostname.gpu
# GPU specs for GPU nodes (may have to ^C this operation but it will still get data):
pdsh -w ^hostname.gpu nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > gpu_info.txt
# Convert gpu_info.txt to gpu_info.csv:
sed 's/:/,/; s/, */,/g' "gpu_info.txt" > "gpu_info.csv"
# Print nodes that were not successfully queried:
grep -Fxv -f <(awk -F, '{print $1}' gpu_info.csv) hostname.gpu > unchecked_gpu_nodes.txt
# You may need to manually check these nodes
```

## Step 3: Summarize node information for CPU and GPU nodes

```bash
python summarize_data.py
```
This creates `cpu_node_summary.csv` and `gpu_node_summary.csv`.
