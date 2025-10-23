#!/usr/bin/env python3
# Causal graph for multiway bubble-sort with duplicates allowed (equal entries indistinguishable).
# Events are single bubble swaps (p -> q). Causal edges connect events that chain via the
# same intermediate state (i.e., if e1: p->q and e2: q->r, then e1 -> e2).

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
        for j in range(i + 1, len(t)):
            if t[i] > t[j]:
                inv += 1
    return inv


def bubble_neighbors_with_index(t):
    """Yield all one-step bubble-sort successors (swap any adjacent out-of-order pair),
       as (neighbor_tuple, swap_index). If neighbors are equal, there's no edge.
    """
    t_list = list(t)
    for i in range(len(t_list) - 1):
        if t_list[i] > t_list[i + 1]:  # strictly out of order only
            q = t_list.copy()
            q[i], q[i + 1] = q[i + 1], q[i]
            yield (tuple(q), i)


def build_causal_graph(states):
    """Build the causal graph whose nodes are events (p --swap@i--> q), and edges connect
       event e1: p->q to event e2: q->r whenever e2 consumes the state produced by e1.
    """
    # First enumerate all events and index them
    events = []  # list of dicts with keys: id, source, target, index
    out_events_from_state = {}  # state -> [event_id]
    in_events_to_state = {}     # state -> [event_id]

    next_event_id = 0
    for p in states:
        for q, idx in bubble_neighbors_with_index(p):
            e = {
                "id": next_event_id,
                "source": p,
                "target": q,
                "swap_index": idx,
            }
            events.append(e)
            out_events_from_state.setdefault(p, []).append(next_event_id)
            in_events_to_state.setdefault(q, []).append(next_event_id)
            next_event_id += 1

    G = nx.DiGraph()

    # Add event nodes with useful attributes
    for e in events:
        label = f"{''.join(map(str, e['source']))}→{''.join(map(str, e['target']))} @{e['swap_index']}"
        G.add_node(
            e["id"],
            source_str=",".join(map(str, e["source"])),
            target_str=",".join(map(str, e["target"])),
            swap_index=e["swap_index"],
            label=label,
            source_inversions=inversions(e["source"]),
            target_inversions=inversions(e["target"]),
        )

    # Add causal edges: link events that chain through an intermediate state
    for intermediate_state in states:
        incoming = in_events_to_state.get(intermediate_state, [])
        outgoing = out_events_from_state.get(intermediate_state, [])
        if not incoming or not outgoing:
            continue
        for e1 in incoming:
            for e2 in outgoing:
                # e1: * -> intermediate_state, e2: intermediate_state -> *
                G.add_edge(e1, e2)

    return G


def layered_layout_by_source_inversions(G):
    """Place event nodes in horizontal layers by inversion count of their source state
       (top = most inversions → bottom = 0)."""
    levels = {}
    for node in G.nodes():
        inv = G.nodes[node].get("source_inversions", 0)
        levels.setdefault(inv, []).append(node)
    pos = {}
    for y, inv in enumerate(sorted(levels.keys(), reverse=True)):
        row = levels[inv]
        # Sort deterministically by label
        row.sort(key=lambda n: G.nodes[n].get("label", str(n)))
        m = len(row)
        xs = [i - (m - 1) / 2 for i in range(m)]
        for x, node in zip(xs, row):
            pos[node] = (x, -y)
    return pos


def main():
    ap = argparse.ArgumentParser(
        description="Causal graph for bubble sort with duplicates allowed (events are swaps; edges show causal chaining)."
    )
    ap.add_argument("--values", required=True,
                    help="Comma-separated values (supports duplicates), e.g. 3,1,1,2")
    ap.add_argument("--graphml", default="causal_with_duplicates.graphml",
                    help="Output GraphML path (default: causal_with_duplicates.graphml)")
    ap.add_argument("--png", default=None,
                    help="Optional PNG path to render a layered layout (headless; requires matplotlib)")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="Scale factor for PNG figure size (default: 1.0)")
    ap.add_argument("--node-color", default="#fdd0a2",
                    help="Node color for PNG (matplotlib color, default: a light orange)")
    args = ap.parse_args()

    values = parse_values(args.values)

    # Initial condition: ALL distinct configurations of the multiset (as per your spec)
    states = unique_permutations(values)
    print(f"Input values: {values}")
    print(f"Distinct configurations (states): {len(states)}")

    G = build_causal_graph(states)

    # Basic stats
    num_events = G.number_of_nodes()
    num_causal_edges = G.number_of_edges()
    print(f"Causal events (nodes): {num_events}  Causal edges: {num_causal_edges}")

    # GraphML output
    nx.write_graphml(G, args.graphml)
    print(f"Wrote GraphML -> {args.graphml}")

    # Optional PNG rendering
    if args.png:
        try:
            import matplotlib
            matplotlib.use("Agg")  # headless-safe
            import matplotlib.pyplot as plt
            pos = layered_layout_by_source_inversions(G)
            # Validate scale
            scale = args.scale if args.scale and args.scale > 0 else 1.0
            base_w, base_h = 10, 8
            plt.figure(figsize=(base_w * scale, base_h * scale))
            nx.draw_networkx_nodes(G, pos, node_size=400, node_color=args.node_color)
            nx.draw_networkx_labels(G, pos,
                labels={n: G.nodes[n].get("label", str(n)) for n in G.nodes()}, font_size=7)
            nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='-|>', arrowsize=10, width=0.8)
            plt.axis('off'); plt.tight_layout()
            plt.savefig(args.png, dpi=180)
            plt.close()
            print(f"Wrote PNG -> {args.png}")
        except ImportError:
            print("matplotlib not installed; skipped PNG. Install with: pip install matplotlib")


if __name__ == "__main__":
    main()


