"""Deterministic layered layout for process map (DFG) visualization."""

from __future__ import annotations

import math
from collections import deque

import networkx as nx
import pandas as pd


def build_process_graph(
    activity_freq: pd.DataFrame,
    transition_freq: pd.DataFrame,
    start_activities: pd.DataFrame,
    end_activities: pd.DataFrame,
) -> nx.DiGraph:
    """Build a directed process graph from DFG data.

    Parameters
    ----------
    activity_freq : pd.DataFrame
        Columns: ``activity``, ``frequency``.
    transition_freq : pd.DataFrame
        Columns: ``source``, ``target``, ``frequency``.
    start_activities : pd.DataFrame
        Columns: ``activity``, ``frequency``.
    end_activities : pd.DataFrame
        Columns: ``activity``, ``frequency``.

    Returns
    -------
    nx.DiGraph
        Graph with START, FINISH, and activity nodes.
    """
    G = nx.DiGraph()

    # Activity nodes
    for _, row in activity_freq.iterrows():
        G.add_node(
            row["activity"],
            label=row["activity"],
            frequency=int(row["frequency"]),
            node_type="activity",
        )

    # Boundary nodes
    G.add_node("START", label="MULAI", frequency=0, node_type="start")
    G.add_node("FINISH", label="SELESAI", frequency=0, node_type="finish")

    # Transition edges
    for _, row in transition_freq.iterrows():
        G.add_edge(
            row["source"],
            row["target"],
            frequency=int(row["frequency"]),
            edge_type="transition",
        )

    # START -> start activity edges
    for _, row in start_activities.iterrows():
        act = row["activity"]
        if act in G.nodes:
            G.add_edge("START", act, frequency=int(row["frequency"]), edge_type="start")

    # End activity -> FINISH edges
    for _, row in end_activities.iterrows():
        act = row["activity"]
        if act in G.nodes:
            G.add_edge(act, "FINISH", frequency=int(row["frequency"]), edge_type="finish")

    return G


def _bfs_ranks(graph: nx.DiGraph) -> dict[str, int]:
    """Assign BFS ranks to graph nodes starting from ``START``.

    Unreachable nodes are placed at a middle rank.  ``FINISH`` is
    forced to be the last rank.

    Parameters
    ----------
    graph : nx.DiGraph
        Process graph.

    Returns
    -------
    dict[str, int]
        Mapping from node id to rank.
    """
    ranks: dict[str, int] = {}

    if "START" in graph:
        queue: deque[str] = deque(["START"])
        ranks["START"] = 0
        while queue:
            node = queue.popleft()
            for succ in graph.successors(node):
                new_rank = ranks[node] + 1
                if succ not in ranks or new_rank < ranks[succ]:
                    ranks[succ] = new_rank
                    queue.append(succ)

    activity_ranks = [r for n, r in ranks.items() if n not in ("START", "FINISH")]
    max_rank = max(activity_ranks) if activity_ranks else 0

    if "FINISH" in graph:
        ranks["FINISH"] = max(ranks.get("FINISH", max_rank + 1), max_rank + 1)

    if ranks:
        mid_rank = max(ranks.values()) // 2
    else:
        mid_rank = 0

    for node in graph.nodes:
        if node not in ranks:
            ranks[node] = mid_rank

    return ranks


def calculate_layered_layout(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Compute a deterministic left-to-right layered layout.

    Nodes are assigned ranks by shortest-path distance from START.
    Within each rank, nodes are sorted by frequency (descending)
    so the most frequent activity appears first.

    Parameters
    ----------
    graph : nx.DiGraph
        Process graph built by :func:`build_process_graph`.

    Returns
    -------
    dict[str, tuple[float, float]]
        Mapping from node id to ``(x, y)`` coordinates.
    """
    if "START" not in graph:
        return {}

    ranks = _bfs_ranks(graph)

    # Group nodes by rank
    rank_groups: dict[int, list[str]] = {}
    for node, rank in ranks.items():
        rank_groups.setdefault(rank, []).append(node)

    # Sort within each rank by frequency descending (deterministic)
    for rank in rank_groups:
        rank_groups[rank].sort(
            key=lambda n: (-graph.nodes[n].get("frequency", 0), n)
        )

    # Assign coordinates
    positions: dict[str, tuple[float, float]] = {}
    total_ranks = max(rank_groups.keys()) + 1 if rank_groups else 1

    for rank, nodes in rank_groups.items():
        x = rank / max(total_ranks - 1, 1)
        n = len(nodes)
        for i, node in enumerate(nodes):
            if n == 1:
                y = 0.0
            else:
                y = (2 * i / (n - 1)) - 1.0  # range [-1, 1]
            positions[node] = (x, y)

    return positions


def _multipartite_layout(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Compute a multipartite layout using BFS ranks as layer keys."""
    ranks = _bfs_ranks(graph)
    # multipartite_layout requires the subset_key attribute on nodes
    nx.set_node_attributes(graph, ranks, "layer")
    pos = nx.multipartite_layout(graph, subset_key="layer", align="vertical")
    return {n: (float(p[0]), float(p[1])) for n, p in pos.items()}


def _spring_layout(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Spring-force layout with START/FINISH nudged to the edges."""
    pos = nx.spring_layout(graph, k=2.0, iterations=50, seed=42)
    out = {n: (float(p[0]), float(p[1])) for n, p in pos.items()}

    xs = [p[0] for n, p in out.items() if n not in ("START", "FINISH")]
    if xs:
        if "START" in out:
            out["START"] = (min(xs) - 0.5, out["START"][1])
        if "FINISH" in out:
            out["FINISH"] = (max(xs) + 0.5, out["FINISH"][1])
    return out


def _shell_layout(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Concentric-shell layout."""
    pos = nx.shell_layout(graph)
    return {n: (float(p[0]), float(p[1])) for n, p in pos.items()}


# Layout name -> implementation function
_LAYOUT_FUNCS = {
    "layered": calculate_layered_layout,
    "multipartite": _multipartite_layout,
    "shell": _shell_layout,
    "spring": _spring_layout,
}

# Fallback chain per requested layout: try in order, stop at first success.
# spring is always last so layered/shell never silently degrade to it.
_FALLBACK_CHAINS = {
    "layered": ["layered", "multipartite", "shell", "spring"],
    "multipartite": ["multipartite", "layered", "shell", "spring"],
    "shell": ["shell", "multipartite", "layered", "spring"],
    "spring": ["spring", "shell", "multipartite", "layered"],
}


def calculate_safe_layout(
    graph: nx.DiGraph,
    requested: str = "layered",
) -> tuple[dict[str, tuple[float, float]], str]:
    """Compute a node layout with a layered -> multipartite -> shell -> spring fallback.

    Per the design rule, the deterministic layered layout is the
    default.  If it fails for any reason, ``networkx.multipartite_layout``
    is tried, then ``networkx.shell_layout``.  ``spring_layout`` is only
    used as a last resort so that the page never crashes.

    Parameters
    ----------
    graph : nx.DiGraph
        Process graph built by :func:`build_process_graph`.
    requested : str, optional
        Preferred layout name.  One of ``"layered"``, ``"multipartite"``,
        ``"shell"``, ``"spring"``.  Defaults to ``"layered"``.

    Returns
    -------
    tuple[dict[str, tuple[float, float]], str]
        ``(positions, layout_used)``.  ``positions`` is empty and
        ``layout_used`` is ``"none"`` only if every layout strategy fails.
    """
    if graph is None or len(graph.nodes) == 0:
        return {}, "none"

    chain = _FALLBACK_CHAINS.get(requested, _FALLBACK_CHAINS["layered"])

    for attempt in chain:
        func = _LAYOUT_FUNCS.get(attempt)
        if func is None:
            continue
        try:
            pos = func(graph)
        except Exception:
            continue
        if pos:
            return pos, attempt

    return {}, "none"


def scale_node_size(
    frequency: int,
    min_freq: int = 1,
    max_freq: int = 1,
    min_size: int = 18,
    max_size: int = 55,
) -> int:
    """Map activity frequency to a node marker size using log scaling.

    Parameters
    ----------
    frequency : int
        Activity frequency.
    min_freq : int
        Minimum frequency in the dataset.
    max_freq : int
        Maximum frequency in the dataset.
    min_size : int
        Minimum marker size.
    max_size : int
        Maximum marker size.

    Returns
    -------
    int
        Marker size in pixels.
    """
    if max_freq <= min_freq or frequency <= 0:
        return min_size
    log_min = math.log(max(min_freq, 1))
    log_max = math.log(max(max_freq, 1))
    log_freq = math.log(max(frequency, 1))
    if log_max <= log_min:
        return min_size
    t = (log_freq - log_min) / (log_max - log_min)
    return int(min_size + (max_size - min_size) * max(0.0, min(1.0, t)))


def scale_edge_width(
    frequency: int,
    min_freq: int = 1,
    max_freq: int = 1,
    min_width: float = 1.0,
    max_width: float = 8.0,
) -> float:
    """Map transition frequency to an edge width using log scaling.

    Parameters
    ----------
    frequency : int
        Transition frequency.
    min_freq : int
        Minimum frequency in the dataset.
    max_freq : int
        Maximum frequency in the dataset.
    min_width : float
        Minimum edge width.
    max_width : float
        Maximum edge width.

    Returns
    -------
    float
        Edge width.
    """
    if max_freq <= min_freq or frequency <= 0:
        return min_width
    log_min = math.log(max(min_freq, 1))
    log_max = math.log(max(max_freq, 1))
    log_freq = math.log(max(frequency, 1))
    if log_max <= log_min:
        return min_width
    t = (log_freq - log_min) / (log_max - log_min)
    return min_width + (max_width - min_width) * max(0.0, min(1.0, t))
