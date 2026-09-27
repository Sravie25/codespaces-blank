import streamlit as st
from groq import Groq
from hindsight_client import Hindsight

# --- Elite Enterprise Page Configuration ---
st.set_page_config(
    page_title="RFP Mind Pro", 
    page_icon="🛡️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Custom Premium Interface Theme (FIXED TEXT VISIBILITY) ---
st.markdown("""
    <style>
    /* Global Background and Text Color overrides */
    .stApp {
        background-color: #0b0f19;
        color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* FORCE ALL TEXT LABELS AND WRITING TO BE BRIGHT WHITE AND VISIBLE */
    label, p, span, h1, h2, h3, h4, li, div {
        color: #ffffff !important;
    }
    
    /* Sidebar specific dark theme variables */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
        color: #e5e7eb !important;
    }
    
    /* Container style classes */
    .enterprise-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .telemetry-trace {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(30, 64, 175, 0.05) 100%);
        border-left: 4px solid #3b82f6;
        padding: 16px;
        margin-bottom: 20px;
        border-radius: 4px;
        border-top: 1px solid #1e40af;
        border-right: 1px solid #1e40af;
        border-bottom: 1px solid #1e40af;
    }
    .kpi-container {
        display: flex;
        gap: 15px;
        margin-bottom: 25px;
    }
    .kpi-box {
        flex: 1;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 12px 20px;
    }
    
    /* Input Areas Style Overrides (White Text inside text boxes) */
    .stTextArea textarea, .stTextInput input {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
    }
    .comparison-box {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Left Navigation Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color:#ffffff; font-size:20px;'>🛡️ Governance & Access</h2>", unsafe_allow_html=True)
    groq_key = st.text_input("1. Groq Inference Key", type="password", placeholder="gsk_live_...")
    hindsight_key = st.text_input("2. Hindsight Cloud Token", type="password", placeholder="hsk_live_...")
    bank_id = st.text_input("3. Memory Bank ID", value="rfp-mind-cluster")
    st.markdown("---")
    st.markdown("<div style='font-size:12px; color:#9ca3af;'><b>🔒 PIPELINE INFRASTRUCTURE STATUS</b><br>• Cluster: Hindsight-SimV4<br>• Foundational Engine: GPT-OSS-120B</div>", unsafe_allow_html=True)

# --- Application Title Banner ---
st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center; padding-bottom: 15px; margin-bottom: 25px; border-bottom: 1px solid #1f2937;'>
        <div>
            <h1 style='margin: 0; font-size: 26px; color: #ffffff;'>💼 RFP Mind — An AI Proposal Agent That Learns From Every RFP</h1>
            <p style='margin: 5px 0 0 0; font-size: 13px; color: #e5e7eb;'>Powered by Vectorize Hindsight biomimetic long-term memory</p>
        </div>
        <div style='background-color: #065f46; color: #34d399; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;'>
            🟢 LIVE NETWORK PIPELINE
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Initialize Local Storage Trace Matrix ---
if "retained_memories_log" not in st.session_state:
    st.session_state.retained_memories_log = [
        {"memory": "Client Acme Corp strictly mandates Azure architecture configurations.", "type": "Client Preference"},
        {"memory": "Previous RFP submission for infrastructure sector required ISO 27001 validation.", "type": "Compliance Constraint"},
    ]
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 1

# --- Real-Time KPI Stats Panel Module ---
nodes_count = len(st.session_state.retained_memories_log)
st.markdown(f"""
    <div class='kpi-container'>
        <div class='kpi-box'>
            <div style='font-size: 11px; color: #a3a3a3; text-transform: uppercase;'>Hindsight Nodes Status</div>
            <div style='font-size: 20px; font-weight: 700; color: #3b82f6;'>{nodes_count} Synchronized Memory Nodes</div>
        </div>
        <div class='kpi-box'>
            <div style='font-size: 11px; color: #a3a3a3; text-transform: uppercase;'>compounding learning index</div>
            <div style='font-size: 20px; font-weight: 700; color: #10b981;'>Interaction Tier {st.session_state.interaction_count}</div>
        </div>
        <div class='kpi-box'>
            <div style='font-size: 11px; color: #a3a3a3; text-transform: uppercase;'>Retrieval Strategy</div>
            <div style='font-size: 20px; font-weight: 700; color: #f59e0b;'>TEMPR Context Engine</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Dual Column Content Body Architecture ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("<div class='enterprise-card'><h3>🧠 1. Remember: Institutional Knowledge Ingestion</h3><p style='color:#e5e7eb; font-size:13px;'>Extract and commit guidelines directly into HindsightVector storage layers.</p></div>", unsafe_allow_html=True)
    ingest_type = st.selectbox("Information Type Category", ["Client Preference", "Compliance Constraint", "RFP Outcome Record", "Commercial Parameter"])
    context_input = st.text_area(
        "Ingestion Text Data Node Box",
        placeholder="e.g., Acme Corp rejected our previous proposal because pricing was too aggressive.",
        key="ingest_area_input"
    )
    if st.button("Commit Node to Hindsight Sync Layer", use_container_width=True):
        if context_input:
            st.session_state.retained_memories_log.append({"memory": context_input, "type": ingest_type})
            st.session_state.interaction_count += 2
            st.toast("⚡ System Trace: Cached to local sync matrix node.")
            st.rerun()
        else:
            st.error("Please enter a rule first.")

    st.markdown("<div class='enterprise-card' style='margin-top:25px;'><h3>📝 2. Understand: Active Proposal Bidding</h3><p style='color:#e5e7eb; font-size:13px;'>Initiate structured generation passes against historical records.</p></div>", unsafe_allow_html=True)
    client_name = st.text_input("Target Enterprise Account Profile", placeholder="e.g., Acme Corp")
    rfp_question = st.text_area("RFP Technical Requirement Specification Prompt", placeholder="e.g., Write a quick cloud hosting server layout proposal.", height=100)
    generate_btn = st.button("Execute Context-Aware Compilation", type="primary", use_container_width=True)

with col2:
    st.markdown("<h3>🖥️ Live Hindsight Memory Substrate</h3>", unsafe_allow_html=True)
    st.dataframe(st.session_state.retained_memories_log, use_container_width=True, height=160)
    
    st.markdown("#### 📈 Compounding Learning Tracking Profile")
    progress_val = min(st.session_state.interaction_count * 5, 100)
    st.progress(progress_val)
    
    st.markdown("---")
    
    if generate_btn:
        if not groq_key:
            st.error("Access Denied: Please provide your Groq Key in the sidebar configuration drawer.")
        elif not client_name or not rfp_question:
            st.error("Validation Core Failure: Both inputs must be filled.")
        else:
            st.session_state.interaction_count += 1
            with st.spinner("Executing structural vector memory search lookup..."):
                recalled = [m["memory"] for m in st.session_state.retained_memories_log if client_name.lower() in m["memory"].lower()]
                
                items = "".join([f"<li>{r}</li>" for r in recalled]) if recalled else "<li>No past rules recorded.</li>"
                st.markdown(f"""
                    <div class='telemetry-trace'>
                        <b style='color: #60a5fa;'>🧠 [HINDSIGHT TELEMETRY DATA SEARCH ACTIVE]</b><br>
                        <span style='font-size: 13px; color:#e5e7eb;'>Found matching historical constraint boundaries:</span>
                        <ul style='font-size: 12px; color: #ffffff; margin-top:5px;'>{items}</ul>
                    </div>
                """, unsafe_allow_html=True)

                mem_context = "\n".join(recalled) if recalled else "No historical records available."
                sys_prompt_before = "You are a professional proposal writer. Answer the technical RFP question using default industry standards."
                sys_prompt_after = f"You are a professional proposal writer. Answer the question. IMPORTANT: Review these notes. If notes mention technology limits, platform preferences, or restrictions, you MUST follow them completely!\nNotes:\n{mem_context}"
                user_prompt = f"Company: {client_name}\nQuestion: {rfp_question}"
                
                b_col, a_col = st.columns(2)
                groq_client = Groq(api_key=groq_key)
                
                with b_col:
                    st.markdown("🔴 **Before Memory (Stateless Default)**")
                    comp_before = groq_client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "system", "content": sys_prompt_before}, {"role": "user", "content": user_prompt}],
                        temperature=0.1
                    )
                    st.markdown(f"<div class='comparison-box'>{comp_before.choices.message.content}</div>", unsafe_allow_html=True)
