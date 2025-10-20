#!/usr/bin/env python3
# Multiway bubble-sort state graph (no Jupyter required)

import argparse
from itertools import permutations
import math
import sys

try:
    import networkx as nx
except ImportError:
    print("Please install networkx:  pip install networkx", file=sys.stderr)
    sys.exit(1)

def inversions(t):
    inv = 0
    for i in range(len(t)):
        for j in range(i+1, len(t)):
            if t[i] > t[j]:
                inv += 1
    return inv

def bubble_neighbors(t):
    t = list(t)
    for i in range(len(t)-1):
        if t[i] > t[i+1]:
            q = t.copy()
            q[i], q[i+1] = q[i+1], q[i]
            yield tuple(q)

def states_from_n(n):
    return list(permutations(range(1, n+1)))

def states_from_values(values):
    # allow duplicates: use set to dedupe equal permutations
    return sorted(set(permutations(values)))

def multiway_bubble(states):
    G = nx.DiGraph()
    G.add_nodes_from(states)
    for p in states:
        for q in bubble_neighbors(p):
            G.add_edge(p, q)
    return G

def layered_layout_by_inversions(G):
    """Layer nodes by inversion count so edges flow downward."""
    levels = {}
    for node in G.nodes():
        levels.setdefault(inversions(node), []).append(node)
    # sort levels descending by inv count
    sorted_levels = sorted(levels.items(), key=lambda kv: -kv[0])
    pos = {}
    for yi, (inv, nodes) in enumerate(sorted_levels):
        m = len(nodes)
        xs = [i - (m-1)/2 for i in range(m)]
        y = -yi
        for x, node in zip(xs, nodes):
            pos[node] = (x, y)
    return pos

def main():
    p = argparse.ArgumentParser(description="Multiway graph for bubble sort (states = permutations).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("-n", type=int, help="Size n; states are permutations of 1..n")
    g.add_argument("--values", type=str, help="Comma-separated values (supports duplicates), e.g. 3,1,1,2")

    p.add_argument("--graphml", default=None, help="Output GraphML path (default: multiway_bubble_n{n}.graphml or _vals.graphml)")
    p.add_argument("--png", default=None, help="Optional PNG path to render layout (headless; requires matplotlib)")
    args = p.parse_args()

    if args.n is not None:
        states = states_from_n(args.n)
        graphml_path = args.graphml or f"multiway_bubble_n{args.n}.graphml"
        sorted_state = tuple(range(1, args.n+1))
        max_inv = args.n * (args.n - 1) // 2
    else:
        values = tuple(int(x.strip()) for x in args.values.split(","))
        states = states_from_values(values)
        graphml_path = args.graphml or "multiway_bubble_vals.graphml"
        sorted_state = tuple(sorted(values))
        # upper bound still (#pairs), but duplicates reduce actual max
        max_inv = sum(1 for i in range(len(values)) for j in range(i+1, len(values)) if values[i] > values[j])

    print(f"States: {len(states)}")

    G = multiway_bubble(states)

    is_dag = nx.is_directed_acyclic_graph(G)
    sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"Nodes: {G.number_of_nodes()}  Edges: {G.number_of_edges()}")
    print(f"DAG: {is_dag}  Sources: {len(sources)}  Sinks: {len(sinks)}")
    print(f"Max inversions (upper bound on longest path): {max_inv}")
    if sorted_state in G:
        print(f"Sorted state present: {sorted_state}  Sink? {sorted_state in sinks}")

    # Write GraphML (portable)
    nx.write_graphml(G, graphml_path)
    print(f"Wrote GraphML -> {graphml_path}")

    # Optional PNG
    if args.png:
        try:
            import matplotlib
            matplotlib.use("Agg")  # headless
            import matplotlib.pyplot as plt
            pos = layered_layout_by_inversions(G)
            plt.figure(figsize=(10, 8))
            nx.draw_networkx_nodes(G, pos, node_size=400)
            nx.draw_networkx_labels(G, pos,
                labels={n:"".join(map(str,n)) for n in G.nodes()},
                font_size=8)
            nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='-|>', arrowsize=10, width=0.8)
            plt.axis('off'); plt.tight_layout()
            plt.savefig(args.png, dpi=180)
            plt.close()
            print(f"Wrote PNG -> {args.png}")
        except ImportError:
            print("matplotlib not installed; skipped PNG. Install with: pip install matplotlib")

if __name__ == "__main__":
    main()
