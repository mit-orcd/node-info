# node-info
Code for fetching node information

**NOTES**
- Does not include nodes that are in a "drained*" state
- PDSH command does not always successfully get data from 100% of GPU nodes
  (either due to issues with ssh or nvidia-smi)

<!-- 
TODO:
- Reorganize everything so that the conflunce table information is in one
  dir and the orcd-docs info is in another dir
- Make GPU and CPU memory syntax consistent (add MiB)
- Put things into shell scripts
- Remove intermediate files from github repo (also programmatically delete?)
-->

## Step 1: Install requirements

```bash
# Create a conda environment:
module load miniforge
conda env create -f environment.yml
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

For Confluence table and orcd-docs table:

```bash
# All nodes (excluding nodes with "drained*" state):
sinfo -o %P,%N,%c,%m,%G,%T,%f | grep -v "drained\*" > all_nodes.csv
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

For orcd-docs table only:

```bash
# Put all node names into a file:
cat all_nodes.csv | awk -F , '{print $2}' | grep -v "NODELIST" | sort | uniq > orcd_docs_data/hostname.all
# Get CPU specs for all nodes (used in ORCD docs table, not Confluence):
pdsh -w ^orcd_docs_data/hostname.all lscpu | grep -E 'Model name|Core\(s\) per socket|Socket\(s\)' > orcd_docs_data/cpu_info.txt
# Convert cpu_info.txt to cpu_info.csv:
sed 's/:/,/g; s/, */,/g; s/ *,/,/g; s/(//g; s/)//g' "orcd_docs_data/cpu_info.txt" > "orcd_docs_data/cpu_info.csv"
```

## Step 3: Summarize node information for CPU and GPU nodes (Confluence table and orcd-docs)

```bash
python summarize_data.py
```
This creates `cpu_node_summary.csv` and `gpu_node_summary.csv`, which are used
for ORCD's internal node inventory Wiki, found [here](https://wikis.mit.edu/confluence/pages/viewpage.action?pageId=290272243).

## Step 4: Create tables for orcd-docs

Generate tables:

```bash
python orcd_docs_data/create_table_for_docs.py
```

Convert CSVs to .md table format:

```bash
DIR=orcd_docs_data

for file in $DIR/orcd_docs_node_info*.csv; do
    base_filename=$DIR/$(basename "$file" .csv)
    csv2md $base_filename.csv > $base_filename.txt
done
```
