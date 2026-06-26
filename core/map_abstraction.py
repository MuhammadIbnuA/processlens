"""Disco-inspired process map abstraction.

Implements percentage-based activity and path significance filtering,
backbone path preservation, and DiGraph construction for the
process map view.

The abstraction is original and based on standard process mining
principles (frequency-based abstraction, activity/path significance,
preservation of connectivity).  No proprietary code is used.
"""

from __future__ import annotations

import math

import networkx as nx
import pandas as pd


def select_visible_activities(
    activity_freq: pd.DataFrame,
    activity_percent: int,
) -> set[str]:
    """Pick the most significant activities by percentage.

    Parameters
    ----------
    activity_freq : pd.DataFrame
        Columns ``activity`` (str) and ``frequency`` (int).
    activity_percent : int
        1-100.  ``100`` keeps every activity, smaller values keep the
        top fraction.

    Returns
    -------
    set[str]
        Names of the activities that should remain visible.  Always
        contains at least one activity if the input is non-empty.
    """
    if len(activity_freq) == 0:
        return set()

    sorted_freq = activity_freq.sort_values(
        ["frequency", "activity"], ascending=[False, True]
    )

    if activity_percent >= 100:
        return set(sorted_freq["activity"].tolist())

    total = len(sorted_freq)
    n = math.ceil(total * activity_percent / 100)
    n = max(1, n)
    return set(sorted_freq.head(n)["activity"].tolist())


def select_visible_paths(
    transition_freq: pd.DataFrame,
    visible_activities: set[str],
    path_percent: int,
) -> pd.DataFrame:
    """Pick the most significant transitions by percentage.

    Only transitions whose source *and* target are both in
    ``visible_activities`` are eligible.  From the eligible set the
    top fraction by frequency is returned.

    Parameters
    ----------
    transition_freq : pd.DataFrame
        Columns ``source`` (str), ``target`` (str), ``frequency`` (int).
    visible_activities : set[str]
        Activities that survived :func:`select_visible_activities`.
    path_percent : int
        1-100.  ``100`` keeps every eligible transition.

    Returns
    -------
    pd.DataFrame
        Same columns as the input, sorted descending by frequency.
        Always contains at least one row if eligible transitions exist.
    """
    if len(transition_freq) == 0:
        return transition_freq.copy().reset_index(drop=True)

    eligible = transition_freq[
        transition_freq["source"].isin(visible_activities)
        & transition_freq["target"].isin(visible_activities)
    ].copy()

    if len(eligible) == 0:
        return eligible.reset_index(drop=True)

    sorted_paths = eligible.sort_values(
        ["frequency", "source", "target"], ascending=[False, True, True]
    ).reset_index(drop=True)

    if path_percent >= 100:
        return sorted_paths

    total = len(sorted_paths)
    n = math.ceil(total * path_percent / 100)
    n = max(1, n)
    return sorted_paths.head(n).reset_index(drop=True)


def add_backbone_paths(
    selected_paths: pd.DataFrame,
    all_paths: pd.DataFrame,
    visible_activities: set[str],
) -> pd.DataFrame:
    """Re-introduce the strongest path for any orphan visible activity.

    For every visible activity that has no incoming (or outgoing)
    selected path, the strongest available incoming (or outgoing)
    path between visible activities is added back.  Edges that do not
    exist in the original log are never invented.

    Parameters
    ----------
    selected_paths : pd.DataFrame
        Output of :func:`select_visible_paths`.
    all_paths : pd.DataFrame
        Full transition table from the log.
    visible_activities : set[str]
        Activities that survived :func:`select_visible_activities`.

    Returns
    -------
    pd.DataFrame
        ``selected_paths`` plus any backbone additions, with duplicate
        ``(source, target)`` pairs removed.
    """
    if len(all_paths) == 0:
        return selected_paths.copy().reset_index(drop=True)

    visible_paths = all_paths[
        all_paths["source"].isin(visible_activities)
        & all_paths["target"].isin(visible_activities)
    ]
    if len(visible_paths) == 0:
        return selected_paths.copy().reset_index(drop=True)

    selected_keys: set[tuple[str, str]] = set(
        zip(selected_paths["source"], selected_paths["target"])
    )
    incoming_have = set(selected_paths["target"].astype(str).tolist())
    outgoing_have = set(selected_paths["source"].astype(str).tolist())

    additions: list[pd.Series] = []

    for activity in sorted(visible_activities):
        # Incoming
        if activity not in incoming_have:
            candidates = visible_paths[visible_paths["target"] == activity]
            if len(candidates) > 0:
                top = candidates.sort_values(
                    ["frequency", "source"], ascending=[False, True]
                ).iloc[0]
                key = (top["source"], top["target"])
                if key not in selected_keys:
                    additions.append(top)
                    selected_keys.add(key)

        # Outgoing
        if activity not in outgoing_have:
            candidates = visible_paths[visible_paths["source"] == activity]
            if len(candidates) > 0:
                top = candidates.sort_values(
                    ["frequency", "target"], ascending=[False, True]
                ).iloc[0]
                key = (top["source"], top["target"])
                if key not in selected_keys:
                    additions.append(top)
                    selected_keys.add(key)

    if not additions:
        return selected_paths.copy().reset_index(drop=True)

    additions_df = pd.DataFrame(additions)
    combined = pd.concat([selected_paths, additions_df], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["source", "target"], keep="first"
    ).reset_index(drop=True)
    return combined


def build_disco_like_graph(
    activity_freq: pd.DataFrame,
    transition_freq: pd.DataFrame,
    start_activities: pd.DataFrame,
    end_activities: pd.DataFrame,
    activity_percent: int,
    path_percent: int,
) -> tuple[nx.DiGraph, dict]:
    """Build a Disco-inspired simplified process graph.

    The percentage sliders only affect activity nodes and transition
    edges.  ``START`` (label ``MULAI``) and ``FINISH`` (label
    ``SELESAI``) are always present and are connected only to the
    visible start/end activities.

    Parameters
    ----------
    activity_freq : pd.DataFrame
        Columns ``activity``, ``frequency``.
    transition_freq : pd.DataFrame
        Columns ``source``, ``target``, ``frequency``.
    start_activities : pd.DataFrame
        Columns ``activity``, ``frequency`` (per-case start activity counts).
    end_activities : pd.DataFrame
        Columns ``activity``, ``frequency`` (per-case end activity counts).
    activity_percent : int
        1-100.
    path_percent : int
        1-100.

    Returns
    -------
    tuple[nx.DiGraph, dict]
        Graph and summary dictionary with totals and visible counts.
    """
    visible_activities = select_visible_activities(activity_freq, activity_percent)
    selected_paths = select_visible_paths(
        transition_freq, visible_activities, path_percent
    )
    selected_paths = add_backbone_paths(
        selected_paths, transition_freq, visible_activities
    )

    graph = nx.DiGraph()

    graph.add_node(
        "START",
        label="START",
        display_label="MULAI",
        frequency=0,
        node_type="start",
    )
    graph.add_node(
        "FINISH",
        label="FINISH",
        display_label="SELESAI",
        frequency=0,
        node_type="finish",
    )

    visible_act_freq = activity_freq[activity_freq["activity"].isin(visible_activities)]
    for _, row in visible_act_freq.iterrows():
        act = str(row["activity"])
        graph.add_node(
            act,
            label=act,
            display_label=act,
            frequency=int(row["frequency"]),
            node_type="activity",
        )

    for _, row in selected_paths.iterrows():
        src = str(row["source"])
        tgt = str(row["target"])
        if src in graph.nodes and tgt in graph.nodes:
            graph.add_edge(
                src,
                tgt,
                frequency=int(row["frequency"]),
                edge_type="transition",
            )

    visible_starts = start_activities[start_activities["activity"].isin(visible_activities)]
    for _, row in visible_starts.iterrows():
        graph.add_edge(
            "START",
            str(row["activity"]),
            frequency=int(row["frequency"]),
            edge_type="start",
        )

    visible_ends = end_activities[end_activities["activity"].isin(visible_activities)]
    for _, row in visible_ends.iterrows():
        graph.add_edge(
            str(row["activity"]),
            "FINISH",
            frequency=int(row["frequency"]),
            edge_type="finish",
        )

    # Final safety: if any visible activity is fully orphaned (no edges
    # of any kind), wire it as START -> activity -> FINISH so the DOT
    # layout never produces invisible/floating nodes.
    for act in list(visible_activities):
        if act not in graph.nodes:
            continue
        if graph.in_degree(act) == 0:
            graph.add_edge("START", act, frequency=0, edge_type="start")
        if graph.out_degree(act) == 0:
            graph.add_edge(act, "FINISH", frequency=0, edge_type="finish")

    summary = {
        "total_activities": int(len(activity_freq)),
        "visible_activities": int(len(visible_activities)),
        "total_paths": int(len(transition_freq)),
        "visible_paths": int(len(selected_paths)),
        "activity_percent": int(activity_percent),
        "path_percent": int(path_percent),
    }

    return graph, summary
