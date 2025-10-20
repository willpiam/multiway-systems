#!/usr/bin/env python3
# bubble2.py — Multiway bubble-sort graph "starting from all states"
# - Adds a synthetic super-source node that points to *every* state
# - Works with distinct values (-n N) or explicit lists with duplicates (--values 3,1,1,2)
# - Exports GraphML (portable) and optional PNG (headless-safe)

import argparse, sys
from itertools import permutations

try:
    import networkx as nx
except ImportError:
    print("Please install networkx:  pip install networkx", file=sys.stderr)
    sys.exit(1)

SUPER = "__START__"

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
    # allow duplicates; dedupe equal permutations
    return sorted(set(permutations(values)))

def multiway_bubble(states):
    """Edges point from state -> result of one bubble step (reduces inversions)."""
    G = nx.DiGraph()
    G.add_nodes_from(states)
    for p in states:
        for q in bubble_neighbors(p):
            G.add_edge(p, q)
    return G

def add_super_source(G, states):
    """Add a single super-source with edges to *all* states (visual only)."""
    G.add_node(SUPER)
    for s in states:
        G.add_edge(SUPER, s)

def layered_layout_all_start(G):
    """
    Place SUPER at the top, then layer real states by inversion count
    (higher inversion count higher up). This makes edges flow downward.
    """
    pos = {}
    # Top: the visual super-source
    if SUPER in G:
        pos[SUPER] = (0, 1.5)

    # Group real nodes by inversion count
    levels = {}
    for node in G.nodes():
        if node == SUPER:
            continue
        inv = inversions(node)
        levels.setdefault(inv, []).append(node)

    # Sort levels: highest inversion at the top
    sorted_levels = sorted(levels.items(), key=lambda kv: -kv[0])

    # Spread nodes horizontally within each level
    for yi, (inv, nodes) in enumerate(sorted_levels):
        m = len(nodes)
        xs = [i - (m - 1) / 2 for i in range(m)]
        y = 1 - yi  # start just under the super-source and go downward
        for x, node in zip(xs, nodes):
            pos[node] = (x, y)
    return pos

def main():
    p = argparse.ArgumentParser(description="Multiway bubble-sort graph starting from *all* states.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("-n", type=int, help="Size n; states are permutations of 1..n (distinct values).")
    g.add_argument("--values", type=str, help="Comma-separated values (supports duplicates), e.g. 3,1,1,2")

    p.add_argument("--graphml", default=None, help="Output GraphML (default: bubble2_n{n}.graphml or bubble2_vals.graphml)")
    p.add_argument("--png", default=None, help="Optional PNG render (headless; requires matplotlib)")
    p.add_argument("--no-super", action="store_true", help="Disable super-source (advanced)")

    args = p.parse_args()

    if args.n is not None:
        states = states_from_n(args.n)
        graphml_path = args.graphml or f"bubble2_n{args.n}.graphml"
        sorted_state = tuple(range(1, args.n + 1))
        label = f"n={args.n}"
    else:
        values = tuple(int(x.strip()) for x in args.values.split(","))
        states = states_from_values(values)
        graphml_path = args.graphml or "bubble2_vals.graphml"
        sorted_state = tuple(sorted(values))
        label = f"values={values}"

    print(f"States (all initial conditions): {len(states)}  [{label}]")

    # Build the bubble-step multiway graph
    G = multiway_bubble(states)

    # Add super-source so the visualization clearly "starts from all states"
    if not args.no_super:
        add_super_source(G, states)

    # Basic stats
    is_dag = nx.is_directed_acyclic_graph(G)
    sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"Nodes: {G.number_of_nodes()}  Edges: {G.number_of_edges()}")
    print(f"DAG: {is_dag}  Sources: {len(sources)}  Sinks: {len(sinks)}")
    if sorted_state in G and sorted_state in sinks:
        print(f"Sorted state {sorted_state} is a sink (as expected).")

    # Export GraphML (portable)
    nx.write_graphml(G, graphml_path)
    print(f"Wrote GraphML -> {graphml_path}")

    # Optional PNG (headless)
    if args.png:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            pos = layered_layout_all_start(G)
            plt.figure(figsize=(11, 9))
            # Node styling
            real_nodes = [n for n in G.nodes() if n != SUPER]
            node_labels = {n: "".join(map(str, n)) for n in real_nodes}
            # draw real nodes
            nx.draw_networkx_nodes(G, pos, nodelist=real_nodes, node_size=420)
            nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)
            # draw super-source distinctly if present
            if SUPER in G:
                nx.draw_networkx_nodes(G, pos, nodelist=[SUPER], node_size=700)
                nx.draw_networkx_labels(G, pos, labels={SUPER: "ALL STARTS"}, font_size=9)
            # edges
            nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='-|>', arrowsize=10, width=0.8)
            plt.axis('off'); plt.tight_layout()
            plt.savefig(args.png, dpi=180); plt.close()
            print(f"Wrote PNG -> {args.png}")
        except ImportError:
            print("matplotlib not installed; skipped PNG (pip install matplotlib)")

if __name__ == "__main__":
    # Lazy import here to keep error messages clean
    import networkx as nx
    main()
