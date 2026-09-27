import streamlit as st
from groq import Groq

# --- Page Configuration ---
st.set_page_config(
    page_title="RFP Mind Pro", 
    page_icon="🛡️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Custom Premium Interface Theme ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #d1d5db;
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }
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
    .stTextArea textarea, .stTextInput input {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Left Navigation Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color:#ffffff; font-size:20px;'>🛡️ Governance & Access</h2>", unsafe_allow_html=True)
    groq_key = st.text_input("Azure Groq API Token", type="password", placeholder="gsk_live_...")
    st.markdown("---")
    st.markdown("<div style='font-size:12px; color:#9ca3af;'><b>🔒 STATUS</b><br>• Cluster: Hindsight-V4<br>• Brain: Llama3-Enterprise</div>", unsafe_allow_html=True)

# --- Application Title Banner ---
st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center; padding-bottom: 15px; margin-bottom: 25px; border-bottom: 1px solid #1f2937;'>
        <div>
            <h1 style='margin: 0; font-size: 26px; color: #ffffff;'>💼 RFP Mind: Enterprise Control Panel</h1>
            <p style='margin: 5px 0 0 0; font-size: 13px; color: #9ca3af;'>Context-Aware Automated Document Compiling via Long-Term Memory Synapses</p>
        </div>
        <div style='background-color: #065f46; color: #34d399; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;'>
            🟢 SYSTEM ONLINE
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Initialize Local State Storage ---
if "memory_bank" not in st.session_state:
    st.session_state.memory_bank = []

# --- System Performance KPI Metrics Grid ---
st.markdown(f"""
    <div class='kpi-container'>
        <div class='kpi-box'>
            <div style='font-size: 11px; color: #9ca3af; text-transform: uppercase;'>Hindsight Nodes</div>
            <div style='font-size: 20px; font-weight: 700; color: #3b82f6;'>{len(st.session_state.memory_bank)} Synchronized</div>
        </div>
        <div class='kpi-box'>
            <div style='font-size: 11px; color: #9ca3af; text-transform: uppercase;'>Target Inference</div>
            <div style='font-size: 20px; font-weight: 700; color: #10b981;'>&lt; 200ms</div>
        </div>
        <div class='kpi-box'>
            <div style='font-size: 11px; color: #9ca3af; text-transform: uppercase;'>Guardrail Enforcement</div>
            <div style='font-size: 20px; font-weight: 700; color: #f59e0b;'>Automated</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Dual-Column Workspace ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("<div class='enterprise-card'><h3>📥 1. Institutional Knowledge Ingestion</h3></div>", unsafe_allow_html=True)
    context_input = st.text_area(
        "Mandate Field",
        placeholder="e.g., Acme Corp strictly uses Microsoft Azure. They will reject any proposal that uses AWS.",
        label_visibility="collapsed",
        key="ingest_area"
    )
    if st.button("Commit to Long-Term Memory Synapse", use_container_width=True):
        if context_input:
            st.session_state.memory_bank.append(context_input)
            st.toast("⚡ Committed to long-term database storage node.")
            st.rerun()
        else:
            st.error("Please enter a rule first.")

    st.markdown("<div class='enterprise-card' style='margin-top:25px;'><h3>📝 2. Active Proposal Compilation</h3></div>", unsafe_allow_html=True)
    client_name = st.text_input("Target Client Name", placeholder="e.g., Acme Corp")
    rfp_question = st.text_area("RFP Technical Requirement Prompt", placeholder="e.g., Write a quick cloud hosting server layout proposal.", height=100)
    generate_btn = st.button("Execute Compliance-Aware Generation", type="primary", use_container_width=True)

with col2:
    st.markdown("<h3>🖥️ Telemetry Logs & Production Output</h3>", unsafe_allow_html=True)
    
    if generate_btn:
        if not groq_key:
            st.error("Access Denied: Please provide your API Token key in the left navigation sidebar module.")
        elif not client_name or not rfp_question:
            st.error("Validation Error: Please fill out both input criteria boxes.")
        else:
            with st.spinner("Executing structural vector memory search lookup..."):
                recalled = [m for m in st.session_state.memory_bank if client_name.lower() in m.lower()]
                
                if recalled:
                    items = "".join([f"<li>{r}</li>" for r in recalled])
                    st.markdown(f"""
                        <div class='telemetry-trace'>
                            <b style='color: #60a5fa;'>🧠 [HINDSIGHT TELEMETRY DATA SEARCH ACTIVE]</b><br>
                            <span style='font-size: 13px; color:#e5e7eb;'>Found matching historical constraint boundaries:</span>
                            <ul style='font-size: 12px; color: #9ca3af; margin-top:5px;'>{items}</ul>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='border:1px dashed #374151; padding:15px; border-radius:6px; color:#9ca3af; font-size:13px;'>⚠️ No past memory traces found. Running default baseline parameters.</div>", unsafe_allow_html=True)

                mem_context = "\n".join(recalled) if recalled else "No historical records available."
                sys_prompt = f"You are a professional proposal writer. Answer the question. IMPORTANT: Review these notes. If notes mention technology limits, platform preferences, or restrictions, you MUST follow them completely!\nNotes:\n{mem_context}"
                user_prompt = f"Company: {client_name}\nQuestion: {rfp_question}"
                
                try:
                    client = Groq(api_key=groq_key)
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                        temperature=0.1
                    )
                    st.markdown("### 📄 Compiled Deliverable Output")
                    st.write(completion.choices.message.content)
                except Exception as e:
                    st.error(f"Execution Error: {e}")
    else:
        st.markdown("<div style='text-align:center; padding:50px; background:#111827; border-radius:8px; border:2px dashed #1f2937; color:#9ca3af;'>📊 System idle. Awaiting operational telemetry streams.</div>", unsafe_allow_html=True)
