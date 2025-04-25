"""
This script generates the tables to be used for the public-facing ORCD
documentation.

TODO:
- Include special features of nodes
"""

import pandas as pd
import sys
import os

BASE_DIR = os.path.dirname(__file__)
os.chdir(BASE_DIR)
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, '..')))
import summarize_data

def read_cpu_data():
    """
    Reads and formats the data that was collected from lscpu.
    """

    columns=["NODELIST", "SPEC", "DETAIL"]
    cpu_info_df = pd.read_csv("cpu_info.csv", header=None)
    cpu_info_df.columns = columns
    cpu_info_df = cpu_info_df.pivot_table(
        index="NODELIST",
        columns="SPEC",
        values="DETAIL",
        aggfunc=lambda x: " ".join(x)
    ).reset_index()
    cpu_info_df.columns.name = None
    cpu_info_df.columns = [
        col.upper().replace(" ", "_") for col in cpu_info_df.columns
    ]

    return cpu_info_df


def expand_nodelist(nodelist):
    """
    Converts a nodelist string into a list of nodes

    Example:
    "node1601-1602;node1626-1627" --> ["node1601", "node1602", "node1626",
                                       "node1627"]
    """

    nodelist_converted = []
    ranges = nodelist.split(";")
    for node_range in ranges:
        if "-" not in node_range:
            nodelist_converted.append(node_range)
            continue
        start, end = node_range.split("-")
        start = ''.join(filter(str.isdigit, start))
        n_digits = len(start)
        for i in range(int(start), int(end) + 1):
            nodelist_converted.append(f"node{str(i).zfill(n_digits)}")

    return nodelist_converted


def clean_node_df(node_df, public_partitions):
    # Filter to only public partitions:
    node_df = node_df[node_df["PARTITION"].isin(public_partitions)]

    node_df = node_df[node_df["PARTITION"] != "mit_data_transfer"]
    node_df.loc[:, "NODELIST"] = node_df["NODELIST"].apply(expand_nodelist)
    node_df = node_df.explode("NODELIST").reset_index(drop=True)
    node_df.drop(columns=["NODE_COUNT", "CPUS"], inplace=True)
    return node_df


def main():
    # Define public partitions:
    public_partitions = set(["mit_normal", "mit_normal_gpu", "mit_preemptable",
                             "sched_mit_hill"])

    # Read CPU specs:
    cpu_info_df = read_cpu_data()

    # Clean up node data frame:
    cpu_node_df = pd.read_csv("../cpu_node_summary.csv") # Change the path to this later
    cpu_node_df = clean_node_df(cpu_node_df, public_partitions)
    cpu_node_df = cpu_node_df.merge(cpu_info_df, on="NODELIST", how="left")
    gpu_node_df = pd.read_csv("../gpu_node_summary.csv") # Change the path to this later
    gpu_node_df = clean_node_df(gpu_node_df, public_partitions)
    gpu_node_df = gpu_node_df.merge(cpu_info_df, on="NODELIST", how="left")

    # Compress the two data frames:
    cpu_node_df = cpu_node_df.groupby(
        ["PARTITION", "MEMORY", "OS", "CORES_PER_SOCKET", "SOCKETS",
         "MODEL_NAME"]
    ).agg(
        NODELIST=("NODELIST", lambda x: ";".join(x)),
        NODE_COUNT=("NODELIST", "count")
    ).reset_index()
    gpu_node_df =  gpu_node_df.groupby(
        ["PARTITION", "MEMORY", "OS", "CORES_PER_SOCKET", "SOCKETS",
         "MODEL_NAME", "GPU_COUNT", "GPU_TYPE", "GPU_MEMORY"]
    ).agg(
        NODELIST= ("NODELIST", lambda x: ";".join(x)),
        NODE_COUNT=("NODELIST", "count")
    ).reset_index()
    # Reformat nodelist:
    cpu_node_df["NODELIST"] = cpu_node_df["NODELIST"].apply(
        summarize_data.compress_nodelist
    )
    gpu_node_df["NODELIST"] = gpu_node_df["NODELIST"].apply(
        summarize_data.compress_nodelist
    )

    # Reorder columns:
    cpu_node_df = cpu_node_df[["PARTITION", "NODE_COUNT", "OS",
                                "CORES_PER_SOCKET", "SOCKETS", "MEMORY",
                                "MODEL_NAME", "NODELIST"]]
    gpu_node_df = gpu_node_df[["PARTITION", "NODE_COUNT", "OS",
                               "CORES_PER_SOCKET", "SOCKETS", "MEMORY",
                               "MODEL_NAME", "GPU_COUNT", "GPU_TYPE",
                               "GPU_MEMORY", "NODELIST"]]
    
    # Export the dataframes to csv files (one per partition):
    for partition in public_partitions:
        partition_node_df = gpu_node_df[
            gpu_node_df["PARTITION"] == partition
        ].copy()
        partition_node_df.drop(columns=["PARTITION"], inplace=True)
        if not partition_node_df.empty:
            partition_node_df.to_csv(f"orcd_docs_node_info_gpu_{partition}.csv",
                                     index=False)
        partition_node_df = cpu_node_df[
            cpu_node_df["PARTITION"] == partition
        ].copy()
        partition_node_df.drop(columns=["PARTITION"], inplace=True)
        if not partition_node_df.empty:
            partition_node_df.to_csv(f"orcd_docs_node_info_cpu_{partition}.csv",
                                     index=False)

    return


if __name__ == "__main__":
    main()
