"""Visualization helpers for the CMMC compliance-engine marimo notebook.

Provides four matplotlib-based chart factories consumed by the walkthrough notebook:

    sprs_gauge           -- semicircular gauge for the 0-110 SPRS score
    oracle_outcomes_chart -- horizontal bar chart of pass/fail/cantTell/needsAction counts
    traceability_graph   -- networkx directed graph: order -> modules -> controls
    coverage_family_chart -- stacked horizontal bar chart of coverage by CMMC family

All functions return a matplotlib Figure (never call plt.show()).
All imports are lazy so this module is safe to import even when the optional
dependencies (matplotlib, networkx) are absent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _missing_dep_figure(plt_module, message: str) -> "Figure":
    """Return a plain figure with a centered message.

    Callers must pass an already-imported matplotlib.pyplot module so this
    helper is never responsible for importing matplotlib itself (it is only
    called when matplotlib is confirmed available).
    """
    fig, ax = plt_module.subplots(figsize=(6, 2))
    ax.text(
        0.5, 0.5, message,
        ha="center", va="center", fontsize=11, color="gray",
        transform=ax.transAxes,
    )
    ax.set_axis_off()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Function 1: SPRS gauge
# ---------------------------------------------------------------------------

def sprs_gauge(score: int, status: str) -> "Figure":
    """Semicircular gauge chart showing SPRS score (0-110).

    Zones:
        0-87   -> red    (Ineligible)
        88-109 -> amber  (Conditional)
        110    -> green  (Final)

    Parameters
    ----------
    score:  integer SPRS score, clamped to [0, 110]
    status: human-readable status string printed below the score
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError as exc:
        raise ImportError("install matplotlib to see the SPRS gauge") from exc

    score = max(0, min(110, int(score)))

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set_aspect("equal")
    ax.set_axis_off()

    # ------------------------------------------------------------------
    # The gauge is drawn in axis coordinates.  We map the [0, 110] score
    # range onto [180, 0] degrees (left arc = low score, right = high).
    # ------------------------------------------------------------------
    def _score_to_angle_rad(s: float) -> float:
        """Map score in [0,110] to radians, left (pi) -> right (0)."""
        return np.pi * (1.0 - s / 110.0)

    cx, cy = 0.5, 0.18   # centre of the semicircle in axes fraction
    r_outer = 0.38
    r_inner = 0.24        # thickness of the arc band
    r_bg    = 0.40        # slightly wider background

    # --- background arc (gray) ---
    theta_bg = np.linspace(0, np.pi, 300)
    for t_out, t_in in [
        (r_bg, r_inner - 0.02),
    ]:
        xs_out = cx + t_out * np.cos(theta_bg)
        ys_out = cy + t_out * np.sin(theta_bg)
        xs_in  = cx + (r_inner - 0.02) * np.cos(theta_bg[::-1])
        ys_in  = cy + (r_inner - 0.02) * np.sin(theta_bg[::-1])
        ax.fill(
            np.concatenate([xs_out, xs_in]),
            np.concatenate([ys_out, ys_in]),
            color="#d0d0d0", zorder=1,
        )

    # --- coloured zone arcs ---
    # Each zone is drawn as a filled wedge patch.
    zones = [
        (0,   87,  "#e74c3c"),   # red   – Ineligible
        (87,  109, "#f39c12"),   # amber – Conditional
        (109, 110, "#27ae60"),   # green – Final
    ]

    for z_lo, z_hi, color in zones:
        a_start = _score_to_angle_rad(z_hi)   # higher score = smaller angle
        a_end   = _score_to_angle_rad(z_lo)
        theta   = np.linspace(a_start, a_end, max(2, int((a_end - a_start) / np.pi * 200)))
        xs_out  = cx + r_outer * np.cos(theta)
        ys_out  = cy + r_outer * np.sin(theta)
        xs_in   = cx + r_inner * np.cos(theta[::-1])
        ys_in   = cy + r_inner * np.sin(theta[::-1])
        ax.fill(
            np.concatenate([xs_out, xs_in]),
            np.concatenate([ys_out, ys_in]),
            color=color, zorder=2, alpha=0.92,
        )

    # --- needle ---
    needle_angle = _score_to_angle_rad(score)
    needle_len   = r_outer + 0.01
    nx = cx + needle_len * np.cos(needle_angle)
    ny = cy + needle_len * np.sin(needle_angle)
    ax.annotate(
        "",
        xy=(nx, ny), xytext=(cx, cy),
        arrowprops=dict(
            arrowstyle="-|>",
            color="black",
            lw=1.8,
            mutation_scale=10,
        ),
        zorder=5,
    )

    # pivot dot
    ax.plot(cx, cy, "o", color="black", ms=5, zorder=6)

    # --- centre text ---
    ax.text(
        cx, cy + 0.04,
        str(score),
        ha="center", va="bottom",
        fontsize=26, fontweight="bold", color="#2c3e50",
        zorder=7,
    )
    ax.text(
        cx, cy - 0.04,
        status,
        ha="center", va="top",
        fontsize=9, color="#555555",
        zorder=7,
    )

    # --- tick labels: 0, 55, 88, 110 ---
    for tick_val, label in [(0, "0"), (88, "88"), (110, "110")]:
        ta = _score_to_angle_rad(tick_val)
        tx = cx + (r_outer + 0.06) * np.cos(ta)
        ty = cy + (r_outer + 0.06) * np.sin(ta)
        ax.text(tx, ty, label, ha="center", va="center", fontsize=7, color="#777777", zorder=8)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.72)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Function 2: Oracle outcomes chart
# ---------------------------------------------------------------------------

def oracle_outcomes_chart(outcomes: dict[str, str]) -> "Figure":
    """Horizontal bar chart showing counts of each oracle outcome.

    Parameters
    ----------
    outcomes: mapping of control_id -> outcome string
              e.g. {"AC.L2-3.1.1": "passed", "IA.L2-3.5.3": "failed"}
    """
    try:
        import matplotlib.pyplot as plt
        from collections import Counter
    except ImportError as exc:
        raise ImportError("install matplotlib to see the oracle outcomes chart") from exc

    from collections import Counter

    OUTCOME_COLORS = {
        "passed":      "#27ae60",
        "failed":      "#e74c3c",
        "cantTell":    "#f39c12",
        "needsAction": "#e67e22",
    }
    DEFAULT_COLOR = "#95a5a6"

    counts = Counter(outcomes.values())

    # Preferred display order
    order = ["passed", "failed", "cantTell", "needsAction"]
    other = sorted(k for k in counts if k not in order)
    display_order = [k for k in order if k in counts] + [k for k in other if k in counts]

    if not display_order:
        # Empty outcomes dict: show placeholder
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No oracle outcomes", ha="center", va="center",
                fontsize=11, color="gray", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        return fig

    labels = display_order
    values = [counts[k] for k in labels]
    colors = [OUTCOME_COLORS.get(k, DEFAULT_COLOR) for k in labels]

    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.barh(labels, values, color=colors, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", ha="left", fontsize=10, color="#333333",
        )

    ax.set_xlabel("Control count", fontsize=9)
    ax.set_title("Oracle outcomes", fontsize=12, fontweight="bold", pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=10)
    ax.tick_params(axis="x", labelsize=9)
    ax.set_xlim(0, max(values) * 1.2 + 1)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Function 3: Traceability graph
# ---------------------------------------------------------------------------

_MODULE_FAMILY_MAP: dict[str, list[str]] = {
    "network":   ["SC"],
    "identity":  ["IA"],
    "audit":     ["AU"],
    "access":    ["AC"],
    "config":    ["CM"],
    "crypto":    ["SC"],
    "incident":  ["IR"],
    "media":     ["MP"],
    "physical":  ["PE"],
    "personnel": ["PS"],
    "risk":      ["RA"],
    "system":    ["SI"],
    "awareness": ["AT"],
    "ca":        ["CA"],
    "ma":        ["MA"],
}


def _families_for_module(module_name: str) -> list[str]:
    """Return CMMC family prefixes covered by a module based on its name prefix."""
    name_lower = module_name.lower()
    for prefix, families in _MODULE_FAMILY_MAP.items():
        if name_lower.startswith(prefix) or prefix in name_lower:
            return families
    return []


def traceability_graph(
    required: list[str],
    oracle_outcomes: dict[str, str],
    included_modules: list[str],
    contradictions: list,
) -> "Figure":
    """Directed graph: Order -> Modules -> Controls.

    Nodes
    -----
    Order node   -- blue
    Module nodes -- purple
    Control nodes -- green (passed), red (failed), amber (cantTell/needsAction), gray (no oracle)

    Edges
    -----
    Order -> each Module
    Module -> controls it covers (by family prefix heuristic)

    Parameters
    ----------
    required:         list of required control IDs (e.g. ["AC.L2-3.1.1", ...])
    oracle_outcomes:  {control_id: outcome}
    included_modules: list of module name strings
    contradictions:   list of control IDs (or objects with .control_id attr) that are contradicted
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required for traceability_graph; "
            "install it with: pip install matplotlib"
        ) from exc

    try:
        import networkx as nx
    except ImportError:
        return _missing_dep_figure(plt, "install networkx to see the traceability graph")

    # Normalise contradictions to a set of control ID strings
    contradiction_ids: set[str] = set()
    for c in contradictions:
        if isinstance(c, str):
            contradiction_ids.add(c)
        elif hasattr(c, "control_id"):
            contradiction_ids.add(str(c.control_id))
        elif hasattr(c, "id"):
            contradiction_ids.add(str(c.id))

    # Build graph
    G = nx.DiGraph()

    ORDER_NODE = "Order"
    G.add_node(ORDER_NODE, kind="order")

    for mod in included_modules:
        G.add_node(mod, kind="module")
        G.add_edge(ORDER_NODE, mod)

    # Control nodes
    for ctrl in required:
        G.add_node(ctrl, kind="control")

    # Module -> control edges via family heuristic
    sorted_controls = sorted(required)
    for mod in included_modules:
        families = _families_for_module(mod)
        matched: list[str] = []
        if families:
            for ctrl in sorted_controls:
                # control family is the first segment before the dot or dash
                family = ctrl.split(".")[0].split("-")[0].upper()
                if family in families:
                    matched.append(ctrl)
        # Fallback: connect to first 2 controls alphabetically
        if not matched:
            matched = sorted_controls[:2]
        for ctrl in matched:
            G.add_edge(mod, ctrl)

    # Layout
    pos: dict = {}
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    except Exception:
        try:
            pos = nx.drawing.nx_pydot.graphviz_layout(G, prog="dot")
        except Exception:
            pos = nx.spring_layout(G, seed=42, k=2.5)

    # Node colour and size
    node_colors: list[str] = []
    node_sizes: list[int] = []
    for node in G.nodes():
        kind = G.nodes[node].get("kind", "control")
        if kind == "order":
            node_colors.append("#2980b9")
            node_sizes.append(1800)
        elif kind == "module":
            node_colors.append("#8e44ad")
            node_sizes.append(1200)
        else:
            outcome = oracle_outcomes.get(node, "")
            if outcome == "passed":
                node_colors.append("#27ae60")
            elif outcome == "failed":
                node_colors.append("#e74c3c")
            elif outcome in ("cantTell", "needsAction"):
                node_colors.append("#f39c12")
            else:
                node_colors.append("#bdc3c7")
            node_sizes.append(800)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_axis_off()

    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9,
    )

    # Contradiction halos
    if contradiction_ids:
        contra_nodes = [n for n in G.nodes() if n in contradiction_ids]
        contra_pos_x = [pos[n][0] for n in contra_nodes]
        contra_pos_y = [pos[n][1] for n in contra_nodes]
        ax.scatter(
            contra_pos_x, contra_pos_y,
            s=[1600] * len(contra_nodes),
            facecolors="none", edgecolors="#c0392b",
            linewidths=3, zorder=4,
        )

    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#7f8c8d",
        arrows=True,
        arrowsize=12,
        width=0.8,
        connectionstyle="arc3,rad=0.05",
    )

    # Labels: shorten control IDs for readability
    labels = {}
    for node in G.nodes():
        kind = G.nodes[node].get("kind", "control")
        if kind == "control":
            # e.g. "AC.L2-3.1.1" -> "AC.L2\n3.1.1"
            parts = node.split("-", 1)
            labels[node] = "\n".join(parts) if len(parts) == 2 else node
        elif kind == "module":
            # show last path component if path-like, else full name
            short = node.split("/")[-1].split("\\")[-1]
            labels[node] = short[:16]
        else:
            labels[node] = node

    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=6, font_color="white", font_weight="bold",
    )

    # Legend
    legend_items = [
        mpatches.Patch(color="#2980b9",  label="Order"),
        mpatches.Patch(color="#8e44ad",  label="Module"),
        mpatches.Patch(color="#27ae60",  label="passed"),
        mpatches.Patch(color="#e74c3c",  label="failed"),
        mpatches.Patch(color="#f39c12",  label="cantTell / needsAction"),
        mpatches.Patch(color="#bdc3c7",  label="no oracle result"),
    ]
    if contradiction_ids:
        legend_items.append(
            mpatches.Patch(facecolor="none", edgecolor="#c0392b",
                           linewidth=2, label="contradiction")
        )
    ax.legend(handles=legend_items, loc="lower left", fontsize=8, framealpha=0.85)

    ax.set_title("Traceability: Order -> Modules -> Controls", fontsize=13, fontweight="bold", pad=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Function 4: Coverage by family chart
# ---------------------------------------------------------------------------

_CMMC_FAMILIES = ["AC", "AT", "AU", "CA", "CM", "IA", "IR", "MA", "MP", "PE", "PS", "RA", "SC", "SI"]

_STATUS_COLORS = {
    "machine":   "#2980b9",
    "attested":  "#e67e22",
    "inherited": "#16a085",
}


def coverage_family_chart(coverage: list[dict]) -> "Figure":
    """Stacked horizontal bar chart: coverage counts per CMMC family.

    Parameters
    ----------
    coverage: list of dicts with keys:
        family  -- e.g. "AC"
        status  -- one of "machine" | "attested" | "inherited"
        weight  -- numeric (used as count weight; pass 1 for unit count)
        id      -- control id (informational, not used for display)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("install matplotlib to see the coverage chart") from exc

    from collections import defaultdict

    # Aggregate counts: family -> status -> total weight
    tally: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for item in coverage:
        family = str(item.get("family", "??")).upper()
        status = str(item.get("status", "machine"))
        weight = float(item.get("weight", 1))
        tally[family][status] += weight

    # Determine which families to display (canonical order, only those present)
    families_present = [f for f in _CMMC_FAMILIES if f in tally]
    # Append any non-standard families at the end
    extras = sorted(f for f in tally if f not in _CMMC_FAMILIES)
    all_families = families_present + extras

    if not all_families:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No coverage data", ha="center", va="center",
                fontsize=11, color="gray", transform=ax.transAxes)
        ax.set_axis_off()
        fig.tight_layout()
        return fig

    statuses = ["machine", "attested", "inherited"]
    # Include any extra status values
    extra_statuses = sorted(
        s for fam in tally.values() for s in fam if s not in statuses
    )
    all_statuses = statuses + extra_statuses

    fig, ax = plt.subplots(figsize=(8, max(4, len(all_families) * 0.45 + 1.5)))

    lefts = [0.0] * len(all_families)
    bar_height = 0.6

    for status in all_statuses:
        vals = [tally[f].get(status, 0.0) for f in all_families]
        color = _STATUS_COLORS.get(status, "#95a5a6")
        bars = ax.barh(
            all_families, vals, left=lefts,
            height=bar_height,
            color=color, label=status,
            edgecolor="white", linewidth=0.4,
        )
        # Label non-zero segments
        for bar, val, left in zip(bars, vals, lefts):
            if val > 0:
                mid = left + val / 2
                ax.text(
                    mid, bar.get_y() + bar.get_height() / 2,
                    str(int(val)) if val == int(val) else f"{val:.1f}",
                    ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold",
                )
        lefts = [l + v for l, v in zip(lefts, vals)]

    ax.set_xlabel("Control count", fontsize=9)
    ax.set_ylabel("CMMC family", fontsize=9)
    ax.set_title("Coverage by family", fontsize=12, fontweight="bold", pad=8)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", labelsize=9)

    fig.tight_layout()
    return fig
