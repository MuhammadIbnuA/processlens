"""Process map page - Graphviz-first DFG visualization.

Renders the simplified Directly-Follows Graph using Graphviz as the
primary renderer.  A zoomable, pannable SVG view is the default; the
non-zoomable ``st.graphviz_chart`` mode is kept as a lightweight
alternative.  All five tables (activities, transitions, start, end,
performance) are always shown below the map, even when rendering fails.
"""

from __future__ import annotations

import base64
import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.dfg import (
    calculate_activity_frequency,
    calculate_end_activities,
    calculate_start_activities,
    calculate_transition_frequency,
    calculate_transition_performance,
)
from core.map_abstraction import build_disco_like_graph
from core.process_map_renderer import generate_graphviz_dot, render_dot_to_svg
from ui.learning_mode import render_page_learning_content


DENSE_EDGES_THRESHOLD = 80
DENSE_NODES_THRESHOLD = 25
ALL_LABELS_DENSE_THRESHOLD = 40

SPLINE_OPTIONS = {
    "Lengkung": "spline",
    "Polyline": "polyline",
    "Ortho": "ortho",
}

LABEL_OPTIONS = ["Tidak tampil", "Top N frekuensi", "Semua"]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _detect_rework(trans_freq: pd.DataFrame) -> bool:
    """Detect self-loops or back-and-forth pairs in transitions."""
    if len(trans_freq) == 0:
        return False
    self_loops = trans_freq[trans_freq["source"] == trans_freq["target"]]
    if len(self_loops) > 0:
        return True
    for _, row in trans_freq.iterrows():
        reverse = trans_freq[
            (trans_freq["source"] == row["target"])
            & (trans_freq["target"] == row["source"])
        ]
        if len(reverse) > 0:
            return True
    return False


def render_zoomable_svg(svg: str, height: int = 750) -> None:
    """Render an SVG inside a zoomable, pannable container.

    The SVG is inlined directly into the HTML body (not into a JS
    template string).  Zoom and pan are applied to a wrapper ``#canvas``
    element so the original SVG markup stays untouched.

    Parameters
    ----------
    svg : str
        SVG markup produced by :func:`render_dot_to_svg`.  Must not
        contain an XML declaration or DOCTYPE.
    height : int, optional
        Viewport height in pixels.
    """
    component_html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: white;
    font-family: Arial, Helvetica, sans-serif;
    color: #111;
  }}
  .map-container {{
    width: 100%;
    background: white;
  }}
  .toolbar {{
    display: flex;
    gap: 8px;
    align-items: center;
    padding: 8px;
    border-bottom: 1px solid #ddd;
    background: #f8f9fa;
  }}
  .toolbar button {{
    background: white;
    border: 1px solid #bbb;
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 13px;
    cursor: pointer;
  }}
  .toolbar button:hover {{
    background: #eef3fa;
    border-color: #2B5B9F;
  }}
  .toolbar .help {{
    margin-left: auto;
    font-size: 12px;
    color: #666;
  }}
  #viewport {{
    width: 100%;
    height: {int(height)}px;
    overflow: hidden;
    border: 1px solid #ddd;
    background: white;
    cursor: grab;
    position: relative;
  }}
  #viewport.grabbing {{
    cursor: grabbing;
  }}
  #canvas {{
    transform-origin: 0 0;
    display: inline-block;
    position: absolute;
    top: 20px;
    left: 20px;
  }}
  #canvas svg {{
    display: block;
    max-width: none !important;
    height: auto;
    background: white;
    overflow: visible;
  }}
</style>
</head>
<body>
<div class="map-container">
  <div class="toolbar">
    <button id="btn-in" type="button">Perbesar</button>
    <button id="btn-out" type="button">Perkecil</button>
    <button id="btn-reset" type="button">Reset Tampilan</button>
    <span class="help">Geser peta dengan klik dan tarik. Gunakan scroll mouse untuk zoom.</span>
  </div>
  <div id="viewport">
    <div id="canvas">
{svg}
    </div>
  </div>
</div>

<script>
(function () {{
  const viewport = document.getElementById("viewport");
  const canvas = document.getElementById("canvas");

  let scale = 1;
  let translateX = 20;
  let translateY = 20;
  let isDragging = false;
  let startX = 0;
  let startY = 0;

  const MIN_SCALE = 0.1;
  const MAX_SCALE = 8;

  function applyTransform() {{
    canvas.style.transform =
      "translate(" + translateX + "px, " + translateY + "px) scale(" + scale + ")";
  }}

  function setScale(newScale, originX, originY) {{
    newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
    if (originX === undefined || originY === undefined) {{
      const rect = viewport.getBoundingClientRect();
      originX = rect.width / 2;
      originY = rect.height / 2;
    }}
    const ratio = newScale / scale;
    translateX = originX - (originX - translateX) * ratio;
    translateY = originY - (originY - translateY) * ratio;
    scale = newScale;
    applyTransform();
  }}

  function reset() {{
    scale = 1;
    translateX = 20;
    translateY = 20;
    applyTransform();
  }}

  // Wheel zoom anchored to the cursor
  viewport.addEventListener("wheel", function (e) {{
    e.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const ox = e.clientX - rect.left;
    const oy = e.clientY - rect.top;
    const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    setScale(scale * zoomFactor, ox, oy);
  }}, {{ passive: false }});

  // Click + drag pan
  viewport.addEventListener("mousedown", function (e) {{
    isDragging = true;
    startX = e.clientX - translateX;
    startY = e.clientY - translateY;
    viewport.classList.add("grabbing");
  }});

  window.addEventListener("mousemove", function (e) {{
    if (!isDragging) return;
    translateX = e.clientX - startX;
    translateY = e.clientY - startY;
    applyTransform();
  }});

  window.addEventListener("mouseup", function () {{
    isDragging = false;
    viewport.classList.remove("grabbing");
  }});

  // Toolbar buttons
  document.getElementById("btn-in").addEventListener("click", function () {{
    setScale(scale * 1.25);
  }});
  document.getElementById("btn-out").addEventListener("click", function () {{
    setScale(scale / 1.25);
  }});
  document.getElementById("btn-reset").addEventListener("click", reset);

  // Apply initial transform
  applyTransform();
}})();
</script>
</body>
</html>
"""
    components.html(component_html, height=int(height) + 80, scrolling=False)


# ----------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------

def render_map_page() -> None:
    """Render the process map page with Graphviz as the primary renderer."""
    st.header("Peta Proses")
    st.info(
        "Graf Aktivitas Berurutan Langsung (Directly-Follows Graph) menunjukkan "
        "aktivitas mana yang langsung mengikuti aktivitas lain dalam kasus yang sama."
    )

    render_page_learning_content("map")

    if "filtered_log" not in st.session_state:
        st.warning("Silakan unggah dan proses log kejadian terlebih dahulu.")
        return

    df = st.session_state["filtered_log"]

    if len(df) == 0:
        st.warning("Tidak ada kasus yang sesuai dengan filter saat ini.")
        return

    # Show progress while calculating DFG data
    with st.spinner("Menghitung data peta proses..."):
        act_freq = calculate_activity_frequency(df)
        trans_freq = calculate_transition_frequency(df)
        trans_perf = calculate_transition_performance(df)
        start_acts = calculate_start_activities(df)
        end_acts = calculate_end_activities(df)

    if _detect_rework(trans_freq):
        st.warning(
            "Aktivitas berulang terdeteksi. "
            "Ini dapat menunjukkan adanya rework (pengerjaan ulang)."
        )

    # ------------------------------------------------------------------
    # Map controls
    # ------------------------------------------------------------------
    st.subheader("Kontrol Peta Proses")
    st.caption(
        "Slider aktivitas mengatur seberapa banyak aktivitas yang ditampilkan "
        "berdasarkan frekuensi. Slider jalur mengatur seberapa banyak transisi "
        "antar aktivitas yang ditampilkan. Semakin kecil persentasenya, peta "
        "menjadi lebih sederhana."
    )

    c1, c2 = st.columns(2)
    with c1:
        activity_percent = st.slider(
            "Aktivitas ditampilkan (%)",
            min_value=1,
            max_value=100,
            value=60,
            step=1,
            key="map_activity_percent",
        )
    with c2:
        path_percent = st.slider(
            "Jalur ditampilkan (%)",
            min_value=1,
            max_value=100,
            value=40,
            step=1,
            key="map_path_percent",
        )

    c3, c4 = st.columns(2)
    with c3:
        spline_label = st.selectbox(
            "Mode garis",
            list(SPLINE_OPTIONS.keys()),
            index=0,
            key="map_spline_mode",
            help="Bentuk garis penghubung antar aktivitas.",
        )
        spline_mode = SPLINE_OPTIONS[spline_label]
    with c4:
        label_mode = st.selectbox(
            "Label jalur",
            LABEL_OPTIONS,
            index=1,
            key="map_label_mode",
            help="Atur tampilan label frekuensi pada jalur.",
        )

    c5, c6 = st.columns(2)
    with c5:
        max_edge_labels = st.number_input(
            "Jumlah label jalur maksimum",
            min_value=0,
            max_value=100,
            value=20,
            step=1,
            key="map_max_edge_labels",
            help="Berlaku untuk mode 'Top N frekuensi'.",
        )
    with c6:
        zoomable = st.checkbox(
            "Tampilan zoomable",
            value=True,
            key="map_zoomable",
            help="Aktifkan untuk zoom dan pan dengan mouse.",
        )

    use_standard_renderer = st.checkbox(
        "Gunakan renderer standar Streamlit",
        value=False,
        key="map_use_standard_renderer",
        help=(
            "Aktifkan untuk merender peta dengan st.graphviz_chart bawaan Streamlit "
            "jika tampilan zoomable bermasalah."
        ),
    )

    # ------------------------------------------------------------------
    # Build simplified graph
    # ------------------------------------------------------------------
    with st.spinner("Membangun graf peta proses..."):
        graph, summary = build_disco_like_graph(
            activity_freq=act_freq,
            transition_freq=trans_freq,
            start_activities=start_acts,
            end_activities=end_acts,
            activity_percent=int(activity_percent),
            path_percent=int(path_percent),
        )

    # ------------------------------------------------------------------
    # Summary metrics
    # ------------------------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total aktivitas", summary["total_activities"])
    m2.metric("Aktivitas ditampilkan", summary["visible_activities"])
    m3.metric("Total jalur", summary["total_paths"])
    m4.metric("Jalur ditampilkan", summary["visible_paths"])

    # ------------------------------------------------------------------
    # Density warnings
    # ------------------------------------------------------------------
    if summary["visible_paths"] > DENSE_EDGES_THRESHOLD:
        st.warning(
            "Peta proses masih cukup padat. "
            "Turunkan persentase jalur agar lebih mudah dibaca."
        )
    if summary["visible_activities"] > DENSE_NODES_THRESHOLD:
        st.warning(
            "Jumlah aktivitas masih banyak. "
            "Turunkan persentase aktivitas atau gunakan filter."
        )
    if label_mode == "Semua" and summary["visible_paths"] > ALL_LABELS_DENSE_THRESHOLD:
        st.warning(
            "Menampilkan semua label jalur pada peta padat dapat membuat peta sulit dibaca."
        )

    # ------------------------------------------------------------------
    # Resolve label settings
    # ------------------------------------------------------------------
    if label_mode == "Tidak tampil":
        show_edge_labels = False
        effective_max_labels = 0
    elif label_mode == "Semua":
        show_edge_labels = True
        effective_max_labels = -1  # no cap
    else:  # Top N frekuensi
        show_edge_labels = True
        effective_max_labels = int(max_edge_labels)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    st.subheader("Graf Aktivitas Berurutan Langsung")

    has_activity_node = any(
        d.get("node_type") == "activity" for _, d in graph.nodes(data=True)
    )

    dot_source: str = ""
    dot_error: str | None = None
    if has_activity_node:
        try:
            with st.spinner("Menghasilkan representasi DOT..."):
                dot_source = generate_graphviz_dot(
                    graph,
                    show_edge_labels=show_edge_labels,
                    max_edge_labels=effective_max_labels,
                    spline_mode=spline_mode,
                )
        except Exception as exc:
            dot_error = str(exc)

    # ------------------------------------------------------------------
    # Try to render SVG once (used for debug + zoomable view)
    # ------------------------------------------------------------------
    svg_source: str = ""
    svg_error: str | None = None
    if dot_source:
        try:
            with st.spinner("Merender SVG..."):
                svg_source = render_dot_to_svg(dot_source)
        except RuntimeError as exc:
            svg_error = str(exc)
        except Exception as exc:
            svg_error = str(exc)

    # ------------------------------------------------------------------
    # Debug expander
    # ------------------------------------------------------------------
    with st.expander("Debug Graphviz", expanded=False):
        st.write("DOT length:", len(dot_source))
        st.write("SVG length:", len(svg_source) if svg_source else 0)
        if dot_error:
            st.write("DOT error:", dot_error)
        if svg_error:
            st.write("SVG error:", svg_error)
        if dot_source:
            st.code(dot_source[:3000], language="dot")
            d1, d2 = st.columns(2)
            with d1:
                st.download_button(
                    "Unduh DOT",
                    data=dot_source,
                    file_name="peta_proses.dot",
                    mime="text/vnd.graphviz",
                )
            with d2:
                if svg_source:
                    st.download_button(
                        "Unduh SVG",
                        data=svg_source,
                        file_name="peta_proses.svg",
                        mime="image/svg+xml",
                    )

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    if not has_activity_node:
        st.info(
            "Tidak ada aktivitas yang tersisa setelah penyederhanaan. "
            "Naikkan persentase aktivitas untuk menampilkan lebih banyak."
        )
    elif dot_error or not dot_source:
        st.error("Gagal membuat DOT untuk peta proses.")
        if dot_error:
            st.info(dot_error)
    elif use_standard_renderer:
        # User opted in to the bundled Streamlit renderer
        try:
            st.graphviz_chart(dot_source, use_container_width=True)
        except Exception:
            st.error("Gagal merender peta proses dengan Graphviz.")
            st.info(
                "Pastikan Graphviz Desktop sudah terinstal dan perintah dot "
                "tersedia di PATH."
            )
    elif not zoomable:
        try:
            st.graphviz_chart(dot_source, use_container_width=True)
        except Exception:
            st.error("Gagal merender peta proses dengan Graphviz.")
            st.info(
                "Pastikan Graphviz Desktop sudah terinstal dan perintah dot "
                "tersedia di PATH."
            )
    elif svg_error or not svg_source:
        st.error("Gagal merender peta proses dengan Graphviz.")
        if svg_error:
            st.info(svg_error)
        st.info(
            "Pastikan Graphviz Desktop sudah terinstal dan perintah dot "
            "tersedia di PATH."
        )
        # Fallback to bundled viz.js renderer (works without local dot binary)
        try:
            st.graphviz_chart(dot_source, use_container_width=True)
        except Exception:
            pass
    else:
        # Zoomable SVG path
        render_zoomable_svg(svg_source, height=750)
        st.caption(
            "Jika SVG tidak tampil dengan benar, aktifkan "
            "**Gunakan renderer standar Streamlit** di kontrol di atas."
        )

    # ------------------------------------------------------------------
    # Legend
    # ------------------------------------------------------------------
    with st.expander("Keterangan"):
        st.markdown(
            "- **Kotak biru** = aktivitas dalam proses\n"
            "- **Lingkaran hijau (MULAI)** = awal kasus\n"
            "- **Lingkaran merah (SELESAI)** = akhir kasus\n"
            "- **Panah** = transisi antar aktivitas; semakin tebal semakin sering\n"
            "- **Label angka pada panah** = frekuensi transisi (jika diaktifkan)\n"
            "- Slider **Aktivitas (%)** dan **Jalur (%)** menyederhanakan peta dengan "
            "menyembunyikan aktivitas dan jalur yang kurang dominan."
        )

    # ------------------------------------------------------------------
    # Tables (always shown, even when plot fails)
    # ------------------------------------------------------------------
    st.subheader("Frekuensi Aktivitas")
    display_act = act_freq.rename(columns={"activity": "Aktivitas", "frequency": "Frekuensi"})
    st.dataframe(display_act, use_container_width=True, hide_index=True)

    st.subheader("Frekuensi Transisi")
    display_trans = trans_freq.rename(columns={
        "source": "Sumber", "target": "Tujuan", "frequency": "Frekuensi",
    })
    st.dataframe(display_trans, use_container_width=True, hide_index=True)

    st.subheader("Aktivitas Awal")
    display_start = start_acts.rename(columns={"activity": "Aktivitas", "frequency": "Frekuensi"})
    st.dataframe(display_start, use_container_width=True, hide_index=True)

    st.subheader("Aktivitas Akhir")
    display_end = end_acts.rename(columns={"activity": "Aktivitas", "frequency": "Frekuensi"})
    st.dataframe(display_end, use_container_width=True, hide_index=True)

    st.subheader("Kinerja Transisi")
    display_perf = trans_perf.rename(columns={
        "source": "Sumber",
        "target": "Tujuan",
        "frequency": "Frekuensi",
        "mean_waiting_seconds": "Tunggu Rata-rata (dtk)",
        "median_waiting_seconds": "Tunggu Median (dtk)",
        "min_waiting_seconds": "Tunggu Min (dtk)",
        "max_waiting_seconds": "Tunggu Maks (dtk)",
    })
    st.dataframe(display_perf, use_container_width=True, hide_index=True)