# node-info
Code for fetching node information

## Step 1: Get all node information

```bash
sinfo -o %P,%N,%c,%m,%G,%f > all_nodes.csv
```

## Step 2: Install requirements

```bash
module load miniforge
conda create -n node_info
conda install --file requirements.txt
```

## Step 3: Summarize CPU node information

```bash
python cpu/summarize_data.py
```

## Step 4: Summarize GPU node information

```bash
sinfo -p sched_system_all -N -o %N,%G |grep gpu |awk -F , '{print $1}' > hostname.gpu
```
