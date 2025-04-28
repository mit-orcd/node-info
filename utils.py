# Utility functions

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


def compress_nodelist(nodelist):
    """
    Converts a nodelist string into a list of nodes (reverse of expand_nodelist)

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
