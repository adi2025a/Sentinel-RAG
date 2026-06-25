"""
dashboard/app.py
================
SentinelRAG — Streamlit Threat Intelligence Dashboard

Connects to:
  GET  /health              — pipeline readiness
  POST /admin/upload-pdf/   — ingest PDF  (X-Admin-Token header)
  POST /user/query/         — query with PID response
"""

import json
import time
from datetime import datetime

import requests
import streamlit as st

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SentinelRAG",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0D1117;
    color: #C9D1D9;
}
.stApp { background-color: #0D1117; }

[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1F2937;
}
[data-testid="stSidebar"] * { color: #C9D1D9 !important; }

.main-header {
    display: flex; align-items: center; gap: 14px;
    padding: 28px 0 8px 0;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 28px;
}
.main-header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.7rem; font-weight: 700;
    color: #F0F6FF; margin: 0; letter-spacing: -0.5px;
}
.main-header .subtitle {
    font-size: 0.78rem; color: #6B7280;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.08em; text-transform: uppercase;
}
.shield-icon { font-size: 2.2rem; line-height: 1; }

.verdict-container {
    display: flex; align-items: center;
    justify-content: center; padding: 36px 0 28px 0;
}
.verdict-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.05rem; font-weight: 700;
    letter-spacing: 0.22em; padding: 14px 44px;
    border-radius: 6px; display: inline-flex;
    align-items: center; gap: 12px;
    text-transform: uppercase; border: 2px solid;
}
.verdict-ALLOW   { color:#34D399; border-color:#34D399; background:rgba(52,211,153,0.07); box-shadow:0 0 32px -4px rgba(52,211,153,0.35); }
.verdict-REVIEW  { color:#FFB300; border-color:#FFB300; background:rgba(255,179,0,0.07);  box-shadow:0 0 32px -4px rgba(255,179,0,0.35); }
.verdict-BLOCK   { color:#FF3B3B; border-color:#FF3B3B; background:rgba(255,59,59,0.07);  box-shadow:0 0 32px -4px rgba(255,59,59,0.35); }

.risk-bar-track {
    background: #1F2937; border-radius: 4px;
    height: 10px; overflow: hidden; margin-bottom: 6px;
}
.risk-bar-fill { height: 100%; border-radius: 4px; }

.metric-card {
    background: #111827; border: 1px solid #1F2937;
    border-radius: 10px; padding: 18px 20px; height: 100%;
}
.metric-card .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: #6B7280; margin-bottom: 8px;
}
.metric-card .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem; font-weight: 700;
    color: #F0F6FF; line-height: 1;
}
.metric-card .sub { font-size: 0.72rem; color: #6B7280; margin-top: 5px; }

.attack-chip {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; font-weight: 500;
    padding: 5px 14px; border-radius: 100px;
    border: 1px solid; margin: 3px;
}
.chip-critical { color:#FF3B3B; border-color:rgba(255,59,59,0.4);   background:rgba(255,59,59,0.08); }
.chip-high     { color:#FF7B3B; border-color:rgba(255,123,59,0.4);  background:rgba(255,123,59,0.08); }
.chip-medium   { color:#FFB300; border-color:rgba(255,179,0,0.4);   background:rgba(255,179,0,0.08); }
.chip-low      { color:#34D399; border-color:rgba(52,211,153,0.4);  background:rgba(52,211,153,0.08); }
.chip-none     { color:#6B7280; border-color:rgba(107,114,128,0.3); background:rgba(107,114,128,0.06); }

.section-heading {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.16em; color: #4B5563;
    margin: 24px 0 12px 0;
    display: flex; align-items: center; gap: 10px;
}
.section-heading::after {
    content: ''; flex: 1; height: 1px; background: #1F2937;
}

.detail-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.detail-table tr { border-bottom: 1px solid #1A2233; }
.detail-table td { padding: 9px 6px; vertical-align: top; }
.detail-table td:first-child {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.08em;
    width: 38%; padding-right: 16px; white-space: nowrap;
}
.detail-table td:last-child {
    color: #C9D1D9;
    font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
}

.response-box {
    background: #0A0F1A; border: 1px solid #1F2937;
    border-radius: 8px; padding: 18px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; line-height: 1.65; color: #C9D1D9;
    min-height: 80px; white-space: pre-wrap; word-break: break-word;
}

.log-entry {
    display: flex; gap: 12px; padding: 8px 0;
    border-bottom: 1px solid #111827;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; align-items: flex-start;
}
.log-ts    { color:#4B5563; white-space:nowrap; min-width:75px; }
.log-badge { font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:3px; white-space:nowrap; }
.log-badge-A { background:rgba(52,211,153,0.15); color:#34D399; }
.log-badge-R { background:rgba(255,179,0,0.15);  color:#FFB300; }
.log-badge-B { background:rgba(255,59,59,0.15);  color:#FF3B3B; }
.log-query  { color:#C9D1D9; flex:1; }

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background-color: #111827 !important;
    border: 1px solid #1F2937 !important;
    color: #C9D1D9 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.15) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #0EA5E9, #0069B4) !important;
    color: #fff !important; border: none !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    padding: 10px 24px !important; width: 100% !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
div[data-testid="stFileUploader"] {
    background: #111827 !important;
    border: 1px dashed #1F2937 !important;
    border-radius: 10px !important;
}
div[data-testid="stFileUploader"] * { color: #6B7280 !important; }
div.stAlert { border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
div[data-testid="stExpander"] { background:#111827; border:1px solid #1F2937; border-radius:10px; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────
for key, default in [
    ("query_log",    []),
    ("last_result",  None),
    ("doc_uploaded", False),
    ("doc_name",     None),
    ("api_healthy",  None),   # None=unchecked, True=ok, False=down
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _verdict_color(decision: str) -> str:
    return {"ALLOW": "#34D399", "REVIEW": "#FFB300", "BLOCK": "#FF3B3B"}.get(decision, "#6B7280")

def _badge_cls(decision: str) -> str:
    return {"ALLOW": "log-badge-A", "REVIEW": "log-badge-R", "BLOCK": "log-badge-B"}.get(decision, "log-badge-A")

def _risk_color(score: float, block_t: float, warn_t: float) -> str:
    if score >= block_t:  return "#FF3B3B"
    if score >= warn_t:   return "#FFB300"
    return "#34D399"

def metric_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f"<div class='sub'>{sub}</div>" if sub else ""
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {sub_html}
    </div>"""


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:4px 0 20px 0'>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.62rem;
                    letter-spacing:0.18em;text-transform:uppercase;color:#4B5563;margin-bottom:4px'>
            SentinelRAG
        </div>
        <div style='font-family:JetBrains Mono,monospace;font-size:1.1rem;
                    font-weight:700;color:#F0F6FF'>Pipeline Evaluator</div>
        <div style='font-size:0.72rem;color:#4B5563;margin-top:4px'>
            v1.0 · Threat Intelligence Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Connection settings ──────────────────────────────────────────────────
    st.markdown('<div class="section-heading">Connection</div>', unsafe_allow_html=True)

    FASTAPI_BASE = st.text_input(
        "FastAPI Base URL",
        value="http://localhost:8000",
        key="api_url",
    )
    ADMIN_TOKEN = st.text_input(
        "Admin Token",
        type="password",
        placeholder="X-Admin-Token value",
        key="admin_token",
    )

    if st.button("⟳  Check Backend", key="health_btn"):
        try:
            r = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
            if r.status_code == 200:
                data = r.json()
                st.session_state.api_healthy = True
                # Sync doc status from server
                if data.get("ready"):
                    st.session_state.doc_uploaded = True
                st.success(
                    f"Backend online · {data.get('pid_patterns', '?')} PID patterns loaded"
                )
            else:
                st.session_state.api_healthy = False
                st.error(f"Backend returned {r.status_code}")
        except Exception as e:
            st.session_state.api_healthy = False
            st.error(f"Cannot reach backend: {e}")

    # ── Document ingestion ───────────────────────────────────────────────────
    st.markdown('<div class="section-heading" style="margin-top:24px">Document Ingestion</div>',
                unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help="Only PDF is accepted by the pipeline.",
        label_visibility="collapsed",
    )

    if uploaded_file:
        size_kb = round(uploaded_file.size / 1024, 1)
        st.markdown(f"""
        <div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;
                    color:#C9D1D9;margin:6px 0 2px 0;word-break:break-all'>
            📄 {uploaded_file.name}
        </div>
        <div style='font-size:0.68rem;color:#4B5563;margin-bottom:8px'>{size_kb} KB · PDF</div>
        """, unsafe_allow_html=True)

        if st.button("⬆  Ingest Document", key="upload_btn"):
            if not ADMIN_TOKEN:
                st.error("Enter your Admin Token above first.")
            else:
                with st.spinner("Uploading to pipeline..."):
                    try:
                        resp = requests.post(
                            f"{FASTAPI_BASE}/admin/upload-pdf/",
                            files={"file": (uploaded_file.name,
                                            uploaded_file.getvalue(),
                                            "application/pdf")},
                            headers={"X-Admin-Token": ADMIN_TOKEN},
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.doc_uploaded = True
                            st.session_state.doc_name = uploaded_file.name
                            st.success(
                                f"Ingested ✓  {data.get('chunks', '?')} chunks "
                                f"in {data.get('elapsed_ms', '?')}ms"
                            )
                        elif resp.status_code == 403:
                            st.error("Wrong admin token.")
                        else:
                            st.error(f"Upload failed ({resp.status_code}): {resp.text[:200]}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

    if st.session_state.doc_uploaded:
        st.markdown(f"""
        <div style='margin-top:10px;padding:10px 14px;background:rgba(52,211,153,0.06);
                    border:1px solid rgba(52,211,153,0.2);border-radius:8px;
                    font-family:JetBrains Mono,monospace;font-size:0.72rem;color:#34D399'>
            ✓ Active: {st.session_state.doc_name or "document"}
        </div>
        """, unsafe_allow_html=True)

    # ── Threshold sliders ────────────────────────────────────────────────────
    st.markdown('<div class="section-heading" style="margin-top:28px">Display Thresholds</div>',
                unsafe_allow_html=True)
    st.caption("Visual only — actual thresholds are set in your .env")

    block_t = st.slider("Block line", 0.0, 1.0, 0.65, 0.01, key="block_thresh")
    warn_t  = st.slider("Warn line",  0.0, 1.0, 0.40, 0.01, key="warn_thresh")

    st.markdown(f"""
    <div style='font-family:JetBrains Mono,monospace;font-size:0.68rem;
                color:#4B5563;margin-top:6px;line-height:1.7'>
        <span style='color:#34D399'>■</span> ALLOW  &lt; {warn_t:.2f}<br>
        <span style='color:#FFB300'>■</span> REVIEW {warn_t:.2f} – {block_t:.2f}<br>
        <span style='color:#FF3B3B'>■</span> BLOCK  &gt; {block_t:.2f}
    </div>
    """, unsafe_allow_html=True)

    # ── Query history ────────────────────────────────────────────────────────
    st.markdown('<div class="section-heading" style="margin-top:28px">Query History</div>',
                unsafe_allow_html=True)

    if st.session_state.query_log:
        for entry in reversed(st.session_state.query_log[-8:]):
            st.markdown(f"""
            <div class="log-entry">
                <span class="log-ts">{entry["ts"]}</span>
                <span class="log-badge {_badge_cls(entry['decision'])}">{entry['decision']}</span>
                <span class="log-query">{entry['query'][:42]}{"…" if len(entry['query'])>42 else ""}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.72rem;'
                    'color:#4B5563;padding:8px 0">No queries yet.</div>', unsafe_allow_html=True)

    if st.button("🗑  Clear History", key="clear_log"):
        st.session_state.query_log  = []
        st.session_state.last_result = None
        st.rerun()


# ─── Main Panel ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <span class="shield-icon">🛡️</span>
    <div>
        <h1>SentinelRAG Evaluator</h1>
        <div class="subtitle">Real-time threat analysis · Injection detection · Risk scoring</div>
    </div>
</div>
""", unsafe_allow_html=True)

col_query, col_status = st.columns([3, 2], gap="large")

with col_query:
    st.markdown('<div class="section-heading">Query Input</div>', unsafe_allow_html=True)

    query_text = st.text_area(
        "Enter your query",
        height=130,
        placeholder="Type your query — the pipeline will score its injection risk...",
        label_visibility="collapsed",
        key="query_input",
    )

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        run_btn = st.button("▶  Evaluate Query", key="run_query")
    with col_btn2:
        if st.button("✕ Clear", key="clear_query"):
            st.session_state.last_result = None
            st.rerun()

    # ── Evaluate ─────────────────────────────────────────────────────────────
    if run_btn:
        if not query_text.strip():
            st.warning("Please enter a query before evaluating.")
        elif not st.session_state.doc_uploaded:
            st.warning("Upload and ingest a document first (sidebar).")
        else:
            with st.spinner("Running through secure pipeline..."):
                t0 = time.perf_counter()
                try:
                    resp = requests.post(
                        f"{FASTAPI_BASE}/user/query/",
                        params={"query": query_text.strip()},
                        timeout=60,
                    )
                    elapsed_ms = (time.perf_counter() - t0) * 1000

                    if resp.status_code == 200:
                        data = resp.json()
                        # Flatten into a single display dict
                        pid  = data.get("pid", {})
                        result = {
                            "query":          data.get("query", query_text),
                            "answer":         data.get("answer", ""),
                            "decision":       pid.get("decision", "ALLOW"),
                            "fused_score":    pid.get("score", 0.0),
                            "regex_score":    pid.get("regex_score", 0.0),
                            "semantic_score": pid.get("semantic_score", 0.0),
                            "risk_level":     pid.get("risk_level", "SAFE"),
                            "elapsed_ms":     data.get("elapsed_ms", elapsed_ms),
                            "blocked":        False,
                            "raw":            data,
                        }

                    elif resp.status_code == 400:
                        # Blocked by PID — detail contains the block reason
                        pid_detail = resp.json().get("detail", "Query blocked.")
                        result = {
                            "query":          query_text,
                            "answer":         "",
                            "decision":       "BLOCK",
                            "fused_score":    block_t,   # we don't get exact score on 400
                            "regex_score":    None,
                            "semantic_score": None,
                            "risk_level":     "CRITICAL",
                            "elapsed_ms":     (time.perf_counter() - t0) * 1000,
                            "blocked":        True,
                            "block_reason":   pid_detail,
                            "raw":            resp.json(),
                        }

                    elif resp.status_code == 503:
                        st.error("Pipeline not ready — ingest a document first.")
                        result = None

                    else:
                        st.error(f"API error ({resp.status_code}): {resp.text[:300]}")
                        result = None

                    if result:
                        st.session_state.last_result = result
                        st.session_state.query_log.append({
                            "ts":       datetime.now().strftime("%H:%M:%S"),
                            "decision": result["decision"],
                            "query":    query_text.strip(),
                        })

                except requests.exceptions.ConnectionError:
                    st.error("Cannot reach the FastAPI backend. Check the URL in the sidebar.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

with col_status:
    st.markdown('<div class="section-heading">System Status</div>', unsafe_allow_html=True)

    api_dot   = {True: ("🟢", "#34D399", "Online"), False: ("🔴", "#FF3B3B", "Offline"), None: ("🟡", "#FFB300", "Not checked")}
    doc_dot   = ("🟢", "#34D399", "Document loaded") if st.session_state.doc_uploaded else ("🔴", "#FF3B3B", "No document")
    api_state = api_dot[st.session_state.api_healthy]

    st.markdown(f"""
    <div style='background:#111827;border:1px solid #1F2937;border-radius:10px;padding:16px 18px;'>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.65rem;
                    text-transform:uppercase;letter-spacing:0.12em;color:#4B5563;margin-bottom:10px'>
            Pipeline Status
        </div>
        <div style='display:flex;flex-direction:column;gap:10px'>
            <div style='display:flex;justify-content:space-between;align-items:center;
                        font-family:JetBrains Mono,monospace;font-size:0.75rem'>
                <span style='color:#6B7280'>Backend API</span>
                <span style='color:{api_state[1]}'>{api_state[0]} {api_state[2]}</span>
            </div>
            <div style='display:flex;justify-content:space-between;align-items:center;
                        font-family:JetBrains Mono,monospace;font-size:0.75rem'>
                <span style='color:#6B7280'>Vector Store</span>
                <span style='color:{doc_dot[1]}'>{doc_dot[0]} {doc_dot[2]}</span>
            </div>
            <div style='display:flex;justify-content:space-between;align-items:center;
                        font-family:JetBrains Mono,monospace;font-size:0.75rem'>
                <span style='color:#6B7280'>PID Engine</span>
                <span style='color:#34D399'>🟢 Active</span>
            </div>
        </div>
        <div style='margin-top:12px;padding-top:12px;border-top:1px solid #1F2937;
                    font-family:JetBrains Mono,monospace;font-size:0.65rem;color:#4B5563'>
            Display: warn={warn_t:.2f} · block={block_t:.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Results Panel ────────────────────────────────────────────────────────────
result = st.session_state.last_result

if result:
    decision    = result.get("decision", "ALLOW")
    fused_score = float(result.get("fused_score", 0.0))
    risk_level  = result.get("risk_level", "SAFE")
    answer      = result.get("answer", "")
    elapsed_ms  = result.get("elapsed_ms", 0.0)
    regex_score    = result.get("regex_score")
    semantic_score = result.get("semantic_score")
    blocked        = result.get("blocked", False)
    block_reason   = result.get("block_reason", "")

    # ── Verdict banner ───────────────────────────────────────────────────────
    icon_map = {"ALLOW": "✅", "REVIEW": "⚠️", "BLOCK": "🚫"}
    icon = icon_map.get(decision, "❓")
    st.markdown(f"""
    <div class="verdict-container">
        <div class="verdict-badge verdict-{decision}">
            <span style='font-size:1.3rem'>{icon}</span>
            {decision}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Risk score bar ───────────────────────────────────────────────────────
    pct       = int(fused_score * 100)
    bar_color = _risk_color(fused_score, block_t, warn_t)

    st.markdown(f"""
    <div style='max-width:540px;margin:0 auto 24px auto'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px'>
            <span style='font-family:JetBrains Mono,monospace;font-size:0.65rem;
                         text-transform:uppercase;letter-spacing:0.12em;color:#6B7280'>
                Fused PID Score
            </span>
            <span style='font-family:JetBrains Mono,monospace;font-size:1rem;
                         font-weight:700;color:{bar_color}'>
                {fused_score:.4f}
            </span>
        </div>
        <div class="risk-bar-track">
            <div class="risk-bar-fill" style='width:{pct}%;background:{bar_color}'></div>
        </div>
        <div style='display:flex;justify-content:space-between;
                    font-family:JetBrains Mono,monospace;font-size:0.62rem;color:#4B5563'>
            <span>0.0</span>
            <span style='color:#FFB300'>warn {warn_t:.2f}</span>
            <span style='color:#FF3B3B'>block {block_t:.2f}</span>
            <span>1.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric cards ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-heading">PID Breakdown</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(metric_card("Fused Score", f"{fused_score:.4f}", "regex + semantic"), unsafe_allow_html=True)
    with m2:
        rx = f"{regex_score:.4f}" if regex_score is not None else "—"
        st.markdown(metric_card("Regex Score", rx, "rule-based"), unsafe_allow_html=True)
    with m3:
        sem = f"{semantic_score:.4f}" if semantic_score is not None else "—"
        st.markdown(metric_card("Semantic Score", sem, "FAISS similarity"), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card("Latency", f"{int(elapsed_ms)}ms", "end-to-end"), unsafe_allow_html=True)

    # ── Risk level chip ──────────────────────────────────────────────────────
    st.markdown('<div class="section-heading">Risk Classification</div>', unsafe_allow_html=True)
    chip_cls = {
        "SAFE": "chip-low", "LOW": "chip-low",
        "MEDIUM": "chip-medium", "HIGH": "chip-high", "CRITICAL": "chip-critical",
    }.get(risk_level, "chip-medium")
    st.markdown(
        f'<span class="attack-chip {chip_cls}">{risk_level}</span>',
        unsafe_allow_html=True,
    )

    # ── Left / right panels ──────────────────────────────────────────────────
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown('<div class="section-heading">Query Detail</div>', unsafe_allow_html=True)
        rows = [
            ("Query",    result.get("query", "")[:120]),
            ("Decision", decision),
            ("Risk",     risk_level),
        ]
        if blocked:
            rows.append(("Block Reason", block_reason[:200]))

        rows_html = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows)
        st.markdown(f'<table class="detail-table">{rows_html}</table>', unsafe_allow_html=True)

        # Score sub-bars
        st.markdown('<div class="section-heading">Score Components</div>', unsafe_allow_html=True)
        for label, val in [("Regex", regex_score), ("Semantic", semantic_score), ("Fused", fused_score)]:
            if val is None:
                continue
            pct_sub   = int(float(val) * 100)
            col_sub   = _risk_color(float(val), block_t, warn_t)
            st.markdown(f"""
            <div style='margin-bottom:10px'>
                <div style='display:flex;justify-content:space-between;margin-bottom:3px;
                            font-family:JetBrains Mono,monospace;font-size:0.65rem;color:#6B7280'>
                    <span>{label}</span><span style='color:{col_sub}'>{float(val):.4f}</span>
                </div>
                <div class="risk-bar-track" style='height:6px'>
                    <div class="risk-bar-fill" style='width:{pct_sub}%;background:{col_sub}'></div>
                </div>
            </div>""", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-heading">Pipeline Response</div>', unsafe_allow_html=True)

        if blocked:
            st.markdown(f"""
            <div style='padding:14px 18px;background:rgba(255,59,59,0.06);
                        border:1px solid rgba(255,59,59,0.25);border-radius:8px;
                        font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#FF3B3B'>
                🚫 {block_reason or "Query blocked by PID engine."}
            </div>""", unsafe_allow_html=True)

        elif decision == "REVIEW":
            st.markdown("""
            <div style='padding:10px 14px;margin-bottom:10px;background:rgba(255,179,0,0.06);
                        border:1px solid rgba(255,179,0,0.25);border-radius:8px;
                        font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#FFB300'>
                ⚠️ Elevated risk — response shown with caution flag.
            </div>""", unsafe_allow_html=True)

        if answer and not blocked:
            st.markdown(f'<div class="response-box">{answer}</div>', unsafe_allow_html=True)
        elif not blocked:
            st.markdown(
                '<div class="response-box" style="color:#4B5563;font-style:italic">'
                'No response returned from pipeline.</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Raw API Response (JSON)", expanded=False):
            st.code(json.dumps(result.get("raw", result), indent=2), language="json")

else:
    st.markdown("""
    <div style='text-align:center;padding:60px 20px;'>
        <div style='font-size:3.5rem;margin-bottom:16px;opacity:0.3'>🛡️</div>
        <div style='font-family:JetBrains Mono,monospace;font-size:0.9rem;
                    color:#4B5563;margin-bottom:8px'>Awaiting evaluation</div>
        <div style='font-size:0.78rem;color:#374151;max-width:380px;
                    margin:0 auto;line-height:1.6'>
            Upload a document in the sidebar, then enter a query<br>
            to see real-time threat analysis and risk scoring.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top:48px;padding-top:16px;border-top:1px solid #1F2937;
            display:flex;justify-content:space-between;align-items:center;
            font-family:JetBrains Mono,monospace;font-size:0.62rem;color:#374151'>
    <span>SentinelRAG · Threat Intelligence Dashboard</span>
    <span>Backed by FastAPI + FAISS + BGE embeddings</span>
</div>
""", unsafe_allow_html=True)