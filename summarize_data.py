"""
This script takes information from all_nodes.csv and creates a summarized chart
(as a CSV) showing node information for CPU-only nodes. The resulting file is
saved to the `cpu` directory.

NOTES:
- Does not include partition: sched_system_all
TO FIX:
- bad rows still have more values and are formatted slightly differently even
  after fixing the multi-node issue. Need to put the nodes in these rows into
  a separate list
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


def clean_table(df):
    """
    Performs cleaning operations on the node table
    """
    # Filter out nodes with GPUs:
    df = df[df["GRES"] == "(null)"]
    # Filter out sched_system_all:
    df = df[df["PARTITION"] != "sched_system_all"]
    return df


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


def main():
    nodes_filename = "all_nodes.csv"
    nodes_path = os.path.join(os.path.dirname(WORKDIR), nodes_filename)
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
    nodes_df = clean_table(nodes_df)
    # Group table:
    grouped_df = nodes_df.groupby(["PARTITION", "OS", "CPUS", "MEMORY"]).agg({
        "NODELIST": lambda x: ";".join(x),
        "OTHER": "count"
    }).rename(columns={"OTHER": "COUNT"}).reset_index()
    # Compress nodelist:
    grouped_df["NODELIST"] = grouped_df["NODELIST"].apply(compress_nodelist)
    # Reorder columns:
    cols = ["PARTITION", "COUNT", "CPUS", "MEMORY", "OS", "NODELIST"]
    grouped_df = grouped_df[cols]
    # Save grouped dataframe as CSV:
    grouped_df.to_csv(os.path.join(WORKDIR, "cpu_node_summary.csv"),
                      index=False)

    return


if __name__ == "__main__":
    main()
