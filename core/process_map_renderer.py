"""Graphviz DOT generator and SVG renderer for the process map.

This module is the rendering layer for the Disco-inspired process
graph produced by :mod:`core.map_abstraction`.  It generates a
human-readable DOT document tailored for a clean left-to-right
process map and can render it to SVG using the system Graphviz
binary.

Design goals:

* Stable left-to-right layout regardless of node count.
* Frequency-driven node sizes and edge widths (log scaling).
* Wrapped activity labels so wide names do not overflow.
* Optional, capped edge labels to keep dense maps readable.
* Stable ``n0``, ``n1`` … node IDs so activity names with quotes,
  arrows or parentheses cannot break DOT syntax.
"""

from __future__ import annotations

import math
from collections import deque

import networkx as nx


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def wrap_label(text: str, max_chars: int = 18) -> str:
    """Wrap a label so each line stays under ``max_chars`` characters.

    Words are kept intact.  A single word longer than ``max_chars``
    sits on its own line.

    Parameters
    ----------
    text : str
        Original label text.
    max_chars : int, optional
        Soft maximum line length, by default 18.

    Returns
    -------
    str
        Wrapped label using ``\n`` as the line separator.
    """
    text = str(text)
    if not text:
        return ""
    if len(text) <= max_chars:
        return text

    words = text.split()
    if not words:
        return text

    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
            continue
        if len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def safe_dot_id(name: str, index: int) -> str:
    """Return a stable DOT-safe node identifier.

    Activity names can contain quotes, arrows, parentheses or
    diacritics.  Using them as raw DOT IDs is fragile, so each node
    receives a synthetic ``n{index}`` ID.

    Parameters
    ----------
    name : str
        Original node name (kept for documentation purposes).
    index : int
        Stable index produced by enumeration order.

    Returns
    -------
    str
        ``"n0"``, ``"n1"`` …
    """
    _ = name  # only used for documentation; index is the real key
    return f"n{int(index)}"


def scale_node_size(
    frequency: int,
    min_size: float = 0.35,
    max_size: float = 0.85,
    min_freq: int = 1,
    max_freq: int = 1,
) -> float:
    """Map an activity frequency to a Graphviz node size in inches.

    Logarithmic scaling so that a few very frequent activities do not
    dwarf the rest of the map.

    Parameters
    ----------
    frequency : int
        Activity frequency.
    min_size : float, optional
        Smallest node size in inches.
    max_size : float, optional
        Largest node size in inches.
    min_freq : int, optional
        Minimum frequency in the dataset.
    max_freq : int, optional
        Maximum frequency in the dataset.

    Returns
    -------
    float
        Node size in inches.
    """
    if frequency <= 0:
        return min_size
    if max_freq <= min_freq:
        return min_size
    log_min = math.log(max(min_freq, 1))
    log_max = math.log(max(max_freq, 1))
    log_freq = math.log(max(frequency, 1))
    if log_max <= log_min:
        return min_size
    t = (log_freq - log_min) / (log_max - log_min)
    t = max(0.0, min(1.0, t))
    return min_size + t * (max_size - min_size)


def scale_edge_width(
    frequency: int,
    min_width: float = 1.0,
    max_width: float = 6.0,
    min_freq: int = 1,
    max_freq: int = 1,
) -> float:
    """Map a transition frequency to a Graphviz edge width.

    Logarithmic scaling.  ``frequency <= 0`` resolves to ``min_width``.

    Parameters
    ----------
    frequency : int
        Transition frequency.
    min_width : float, optional
        Minimum edge width.
    max_width : float, optional
        Maximum edge width.
    min_freq : int, optional
        Minimum frequency in the dataset.
    max_freq : int, optional
        Maximum frequency in the dataset.

    Returns
    -------
    float
    """
    if frequency <= 0:
        return min_width
    if max_freq <= min_freq:
        return min_width
    log_min = math.log(max(min_freq, 1))
    log_max = math.log(max(max_freq, 1))
    log_freq = math.log(max(frequency, 1))
    if log_max <= log_min:
        return min_width
    t = (log_freq - log_min) / (log_max - log_min)
    t = max(0.0, min(1.0, t))
    return min_width + t * (max_width - min_width)


def _scale_edge_weight(
    frequency: int,
    min_freq: int = 1,
    max_freq: int = 1,
    min_weight: int = 1,
    max_weight: int = 10,
) -> int:
    """Map frequency to an integer Graphviz edge weight (log scaling)."""
    if frequency <= 0:
        return min_weight
    if max_freq <= min_freq:
        return min_weight
    log_min = math.log(max(min_freq, 1))
    log_max = math.log(max(max_freq, 1))
    log_freq = math.log(max(frequency, 1))
    if log_max <= log_min:
        return min_weight
    t = (log_freq - log_min) / (log_max - log_min)
    t = max(0.0, min(1.0, t))
    return int(round(min_weight + t * (max_weight - min_weight)))


def _escape_dot(text: str) -> str:
    """Escape a string for safe inclusion inside a DOT double-quoted value."""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def _bfs_ranks(graph: nx.DiGraph) -> dict[str, int]:
    """Assign BFS ranks to every node using ``START`` as the source.

    ``FINISH`` is forced to be the largest rank.  Unreachable nodes
    are placed at the median rank so they still appear on the map.
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


# ----------------------------------------------------------------------
# DOT generation
# ----------------------------------------------------------------------

_SPLINE_MODES = {"spline", "polyline", "ortho", "curved", "line", "false"}


def generate_graphviz_dot(
    graph: nx.DiGraph,
    show_edge_labels: bool = False,
    max_edge_labels: int = 20,
    spline_mode: str = "spline",
) -> str:
    """Build a DOT representation of the process map.

    Parameters
    ----------
    graph : nx.DiGraph
        Graph produced by
        :func:`core.map_abstraction.build_disco_like_graph`.
    show_edge_labels : bool, optional
        When ``True`` the top-frequency edges are annotated with their
        frequency.  Default ``False``.
    max_edge_labels : int, optional
        Upper bound for how many edges may carry a label when
        ``show_edge_labels`` is true.  ``-1`` means "all".  Default 20.
    spline_mode : str, optional
        DOT ``splines`` attribute.  One of ``"spline"``, ``"polyline"``,
        ``"ortho"``.  Defaults to ``"spline"``.

    Returns
    -------
    str
        A DOT document.
    """
    if spline_mode not in _SPLINE_MODES:
        spline_mode = "spline"

    lines: list[str] = []
    add = lines.append

    add("digraph G {")
    # Graph attributes
    add('  rankdir="LR";')
    add('  bgcolor="white";')
    add('  pad="0.6";')
    add('  ranksep="1.8";')
    add('  nodesep="0.9";')
    add(f'  splines="{spline_mode}";')
    add('  overlap="false";')
    add('  sep="+20";')
    add('  esep="+10";')
    add('  margin="0.2";')
    add('  compound="true";')
    add('  concentrate="false";')
    add('  newrank="true";')
    add('  outputorder="edgesfirst";')

    # Default node / edge attributes
    add(
        '  node ['
        'fontname="Arial", fontsize="10", fontcolor="#111111", '
        'margin="0.12,0.08", shape="box", style="rounded,filled", '
        'color="#2B5B9F", fillcolor="#E8F1FF"];'
    )
    add(
        '  edge ['
        'fontname="Arial", fontsize="9", fontcolor="#111111", '
        'color="#555555", arrowsize="0.7"];'
    )

    # ------------------------------------------------------------------
    # Stable IDs
    # ------------------------------------------------------------------
    nodes_in_order = list(graph.nodes(data=True))
    node_id: dict[str, str] = {
        name: safe_dot_id(name, idx) for idx, (name, _) in enumerate(nodes_in_order)
    }

    # ------------------------------------------------------------------
    # Node-size scaling range
    # ------------------------------------------------------------------
    activity_freqs = [
        int(d.get("frequency", 0))
        for _, d in nodes_in_order
        if d.get("node_type") == "activity"
    ]
    pos_freqs = [f for f in activity_freqs if f > 0]
    min_node_freq = min(pos_freqs) if pos_freqs else 1
    max_node_freq = max(pos_freqs) if pos_freqs else 1

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------
    for name, data in nodes_in_order:
        nid = node_id[name]
        ntype = data.get("node_type", "activity")

        if ntype == "start":
            display = data.get("display_label", "MULAI")
            label = _escape_dot(display)
            tooltip = _escape_dot("MULAI: titik awal kasus")
            add(
                f'  {nid} [label="{label}", shape="circle", style="filled", '
                f'fillcolor="#2ECC71", color="#1B8E4B", fontcolor="#111111", '
                f'width="0.55", height="0.55", fixedsize="true", '
                f'tooltip="{tooltip}"];'
            )
        elif ntype == "finish":
            display = data.get("display_label", "SELESAI")
            label = _escape_dot(display)
            tooltip = _escape_dot("SELESAI: titik akhir kasus")
            add(
                f'  {nid} [label="{label}", shape="circle", style="filled", '
                f'fillcolor="#E74C3C", color="#A93226", fontcolor="#111111", '
                f'width="0.65", height="0.65", fixedsize="true", '
                f'tooltip="{tooltip}"];'
            )
        else:
            display = data.get("display_label", data.get("label", name))
            freq = int(data.get("frequency", 0))
            wrapped = wrap_label(display)
            label_text = f"{wrapped}\nfreq: {freq}"
            label = _escape_dot(label_text)
            tooltip = _escape_dot(f"Aktivitas: {display}\nFrekuensi: {freq}")
            size = scale_node_size(
                freq,
                min_freq=min_node_freq,
                max_freq=max_node_freq,
            )
            add(
                f'  {nid} [label="{label}", '
                f'width="{size:.2f}", height="{size:.2f}", '
                f'tooltip="{tooltip}"];'
            )

    # ------------------------------------------------------------------
    # Rank groups
    # ------------------------------------------------------------------
    ranks = _bfs_ranks(graph)

    # Force START at source rank, FINISH at sink rank
    if "START" in graph:
        add(f'  {{ rank=source; {node_id["START"]}; }}')
    if "FINISH" in graph:
        add(f'  {{ rank=sink; {node_id["FINISH"]}; }}')

    rank_groups: dict[int, list[str]] = {}
    for name, rank in ranks.items():
        if name in ("START", "FINISH"):
            continue
        rank_groups.setdefault(rank, []).append(name)

    for rank, names in sorted(rank_groups.items()):
        if len(names) <= 1:
            continue
        # Sort by frequency descending (deterministic)
        names_sorted = sorted(
            names,
            key=lambda n: (-int(graph.nodes[n].get("frequency", 0)), n),
        )
        ids = "; ".join(node_id[n] for n in names_sorted)
        add(f"  {{ rank=same; {ids}; }}")

    # ------------------------------------------------------------------
    # Edges
    # ------------------------------------------------------------------
    edges = list(graph.edges(data=True))
    if edges:
        edge_freqs = [int(d.get("frequency", 0)) for _, _, d in edges]
        pos_edge_freqs = [f for f in edge_freqs if f > 0]
        min_edge_freq = min(pos_edge_freqs) if pos_edge_freqs else 1
        max_edge_freq = max(pos_edge_freqs) if pos_edge_freqs else 1

        # Decide which edges are labeled
        label_keys: set[tuple[str, str]] = set()
        if show_edge_labels:
            ordered = sorted(
                edges,
                key=lambda e: (
                    -int(e[2].get("frequency", 0)),
                    str(e[0]),
                    str(e[1]),
                ),
            )
            if max_edge_labels < 0:
                limit = len(ordered)
            else:
                limit = max_edge_labels
            for src, tgt, _ in ordered[:limit]:
                label_keys.add((src, tgt))

        for src, tgt, data in edges:
            sid = node_id[src]
            tid = node_id[tgt]
            freq = int(data.get("frequency", 0))
            width = scale_edge_width(
                freq,
                min_freq=min_edge_freq,
                max_freq=max_edge_freq,
            )
            weight = _scale_edge_weight(
                freq,
                min_freq=min_edge_freq,
                max_freq=max_edge_freq,
            )
            tooltip = _escape_dot(f"{src} -> {tgt}\nFrekuensi: {freq}")

            attrs = [
                f'penwidth="{width:.2f}"',
                f'weight="{weight}"',
                f'tooltip="{tooltip}"',
                f'edgetooltip="{tooltip}"',
                'label=""',
            ]
            if (src, tgt) in label_keys:
                attrs.append(f'xlabel="{freq}"')

            add(f"  {sid} -> {tid} [{', '.join(attrs)}];")

    add("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# DOT -> SVG
# ----------------------------------------------------------------------

def render_dot_to_svg(dot: str) -> str:
    """Render a DOT document to an SVG string using local Graphviz.

    Strips the XML declaration and DOCTYPE so the result can be inlined
    into an HTML body without breaking the parent document.

    Parameters
    ----------
    dot : str
        DOT source produced by :func:`generate_graphviz_dot`.

    Returns
    -------
    str
        Cleaned SVG markup starting with the ``<svg`` element.

    Raises
    ------
    RuntimeError
        * If ``dot`` is empty.
        * If the Graphviz Python binding is not installed.
        * If the ``dot`` executable cannot be located on ``PATH``.
        * If Graphviz returns empty or invalid SVG output.
    """
    if not dot or not dot.strip():
        raise RuntimeError("DOT Graphviz kosong.")

    try:
        from graphviz import Source
        from graphviz.backend.execute import ExecutableNotFound
    except ImportError as exc:
        raise RuntimeError(
            "Modul Python graphviz belum terpasang. Install dengan: pip install graphviz"
        ) from exc

    src = Source(dot)
    try:
        svg_bytes = src.pipe(format="svg")
    except ExecutableNotFound as exc:
        raise RuntimeError(
            "Binary Graphviz 'dot' tidak ditemukan di sistem. "
            "Ini normal di lingkungan cloud seperti Streamlit Cloud. "
            "Gunakan renderer standar Streamlit untuk render peta proses."
        ) from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Binary Graphviz 'dot' tidak ditemukan di sistem. "
            "Ini normal di lingkungan cloud seperti Streamlit Cloud. "
            "Gunakan renderer standar Streamlit untuk render peta proses."
        ) from exc

    svg = svg_bytes.decode("utf-8", errors="replace")

    # Strip XML declaration: <?xml ... ?>
    if svg.lstrip().startswith("<?xml"):
        end = svg.find("?>")
        if end != -1:
            svg = svg[end + 2 :]

    # Strip DOCTYPE
    stripped = svg.lstrip()
    if stripped.startswith("<!DOCTYPE"):
        end = stripped.find(">")
        if end != -1:
            # Find offset relative to the original string
            doctype_start = svg.find("<!DOCTYPE")
            svg = svg[: doctype_start] + stripped[end + 1 :]

    svg = svg.lstrip()

    # Strip leading HTML comments emitted by Graphviz
    while svg.startswith("<!--"):
        end = svg.find("-->")
        if end == -1:
            break
        svg = svg[end + 3 :].lstrip()

    if "<svg" not in svg:
        raise RuntimeError("Graphviz menghasilkan SVG kosong atau tidak valid.")

    if len(svg) < 80:
        raise RuntimeError("SVG Graphviz terlalu kecil atau tidak valid.")

    return svg
