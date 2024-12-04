"""
This script takes information from all_nodes.csv and gpu_info.csv and creates a
summarized chart (as a CSV) showing node information for CPU-only nodes and GPU-
only nodes.

NOTES:
- Does not include partition: sched_system_all
- Some rows returned by slurm (in the all_nodes.csv file) contain multiple nodes
  and do not contain values that are informative. For now, these rows are
  dropped, but this may result in missing node information in the final result.
"""

import pandas as pd
import csv
import os

WORKDIR = os.path.dirname(os.path.abspath(__file__))

def process_bad_row(row):
    """
    Processes rows that are in a strange format

    E.g.:
      Inputs:
        ['sched_bu_rebbi',
         'node[017-018',
         '045',
         '064',
         '109-111]',
         '1',
         '1',
         '(null)',
         '(null)']
      Returns: 
        ['sched_bu_rebbi',
         'node[017-018;045;064;109-111]',
         '(null)',
         '(null)',
         '(null)',
         '(null)']
    """
    for i, val in enumerate(row):
        if "node[" in val:
            begin_i = i
        if "]" in val:
            end_i = i
    node_list = ";".join(row[begin_i:end_i + 1])

    new_row = []
    for i, val in enumerate(row):
        if i == begin_i:
            new_row.append(node_list)
        elif i > begin_i and i <= end_i:
            continue
        elif i > end_i:
            # Values after node list are not informative, so change to (null)
            new_row.append("(null)")
        else:
            new_row.append(val)
    return new_row


def clean_and_split(df):
    """
    Performs cleaning operations on the node table
    """
    # Filter out sched_system_all:
    df = df[df["PARTITION"] != "sched_system_all"]
    # Split into CPU and GPU:
    cpu_df = df[df["GRES"] == "(null)"]
    gpu_df = df[df["GRES"] != "(null)"]
    return cpu_df, gpu_df


def compress_nodelist(nodelist):
    """
    Change the format of the NODELIST column.

    E.g.:
        "node001;node002;node003;node006" --> "node001-003;node006"
    """
    nodes = nodelist.split(';')
    nodes.sort()
    result = []
    i = 0

    while i < len(nodes):
        start = nodes[i]
        while i + 1 < len(nodes) and \
            int(nodes[i + 1][4:]) == int(nodes[i][4:]) + 1:
            i += 1
        end = nodes[i]
        if start != end:
            result.append(f"{start[:4]}{start[4:]}-{end[4:]}")
        else:
            result.append(start)
        i += 1

    return ';'.join(result)


def summarize_cpu(cpu_df):
    """
    Group the CPU dataframe.
    """
    # Group table:
    grouped_df = cpu_df.groupby(["PARTITION", "OS", "CPUS", "MEMORY"]).agg({
        "NODELIST": lambda x: ";".join(x),
        "OTHER": "count"
    }).rename(columns={"OTHER": "COUNT"}).reset_index()
    # Compress nodelist:
    grouped_df["NODELIST"] = grouped_df["NODELIST"].apply(compress_nodelist)
    # Reorder columns:
    cols = ["PARTITION", "COUNT", "CPUS", "MEMORY", "OS", "NODELIST"]
    return grouped_df[cols]


def join_gpu_info(gpu_df):
    """
    Joins a GPU node dataframe with GPU information
    """
    # Pull GPU info data:
    cols = ["NODELIST", "GPU_TYPE", "GPU_MEMORY"]
    gpu_info_df = pd.read_csv(os.path.join(WORKDIR, "gpu_info.csv"),
                              header=None, names=cols)
    # Reformat:
    gpu_info_df = gpu_info_df.groupby(["NODELIST", "GPU_TYPE", "GPU_MEMORY"])\
        .agg(GPU_COUNT=pd.NamedAgg(column="NODELIST", aggfunc="count"))\
        .reset_index()
    # Join with GPU node info:
    joined_df = pd.merge(gpu_df, gpu_info_df, on="NODELIST", how="outer")
    return joined_df


def summarize_gpu(gpu_df):
    """
    Add GPU information to GPU data frame and group the rows.
    """
    # Join GPU node df with GPU info:
    gpu_df = join_gpu_info(gpu_df)

    # Group table:
    grouped_df = gpu_df.groupby(["PARTITION", "CPUS", "MEMORY", "OS",
                                 "GPU_COUNT", "GPU_TYPE", "GPU_MEMORY"]).agg({
        "NODELIST": lambda x: ";".join(x),
        "OTHER": "count"
    }).rename(columns={"OTHER": "COUNT"}).reset_index()
    # Compress nodelist:
    grouped_df["NODELIST"] = grouped_df["NODELIST"].apply(compress_nodelist)
    # Change GPU count to int:
    grouped_df["GPU_COUNT"] = grouped_df["GPU_COUNT"].astype(int)
    # Reorder columns:
    cols = ["PARTITION", "COUNT", "CPUS", "MEMORY", "GPU_COUNT", "GPU_TYPE",
            "GPU_MEMORY", "OS", "NODELIST"]
    return grouped_df[cols]


def main():
    # Read data:
    nodes_filename = "all_nodes.csv"
    nodes_path = os.path.join(WORKDIR, nodes_filename)
    with open(nodes_path, "r") as f:
        reader = csv.reader(f)
        headers = next(reader)
        headers.append("OS")
        headers.append("OTHER")
        cleaned_rows = []
        for row in reader:
            # Check if the row contains multiple nodes:
            good_row = True
            for val in row:
                if "node[" in val:
                    good_row = False
            # Fix format of bad rows (skipping bad rows for now):
            if not good_row:
                # new_row = process_bad_row(row)
                continue
            else:
                new_row = row
            # Ensure row is correct length:
            new_row += ["(null)" for _ in range(8 - len(new_row))]
            cleaned_rows.append(new_row)

        nodes_df = pd.DataFrame(cleaned_rows, columns=headers)
    
    # Clean dataframe:
    cpu_df, gpu_df = clean_and_split(nodes_df)
    # Summarize information:
    cpu_df = summarize_cpu(cpu_df)
    gpu_df = summarize_gpu(gpu_df)

    # Save grouped dataframes as CSV:
    cpu_df.to_csv(os.path.join(WORKDIR, "cpu_node_summary.csv"), index=False)
    gpu_df.to_csv(os.path.join(WORKDIR, "gpu_node_summary.csv"), index=False)

    return


if __name__ == "__main__":
    main()
