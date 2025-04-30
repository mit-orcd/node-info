# node-info
Code for fetching node information

**NOTES**
- Does not include nodes that are in a "drained*" state
- PDSH command does not always successfully get data from 100% of GPU nodes
  (either due to issues with ssh or nvidia-smi)

<!-- 
TODO:
- Make GPU and CPU memory syntax consistent (change to GB) X
- Docs tables:
  - Change sockets/cores to "2x32" X
  - Remove OS X
  - Remove sched_mit_hill X
  - Add mit_quicktest X
  - Change width of some columns
  - Add special features X
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

## Step 2: Generate tables for Confluence

```bash
sh confluence_data/create_confluence_tables.sh
```

This creates `confluence_data/data/cpu_node_summary.csv` and
`confluence_data/data/gpu_node_summary.csv`, which are used for ORCD's internal
node inventory Wiki, found
[here](https://wikis.mit.edu/confluence/pages/viewpage.action?pageId=290272243).
These tables are also used for generating the orcd-docs tables.

## Step 3: Generate tables for public ORCD docs

Note: Cannot run this script on its own. Must generate Confluence tables first.

```bash
sh orcd_docs_data/create_docs_tables.sh
```

This creates one table for each public partition on Engaging, located in
`orcd_docs_data/data`. There is a `.csv` and `.txt` version for each table. The
`.txt` version can be copied and pasted into the ORCD docs `.md` files.
