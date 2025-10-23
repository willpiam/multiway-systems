#!/usr/bin/env python3
# Multiway bubble-sort state graph with duplicates allowed (indistinguishable equal entries).
# Nodes are unique value-sequences only (no hidden IDs), so histories merge whenever sequences coincide.

import argparse
from itertools import permutations
import sys

try:
    import networkx as nx
except ImportError:
    print("Please install networkx:  pip install networkx", file=sys.stderr)
    sys.exit(1)

def parse_values(s: str):
    try:
        return tuple(int(x.strip()) for x in s.split(",") if x.strip() != "")
    except ValueError:
        print("Could not parse --values. Example: 3,1,1,2", file=sys.stderr)
        sys.exit(2)

def unique_permutations(values):
    # Generate all distinct permutations of a multiset of integers
    # (simple and clear; fast enough up to moderate sizes)
    return sorted(set(permutations(values)))

def inversions(t):
    inv = 0
    for i in range(len(t)):
        for j in range(i+1, len(t)):
            if t[i] > t[j]:
                inv += 1
    return inv

def bubble_neighbors(t):
    """Yield all one-step bubble-sort successors (swap any adjacent out-of-order pair).
       NOTE: If neighbors are equal, there's no edge (swapping equal items would yield the same state)."""
    t = list(t)
    for i in range(len(t)-1):
        if t[i] > t[i+1]:  # strictly out of order only
            q = t.copy()
            q[i], q[i+1] = q[i+1], q[i]
            yield tuple(q)

def build_multiway(states):
    """Build the multiway graph from all given initial states (distinct sequences)."""
    G = nx.DiGraph()
    G.add_nodes_from(states)
    # Add every applicable bubble step from each state
    for p in states:
        for q in bubble_neighbors(p):
            G.add_edge(p, q)
    return G

def layered_layout_by_inversions(G):
    """Place nodes in horizontal layers by inversion count (top = most inversions → bottom = 0)."""
    levels = {}
    for node in G.nodes():
        inv = inversions(node)
        levels.setdefault(inv, []).append(node)
    pos = {}
    for y, inv in enumerate(sorted(levels.keys(), reverse=True)):
        row = levels[inv]
        row.sort()
        m = len(row)
        xs = [i - (m-1)/2 for i in range(m)]
        for x, node in zip(xs, row):
            pos[node] = (x, -y)
    return pos

def main():
    ap = argparse.ArgumentParser(
        description="Multiway graph for bubble sort with duplicates allowed (equal entries indistinguishable)."
    )
    ap.add_argument("--values", required=True,
                    help="Comma-separated values (supports duplicates), e.g. 3,1,1,2")
    ap.add_argument("--graphml", default="bubble_with_duplicates.graphml",
                    help="Output GraphML path (default: bubble_with_duplicates.graphml)")
    ap.add_argument("--png", default=None,
                    help="Optional PNG path to render a layered layout (headless; requires matplotlib)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="Scale factor for PNG figure size (default: 1.0)")
    ap.add_argument("--node-color", default="#9ecae1",
                    help="Node color for PNG (matplotlib color, default: a light blue)")
    args = ap.parse_args()

    values = parse_values(args.values)

    # Initial condition: ALL distinct configurations of the multiset (as per your spec)
    states = unique_permutations(values)
    print(f"Input values: {values}")
    print(f"Distinct configurations (nodes before edges): {len(states)}")

    G = build_multiway(states)

    is_dag = nx.is_directed_acyclic_graph(G)
    sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"Nodes: {G.number_of_nodes()}  Edges: {G.number_of_edges()}")
    print(f"DAG: {is_dag}  Sources: {len(sources)}  Sinks: {len(sinks)}")

    sorted_state = tuple(sorted(values))
    print(f"Sorted state: {sorted_state}  Present: {sorted_state in G}  Sink? {sorted_state in sinks}")

    nx.write_graphml(G, args.graphml)
    print(f"Wrote GraphML -> {args.graphml}")

    if args.png:
        try:
            import matplotlib
            matplotlib.use("Agg")  # headless-safe
            import matplotlib.pyplot as plt
            pos = layered_layout_by_inversions(G)
            # Validate scale
            scale = args.scale if args.scale and args.scale > 0 else 1.0
            base_w, base_h = 10, 8
            plt.figure(figsize=(base_w * scale, base_h * scale))
            nx.draw_networkx_nodes(G, pos, node_size=400, node_color=args.node_color)
            nx.draw_networkx_labels(G, pos,
                labels={n:"".join(map(str,n)) for n in G.nodes()}, font_size=8)
            nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='-|>', arrowsize=10, width=0.8)
            plt.axis('off'); plt.tight_layout()
            plt.savefig(args.png, dpi=180)
            plt.close()
            print(f"Wrote PNG -> {args.png}")
        except ImportError:
            print("matplotlib not installed; skipped PNG. Install with: pip install matplotlib")

if __name__ == "__main__":
    main()
