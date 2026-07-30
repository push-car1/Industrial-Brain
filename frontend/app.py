import streamlit as st
import httpx
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pyvis.network import Network
from datetime import datetime

API_BASE = "http://nginx:8080/api"

st.set_page_config(
    page_title="Industrial Knowledge Brain",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

GLASS_CSS = """
<style>
/* ── Gradient Background ── */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}
.stApp > header { background: transparent !important; }

/* ── Sidebar — Dark Glass ── */
section[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.88) !important;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div[data-baseweb="radio"] label {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
}

/* ── Typography ── */
h1, h2, h3, h4 { color: #f1f5f9 !important; }
p, span, label, li { color: #cbd5e1 !important; }

/* ── Glass Card ── */
.glass-card {
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease;
}
.glass-card:hover {
    background: rgba(255, 255, 255, 0.09);
    border-color: rgba(255, 255, 255, 0.16);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* ── Glass Metric Card ── */
.glass-metric {
    background: rgba(255, 255, 255, 0.07);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    padding: 1.4rem;
    text-align: center;
    transition: all 0.25s ease;
    height: 100%;
    border-top: 3px solid rgba(14, 165, 233, 0.5);
}
.glass-metric:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(14, 165, 233, 0.15);
    border-top-color: rgba(14, 165, 233, 0.8);
}
.glass-metric-icon { font-size: 1.6rem; margin-bottom: 0.2rem; }
.glass-metric-value {
    font-size: 2rem; font-weight: 700; color: #f1f5f9;
    line-height: 1.2;
}
.glass-metric-label {
    font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 600; margin-top: 0.15rem;
}
.glass-metric.accent-emerald { border-top-color: rgba(16, 185, 129, 0.5); }
.glass-metric.accent-emerald:hover { border-top-color: rgba(16, 185, 129, 0.8); box-shadow: 0 8px 32px rgba(16, 185, 129, 0.15); }
.glass-metric.accent-amber { border-top-color: rgba(245, 158, 11, 0.5); }
.glass-metric.accent-amber:hover { border-top-color: rgba(245, 158, 11, 0.8); box-shadow: 0 8px 32px rgba(245, 158, 11, 0.15); }
.glass-metric.accent-violet { border-top-color: rgba(139, 92, 246, 0.5); }
.glass-metric.accent-violet:hover { border-top-color: rgba(139, 92, 246, 0.8); box-shadow: 0 8px 32px rgba(139, 92, 246, 0.15); }

/* ── Glass Title ── */
.glass-title {
    font-size: 2rem; font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.2rem;
}
.glass-subtitle {
    color: #94a3b8; font-size: 0.95rem; margin-top: -0.3rem; margin-bottom: 1.2rem;
}

/* ── Glass Divider ── */
.glass-divider {
    height: 1px; margin: 1.5rem 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
}

/* ── Glass Section Header ── */
.glass-section {
    font-size: 1.2rem; font-weight: 700; color: #f1f5f9;
    margin-bottom: 0.8rem;
}

/* ── Glass Document Card ── */
.glass-doc {
    background: rgba(255, 255, 255, 0.05);
    border-left: 3px solid rgba(14, 165, 233, 0.5);
    border-radius: 0 12px 12px 0;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    transition: all 0.15s ease;
}
.glass-doc:hover {
    background: rgba(255, 255, 255, 0.08);
    border-left-color: rgba(14, 165, 233, 0.8);
}
.glass-doc-title { font-weight: 600; color: #f1f5f9; font-size: 0.9rem; }
.glass-doc-meta { font-size: 0.75rem; color: #64748b; margin-top: 0.1rem; }
.glass-badge {
    display: inline-block; padding: 0.1rem 0.5rem; border-radius: 9999px;
    font-size: 0.6rem; font-weight: 600; text-transform: uppercase;
    margin-left: 0.3rem;
}
.glass-badge-pdf { background: rgba(244, 63, 94, 0.2); color: #fda4af; }
.glass-badge-csv { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
.glass-badge-txt { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
.glass-badge-md { background: rgba(245, 158, 11, 0.2); color: #fcd34d; }

/* ── Streamlit Widgets — glass-friendly overrides ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #8b5cf6) !important;
    border: none !important; color: white !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 20px rgba(14, 165, 233, 0.3) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e2e8f0 !important; border-radius: 10px !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.10) !important;
    border-color: rgba(255,255,255,0.2) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important; padding: 0.3rem !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important; border-radius: 8px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(14, 165, 233, 0.2) !important;
    color: #38bdf8 !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    color: #f1f5f9 !important; border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(14, 165, 233, 0.5) !important;
    box-shadow: 0 0 0 1px rgba(14, 165, 233, 0.3) !important;
}

/* Slider */
.stSlider > div > div > div > div {
    background: #0ea5e9 !important;
}

/* File uploader */
.stFileUploader {
    background: rgba(255,255,255,0.04);
    border: 2px dashed rgba(255,255,255,0.12);
    border-radius: 14px; padding: 1rem;
}
.stFileUploader:hover {
    border-color: rgba(14, 165, 233, 0.4);
    background: rgba(255,255,255,0.06);
}

/* Expanders */
.stExpander {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}
.stExpander summary { color: #e2e8f0 !important; }

/* Chat messages */
.stChatMessage {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
}

/* Dataframe */
.stDataFrame {
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
}

/* Info/Success/Warning/Error */
.stAlert { border-radius: 10px !important; }

/* Plotly chart container */
.stPlotlyChart {
    background: rgba(255,255,255,0.03);
    border-radius: 12px; padding: 0.5rem;
}

/* Radio in sidebar */
section[data-testid="stSidebar"] div[data-baseweb="radio"] {
    background: transparent !important;
}
section[data-testid="stSidebar"] div[data-baseweb="radio"] label {
    color: #cbd5e1 !important;
}
section[data-testid="stSidebar"] div[data-baseweb="radio"] label[data-checked="true"] {
    color: #38bdf8 !important;
}
</style>
"""


def api_get(path):
    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(f"{API_BASE}{path}")
            return r.json() if r.status_code == 200 else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


def api_post(path, data=None):
    try:
        with httpx.Client(timeout=600) as client:
            r = client.post(f"{API_BASE}{path}", json=data or {})
            return r.json() if r.status_code == 200 else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


def api_upload(path, files):
    try:
        with httpx.Client(timeout=120) as client:
            r = client.post(f"{API_BASE}{path}", files=files)
            return r.json() if r.status_code == 200 else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}


def glass_title(text, icon=""):
    prefix = f"{icon} " if icon else ""
    return f'<div class="glass-title">{prefix}{text}</div>'


def glass_section(text):
    return f'<div class="glass-section">{text}</div>'


def glass_metric(icon, value, label, accent=""):
    cls = f"glass-metric {accent}" if accent else "glass-metric"
    return f"""<div class="{cls}">
        <div class="glass-metric-icon">{icon}</div>
        <div class="glass-metric-value">{value}</div>
        <div class="glass-metric-label">{label}</div>
    </div>"""


def glass_divider():
    return '<div class="glass-divider"></div>'


def doc_badge(filename):
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    cls = {"pdf": "glass-badge-pdf", "csv": "glass-badge-csv",
           "txt": "glass-badge-txt", "md": "glass-badge-md"}.get(ext, "glass-badge-txt")
    return f'<span class="glass-badge {cls}">{ext}</span>' if ext else ""


def main():
    st.markdown(GLASS_CSS, unsafe_allow_html=True)

    st.sidebar.title("🏭 IKB")
    st.sidebar.caption("Industrial Knowledge Brain")

    pages = {
        "Dashboard": dashboard,
        "Upload Documents": upload_page,
        "Knowledge Graph": graph_page,
        "AI Copilot": copilot_page,
        "Maintenance": maintenance_page,
        "Compliance": compliance_page,
    }

    choice = st.sidebar.radio("Navigate", list(pages.keys()))

    st.sidebar.markdown("---")

    pages[choice]()


def dashboard():
    st.markdown(glass_title("Industrial Knowledge Brain"), unsafe_allow_html=True)
    st.markdown('<div class="glass-subtitle">Unified Asset & Operations Intelligence</div>', unsafe_allow_html=True)

    summary = api_get("/knowledge-graph/summary")
    node_counts = summary.get("node_counts", {}) if "error" not in summary else {}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(glass_metric("🏭", node_counts.get("Equipment", 0), "Equipment"), unsafe_allow_html=True)
    with col2:
        st.markdown(glass_metric("📄", node_counts.get("Document", 0), "Documents", "accent-emerald"), unsafe_allow_html=True)
    with col3:
        st.markdown(glass_metric("📋", node_counts.get("Regulation", 0), "Regulations", "accent-amber"), unsafe_allow_html=True)
    with col4:
        st.markdown(glass_metric("🔗", summary.get("relationship_count", 0), "Relationships", "accent-violet"), unsafe_allow_html=True)

    st.markdown(glass_divider(), unsafe_allow_html=True)

    st.markdown(glass_section("Recent Documents"), unsafe_allow_html=True)
    docs = summary.get("recent_documents", [])
    if docs:
        df = pd.DataFrame(docs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No documents ingested yet. Go to **Upload Documents** to add sample data.")

    st.markdown(glass_divider(), unsafe_allow_html=True)

    st.markdown(glass_section("Knowledge Coverage"), unsafe_allow_html=True)
    if node_counts:
        labels = list(node_counts.keys())
        values = list(node_counts.values())
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
        fig.update_layout(
            height=300, margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)


def upload_page():
    st.markdown(glass_title("Document Ingestion"), unsafe_allow_html=True)
    st.markdown('<div class="glass-subtitle">Upload industrial documents to build the knowledge base.</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "png", "jpg", "jpeg", "csv", "xlsx", "txt", "md"],
    )

    if uploaded_file:
        with st.spinner("Processing document..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            result = api_upload("/documents/upload", files)

        if "error" in result:
            st.error(f"Upload failed: {result['error']}")
        else:
            st.success(result.get("message", "Document processed successfully"))

            cols = st.columns(4)
            cols[0].metric("Pages", result.get("page_count", 0))
            cols[1].metric("Chunks", result.get("chunk_count", 0))
            cols[2].metric("Entities", result.get("entity_count", 0))
            cols[3].metric("Status", result.get("status", ""))

    st.markdown(glass_divider(), unsafe_allow_html=True)
    st.markdown(glass_section("Sample Documents"), unsafe_allow_html=True)
    st.markdown("""
    Download these sample documents to test the platform:

    1. **Standard Operating Procedure** - Pump operation procedure
    2. **Equipment Inventory** - Plant equipment list (CSV)
    3. **Maintenance Work Orders** - Historical work order records (CSV)
    4. **Incident Report** - Near-miss gas leak report
    5. **Regulatory Checklist** - OISD / Factory Act compliance items

    *(Sample files are pre-loaded in `data/sample_docs/`)*
    """)


def graph_page():
    st.markdown(glass_title("Knowledge Graph Explorer"), unsafe_allow_html=True)
    st.markdown('<div class="glass-subtitle">Explore entities and relationships in the knowledge graph.</div>', unsafe_allow_html=True)

    summary = api_get("/knowledge-graph/summary")
    node_counts = summary.get("node_counts", {}) if "error" not in summary else {}

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(glass_section("Node Types"), unsafe_allow_html=True)
        if node_counts:
            df = pd.DataFrame([
                {"Type": k, "Count": v} for k, v in node_counts.items()
            ])
            st.dataframe(df, hide_index=True, use_container_width=True)

        st.markdown(glass_section("Search"), unsafe_allow_html=True)
        search_q = st.text_input("Search nodes by name, ID, or keyword")
        if search_q:
            results = api_get(f"/knowledge-graph/search?q={search_q}")
            if "error" in results:
                st.warning("Search unavailable. Ensure sample data is ingested.")
            elif "results" in results:
                for r in results["results"]:
                    label = r.get("label", "")
                    name = r.get("name", "")
                    st.markdown(f"- **{label}**: {name}")
                if not results["results"]:
                    st.info("No matching nodes found")

        st.markdown(glass_section("Explore Node"), unsafe_allow_html=True)
        node_id = st.text_input("Enter Node ID to explore connections")
        if node_id:
            with st.spinner("Loading subgraph..."):
                subgraph = api_get(f"/knowledge-graph/explore?node_id={node_id}&depth=2")
            if "error" in subgraph:
                st.error(f"Node '{node_id}' not found or API error.")
            else:
                nodes = subgraph.get("nodes", [])
                rels = subgraph.get("relationships", [])
                st.metric("Connected Nodes", len(nodes))
                st.metric("Relationships", len(rels))
                st.session_state["subgraph_data"] = subgraph

    with col2:
        st.markdown(glass_section("Graph Visualization"), unsafe_allow_html=True)

        subgraph = st.session_state.get("subgraph_data", None)
        if subgraph and subgraph.get("nodes"):
            nodes_list = subgraph["nodes"]
            rels_list = subgraph.get("relationships", [])

            net = Network(height="500px", width="100%", directed=True, bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")

            color_map = {
                "Equipment": "#4CAF50", "Document": "#2196F3",
                "Regulation": "#FF9800", "Incident": "#F44336",
                "Personnel": "#9C27B0", "Permit": "#00BCD4",
                "WorkOrder": "#FF5722",
            }

            for n in nodes_list:
                label = n.get("label", "Unknown")
                node_id_val = n.get("id", "")
                color = color_map.get(label, "#607D8B")
                display = n.get("properties", {}).get("name") or n.get("properties", {}).get("title") or node_id_val
                net.add_node(node_id_val, label=display, title=f"{label}: {node_id_val}", color=color, size=25)

            for r in rels_list:
                src = r.get("source", "")
                tgt = r.get("target", "")
                rel_type = r.get("type", "RELATED_TO")
                if src and tgt:
                    net.add_edge(src, tgt, title=rel_type, label=rel_type, arrows="to")

            net.set_options("""
            {
              "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100},
                "solver": "forceAtlas2Based"
              },
              "interaction": {
                "hover": true,
                "tooltipDelay": 200,
                "zoomView": true,
                "dragView": true
              }
            }
            """)

            html_path = "/tmp/kgraph.html"
            net.save_graph(html_path)
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=550, scrolling=True)
        elif search_q and "results" in locals() and "error" not in results and results.get("results"):
            st.info("Search results shown on the left. Enter a Node ID in the Explore field to see the graph.")
        else:
            st.info("Enter a Node ID in the left panel to visualize the knowledge graph interactively.")


def copilot_page():
    st.markdown(glass_title("AI Knowledge Copilot"), unsafe_allow_html=True)
    st.markdown('<div class="glass-subtitle">Ask questions about your industrial knowledge base.</div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    query = st.chat_input("Ask a question...")

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})

        with st.spinner("Thinking... (LLM is running on CPU, this may take 30-60s)"):
            result = api_post("/query/chat", {"message": query})

        if "error" in result:
            answer = f"⚠️ Error: {result['error']}"
            sources = []
            agent_trace = []
        else:
            answer = result.get("answer", "No answer generated")
            sources = result.get("sources", [])
            agent_trace = result.get("agent_trace", [])

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "agent_trace": agent_trace,
        })

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("Sources", expanded=False):
                    for s in msg["sources"]:
                        st.caption(f"📄 {s}")
            if msg["role"] == "assistant" and msg.get("agent_trace"):
                with st.expander("Agent Trace", expanded=False):
                    for t in msg["agent_trace"]:
                        st.caption(f"🤖 {t.get('agent', '')}: {t.get('summary', '')}")

    if st.session_state.chat_history:
        if st.button("Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Example Queries")
    st.sidebar.markdown("""
    Click to try:
    - "What is the operating procedure for the pump?"
    - "Analyze maintenance history for Pump-001"
    - "Check compliance with OISD standards"
    - "Show me patterns in near-miss incidents"
    - "What equipment is in Zone A?"
    - "Are there any active permits for the boiler area?"
    """)


def maintenance_page():
    st.markdown(glass_title("Maintenance Intelligence"), unsafe_allow_html=True)
    st.markdown('<div class="glass-subtitle">Predictive maintenance, work order analysis, and root cause insights.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Predictive Analysis", "Root Cause Analysis", "Work Orders"])

    with tab1:
        st.markdown(glass_section("Predictive Maintenance"), unsafe_allow_html=True)
        equipment_id = st.text_input("Equipment ID", key="pm_eq")
        days = st.slider("Forecast horizon (days)", 7, 90, 30)

        if st.button("Analyze", type="primary"):
            with st.spinner("Analyzing... (LLM on CPU, ~30-60s)"):
                result = api_post("/maintenance/predict", {
                    "equipment_id": equipment_id,
                    "days_ahead": days,
                })
            if "error" in result:
                st.error(result["error"])
            else:
                st.markdown("#### Recommendations")
                st.markdown(result.get("details", "Analysis complete."))

                recs = result.get("recommendations", [])
                if recs:
                    df = pd.DataFrame(recs)
                    st.dataframe(df, use_container_width=True)

    with tab2:
        st.markdown(glass_section("Root Cause Analysis"), unsafe_allow_html=True)
        rca_eq = st.text_input("Equipment ID (optional)", key="rca_eq")
        rca_desc = st.text_area("Incident Description", "Describe the failure or incident...")

        if st.button("Run RCA", type="primary"):
            with st.spinner("Analyzing root causes... (LLM on CPU, ~30-60s)"):
                result = api_post("/maintenance/rca", {
                    "equipment_id": rca_eq if rca_eq else None,
                    "description": rca_desc,
                })
            if "error" in result:
                st.error(result["error"])
            else:
                st.markdown("#### Root Cause Analysis")
                st.markdown(result.get("maintenance_analysis", ""))

                if result.get("lessons_analysis"):
                    with st.expander("Lessons Learned Analysis"):
                        st.markdown(result["lessons_analysis"])

    with tab3:
        st.markdown(glass_section("Work Order History"), unsafe_allow_html=True)
        wo_eq = st.text_input("Equipment ID", key="wo_eq")
        if wo_eq:
            data = api_get(f"/knowledge-graph/equipment/{wo_eq}/work-orders")
            wos = data.get("work_orders", [])
            if wos:
                df = pd.DataFrame(wos)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No work orders found for this equipment")


def compliance_page():
    st.markdown(glass_title("Compliance Intelligence"), unsafe_allow_html=True)
    st.markdown('<div class="glass-subtitle">Regulatory compliance monitoring and gap analysis.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(glass_section("Compliance Check"), unsafe_allow_html=True)
        eq_id = st.text_input("Equipment ID (optional)")
        reg_id = st.text_input("Regulation ID (optional)")

        if st.button("Run Compliance Check", type="primary"):
            with st.spinner("Analyzing compliance... (LLM on CPU, ~30-60s)"):
                result = api_post("/compliance/check", {
                    "equipment_id": eq_id if eq_id else None,
                    "regulation_id": reg_id if reg_id else None,
                })
            if "error" in result:
                st.error(result["error"])
            else:
                st.markdown("#### Compliance Analysis")
                st.markdown(result.get("answer", ""))

                sources = result.get("sources", [])
                if sources:
                    with st.expander("Sources"):
                        for s in sources:
                            st.caption(f"📄 {s}")

    with col2:
        st.markdown(glass_section("Framework Coverage"), unsafe_allow_html=True)
        summary = api_get("/knowledge-graph/summary")
        node_counts = summary.get("node_counts", {}) if "error" not in summary else {}

        reg_count = node_counts.get("Regulation", 0)
        equip_count = node_counts.get("Equipment", 0)

        fig = go.Figure()

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=reg_count,
            title={"text": "Regulations"},
            domain={"row": 0, "column": 0},
        ))
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=equip_count,
            title={"text": "Equipment Tracked"},
            domain={"row": 0, "column": 1},
        ))

        fig.update_layout(
            grid={"rows": 1, "columns": 2},
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(glass_section("Regulatory Frameworks"), unsafe_allow_html=True)
        frameworks = [
            ("OISD", "Oil Industry Safety Directorate"),
            ("Factory Act, 1948", "Sections 21-38"),
            ("DGMS", "Mines Safety"),
            ("PESO", "Explosives Safety"),
            ("CPCB", "Pollution Control"),
            ("BIS / ISO", "Quality Standards"),
        ]
        fw_html = '<div class="glass-card" style="padding:1rem 1.5rem;">'
        for name, desc in frameworks:
            fw_html += f'<div style="margin-bottom:0.4rem;"><strong style="color:#38bdf8;">{name}</strong> <span style="color:#94a3b8;">— {desc}</span></div>'
        fw_html += '</div>'
        st.markdown(fw_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
