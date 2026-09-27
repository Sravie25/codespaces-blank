import os
import textwrap
import datetime
import streamlit as st
from groq import Groq
from hindsight_client import Hindsight

# ============================================================
# RFP MIND — Hindsight-powered RFP Proposal Agent
# ============================================================

HINDSIGHT_API_URL = "https://api.hindsight.vectorize.io"
DEFAULT_BANK_ID = "rfp-mind-cluster-v3"
GROQ_MODEL = "openai/gpt-oss-120b"

st.set_page_config(
    page_title="RFP Mind Pro - Enterprise Control Panel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
_original_st_markdown = st.markdown


def safe_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        body = textwrap.dedent(body)
    return _original_st_markdown(body, *args, **kwargs)


st.markdown = safe_markdown

# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #ffffff !important;
        font-family: 'Segoe UI', sans-serif;
    }

    label, p, span, h1, h2, h3, h4, li, div, small {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #d1d5db !important;
    }

    .enterprise-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 22px;
        margin-bottom: 25px;
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
        padding: 14px 20px;
    }

    .stTextArea textarea,
    .stTextInput input {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
    }

    .memory-box {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }

    .decision-badge {
        background-color: #1e293b;
        border-left: 3px solid #f59e0b;
        padding: 8px 12px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-size: 12.5px;
    }

    .success-box {
        background-color: #052e24;
        border: 1px solid #047857;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
    }

    .warning-box {
        background-color: #422006;
        border: 1px solid #b45309;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "telemetry_logs": [],
    "learning_tier": 1,
    "retrieved_memories": [],
    "last_proposal": "",
    "baseline_proposal": "",
    "last_client": "",
    "last_rfp": "",
    "last_memory_count": 0,
    "hindsight_ok": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def log(message: str):
    stamp = datetime.datetime.now().strftime("%H:%M:%S")

    st.session_state.telemetry_logs.insert(
        0,
        f"[{stamp}] {message}"
    )

    st.session_state.telemetry_logs = (
        st.session_state.telemetry_logs[:40]
    )


# ============================================================
# HINDSIGHT FUNCTIONS
# ============================================================

def get_hindsight(api_key: str):

    if not api_key:
        raise ValueError(
            "Hindsight API key is required."
        )

    return Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=api_key,
        timeout=30.0,
    )


def ensure_bank(client: Hindsight, bank_id: str):

    try:

        client.create_bank(
            bank_id=bank_id,
            name="RFP Mind Enterprise Memory",
        )

        log(
            f"Hindsight memory bank created: {bank_id}"
        )

    except Exception:
        # Bank may already exist.
        pass


def extract_memory_texts(recall_response):

    memories = []

    for item in getattr(
        recall_response,
        "results",
        []
    ) or []:

        text_value = getattr(
            item,
            "text",
            None
        )

        if text_value:

            memories.append(
                {
                    "text": str(text_value),
                    "type": str(
                        getattr(
                            item,
                            "type",
                            "memory"
                        )
                    ),
                }
            )

    return memories


def recall_hindsight(
    api_key: str,
    bank_id: str,
    query: str
):

    client = get_hindsight(api_key)

    ensure_bank(
        client,
        bank_id
    )

    result = client.recall(
        bank_id=bank_id,
        query=query,
        max_tokens=5000,
        budget="mid",
    )

    return extract_memory_texts(result)


def retain_hindsight(
    api_key: str,
    bank_id: str,
    content: str,
    context: str,
    document_id: str,
):

    client = get_hindsight(api_key)

    ensure_bank(
        client,
        bank_id
    )

    client.retain(
        bank_id=bank_id,
        content=content,
        context=context,
        document_id=document_id,
        retain_async=False,
    )


# ============================================================
# GROQ FUNCTION
# ============================================================

def groq_generate(
    api_key: str,
    system_prompt: str,
    user_prompt: str
):

    if not api_key:
        raise ValueError(
            "Groq API key is required."
        )

    client = Groq(
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            },
        ],

        temperature=0.25,
        max_completion_tokens=4000,
        reasoning_effort="medium",
    )

    return response.choices[0].message.content


def build_memory_context(memories):

    if not memories:

        return (
            "No relevant Hindsight memories "
            "were retrieved."
        )

    return "\n".join(
        f"- [{m['type']}] {m['text']}"
        for m in memories
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "<h2 style='font-size:19px;'>"
        "🛡️ Governance & Access"
        "</h2>",
        unsafe_allow_html=True,
    )

    st.caption(
        "API keys are masked and used only "
        "for the current session."
    )

    groq_key = st.text_input(
        "1. Groq Inference Token",
        value=os.getenv(
            "GROQ_API_KEY",
            ""
        ),
        type="password",
        placeholder="gsk_...",
    )

    hindsight_key = st.text_input(
        "2. Hindsight Production Token",
        value=os.getenv(
            "HINDSIGHT_API_KEY",
            ""
        ),
        type="password",
        placeholder="hsk_...",
    )

    bank_id = st.text_input(
        "3. Hindsight Memory Bank ID",
        value=os.getenv(
            "HINDSIGHT_BANK_ID",
            DEFAULT_BANK_ID
        ),
    )

    st.markdown("---")

    if st.button(
        "🔌 Test Hindsight Connection",
        use_container_width=True
    ):

        try:

            client = get_hindsight(
                hindsight_key
            )

            ensure_bank(
                client,
                bank_id
            )

            client.recall(
                bank_id=bank_id,
                query="RFP Mind connection test",
                max_tokens=500,
                budget="low",
            )

            st.session_state.hindsight_ok = True

            log(
                "Hindsight connection verified successfully."
            )

            st.success(
                "Hindsight connected."
            )

        except Exception as exc:

            st.session_state.hindsight_ok = False

            log(
                "Hindsight connection failed: "
                + type(exc).__name__
            )

            st.error(
                f"Hindsight connection failed: {exc}"
            )

    if st.session_state.hindsight_ok:

        st.markdown(
            """
            <div class='success-box'>
            🟢 Hindsight Cloud: VERIFIED
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class='warning-box'>
            🟡 Hindsight: Not verified yet
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown(
        """
        <div style='font-size:11px; color:#d1d5db;'>

        <b>ARCHITECTURE</b><br>

        • Hindsight Cloud memory<br>
        • Groq GPT-OSS 120B reasoning<br>
        • Recall → Generate → Retain loop<br>
        • No fake local memory source

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div style='display:flex;
                justify-content:space-between;
                align-items:center;
                padding-bottom:12px;
                margin-bottom:20px;
                border-bottom:1px solid #1f2937;'>

        <div>

            <h1 style='margin:0; font-size:26px;'>
                💼 RFP Mind —
                An AI Proposal Agent That Learns From Every RFP
            </h1>

            <p style='margin:5px 0 0 0; font-size:13px;'>
                Hindsight long-term memory +
                Groq agentic proposal generation
            </p>

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPI DASHBOARD
# ============================================================

connection_label = (
    "VERIFIED"
    if st.session_state.hindsight_ok
    else "NOT VERIFIED"
)

memory_label = (
    f"{st.session_state.last_memory_count} Retrieved"
    if st.session_state.last_memory_count
    else "No Retrieval Yet"
)

st.markdown(
    f"""
    <div class='kpi-container'>

        <div class='kpi-box'>

            <div style='font-size:11px;'>
                HINDSIGHT CONNECTION
            </div>

            <div style='font-size:20px;
                        font-weight:700;'>
                {connection_label}
            </div>

        </div>


        <div class='kpi-box'>

            <div style='font-size:11px;'>
                LAST MEMORY RETRIEVAL
            </div>

            <div style='font-size:20px;
                        font-weight:700;'>
                {memory_label}
            </div>

        </div>


        <div class='kpi-box'>

            <div style='font-size:11px;'>
                COMPOUNDING LEARNING
            </div>

            <div style='font-size:20px;
                        font-weight:700;'>
                Interaction Tier
                {st.session_state.learning_tier}
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MAIN WORKSPACE
# ============================================================

col1, col2 = st.columns(
    2,
    gap="large"
)


# ============================================================
# MEMORY INGESTION
# ============================================================

with col1:

    st.markdown(
        """
        <div class='enterprise-card'>

        <h3>
        🧠 1. Remember:
        Institutional Knowledge Ingestion
        </h3>

        <p style='font-size:13px;'>
        Store real organizational knowledge in
        Hindsight so future RFPs can retrieve
        and use it.
        </p>
        """,
        unsafe_allow_html=True,
    )

    ingest_client = st.text_input(
        "Client / Organization",
        placeholder="e.g., Acme Corp",
        key="ingest_client",
    )

    ingest_type = st.selectbox(
        "Information Type",
        [
            "Client Preference",
            "Compliance Mandate",
            "RFP Outcome",
            "Commercial Framework",
            "Successful Proposal Pattern",
            "Company Capability",
        ],
    )

    context_input = st.text_area(
        "Knowledge to Remember",

        placeholder=(
            "e.g., Acme Corp requires "
            "Microsoft Azure and ISO 27001. "
            "A previous proposal was rejected "
            "because pricing was too aggressive."
        ),

        height=130,

        key="active_data_box",
    )

    if st.button(
        "🧠 Commit Memory to Hindsight",
        use_container_width=True,
        type="primary",
    ):

        if not hindsight_key:

            st.error(
                "Enter the Hindsight Production Token first."
            )

        elif (
            not ingest_client.strip()
            or not context_input.strip()
        ):

            st.error(
                "Client name and memory content are required."
            )

        else:

            try:

                content = (
                    f"Client: {ingest_client.strip()}\n"
                    f"Information type: {ingest_type}\n"
                    f"Fact: {context_input.strip()}"
                )

                retain_hindsight(
                    hindsight_key,
                    bank_id,
                    content=content,
                    context=(
                        "RFP organizational knowledge — "
                        + ingest_type
                    ),
                    document_id=(
                        "knowledge-"
                        + ingest_client.strip()
                        .lower()
                        .replace(" ", "-")
                    ),
                )

                st.session_state.learning_tier += 1

                log(
                    f"Hindsight RETAIN successful: "
                    f"{ingest_type} for "
                    f"{ingest_client.strip()}."
                )

                st.success(
                    "Memory stored in Hindsight successfully. "
                    "It can now be recalled by future RFPs."
                )

            except Exception as exc:

                log(
                    "Hindsight RETAIN failed: "
                    + type(exc).__name__
                )

                st.error(
                    f"Memory storage failed: {exc}"
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# ACTIVE RFP
# ============================================================

with col1:

    st.markdown(
        """
        <div class='enterprise-card'>

        <h3>
        📝 2. Understand:
        Active Proposal Bidding
        </h3>

        <p style='font-size:13px;'>
        Retrieve relevant Hindsight memories and
        use them to generate a context-aware proposal.
        </p>
        """,
        unsafe_allow_html=True,
    )

    client_name = st.text_input(
        "Target Enterprise Client",
        placeholder="e.g., Acme Corp",
    )

    rfp_question = st.text_area(
        "RFP Technical Requirement",

        placeholder=(
            "e.g., Design a cloud infrastructure "
            "proposal for Acme Corp covering "
            "architecture, security, compliance "
            "and pricing."
        ),

        height=130,
    )

    baseline_btn = st.button(
        "📄 Generate Baseline (No Hindsight)",
        use_container_width=True,
    )

    generate_btn = st.button(
        "🧠 Execute Context-Aware Compilation",
        type="primary",
        use_container_width=True,
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# RIGHT SIDE — MEMORY
# ============================================================

with col2:

    st.markdown(
        "### 🖥️ Live Hindsight Memory Retrieval"
    )

    if st.session_state.retrieved_memories:

        for memory in st.session_state.retrieved_memories:

            st.markdown(
                f"""
                <div class='memory-box'>

                <b>
                🧠 {memory['type']}
                </b>
                <br>

                {memory['text']}

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "No retrieval yet. Run a context-aware "
            "compilation to show real memories returned "
            "by Hindsight."
        )

    st.markdown(
        "### ⏳ Live Pipeline Telemetry"
    )

    if st.session_state.telemetry_logs:

        st.text_area(
            "Console",

            value="\n".join(
                st.session_state.telemetry_logs
            ),

            height=180,

            disabled=True,

            label_visibility="collapsed",
        )

    else:

        st.info(
            "Pipeline telemetry will appear here."
        )


# ============================================================
# BASELINE GENERATION
# ============================================================

if baseline_btn:

    if not groq_key:

        st.error(
            "Enter the Groq Inference Token first."
        )

    elif (
        not client_name.strip()
        or not rfp_question.strip()
    ):

        st.error(
            "Enter both the client name and RFP requirement."
        )

    else:

        with st.spinner(
            "Generating baseline proposal without memory..."
        ):

            try:

                baseline_system = """
You are an enterprise proposal-writing assistant.

Generate a professional RFP proposal using ONLY
the current RFP request.

Do not assume historical client preferences
or previous outcomes.

Do not invent client-specific facts.
"""

                baseline = groq_generate(

                    groq_key,

                    baseline_system,

                    f"""
Client:
{client_name.strip()}

Current RFP:
{rfp_question.strip()}

Generate:

1. Executive Summary
2. Proposed Solution
3. Technical Architecture
4. Security & Compliance
5. Delivery Plan
6. Assumptions / Open Questions
7. Commercial Considerations
""",
                )

                st.session_state.baseline_proposal = baseline

                log(
                    "Baseline proposal generated WITHOUT Hindsight."
                )

            except Exception as exc:

                log(
                    "Baseline generation failed: "
                    + type(exc).__name__
                )

                st.error(
                    f"Baseline generation failed: {exc}"
                )


# ============================================================
# MEMORY-AWARE GENERATION
# ============================================================

if generate_btn:

    if not groq_key:

        st.error(
            "Enter the Groq Inference Token first."
        )

    elif not hindsight_key:

        st.error(
            "Enter the Hindsight Production Token first."
        )

    elif (
        not client_name.strip()
        or not rfp_question.strip()
    ):

        st.error(
            "Enter both the client name and RFP requirement."
        )

    else:

        try:

            # ------------------------------------------------
            # STEP 1 — RECALL
            # ------------------------------------------------

            with st.spinner(
                "1/3 — Retrieving relevant Hindsight memories..."
            ):

                query = f"""
For an upcoming RFP for {client_name.strip()},
what historical organizational knowledge should
influence the proposal?

Current RFP:

{rfp_question.strip()}

Return relevant:

- client preferences
- compliance requirements
- previous RFP outcomes
- commercial constraints
- successful proposal patterns
- company capabilities
"""

                memories = recall_hindsight(
                    hindsight_key,
                    bank_id,
                    query,
                )

                st.session_state.retrieved_memories = memories

                st.session_state.last_memory_count = len(
                    memories
                )

                log(
                    "Hindsight RECALL returned "
                    f"{len(memories)} relevant memories."
                )


            # ------------------------------------------------
            # BUILD MEMORY CONTEXT
            # ------------------------------------------------

            memory_context = build_memory_context(
                memories
            )


            # ------------------------------------------------
            # STEP 2 — GENERATE
            # ------------------------------------------------

            with st.spinner(
                "2/3 — Generating memory-aware proposal..."
            ):

                system_prompt = """
You are RFP Mind,
an enterprise proposal agent.

Your job is to generate a high-quality
RFP response using:

1. The current RFP.
2. Relevant memories retrieved from Hindsight.

STRICT MEMORY RULES:

- Treat retrieved memories as historical context,
  not unquestionable truth.

- Do not invent client facts.

- Do not claim that a memory is current unless
  the RFP supports it.

- If information conflicts, identify the conflict
  as an assumption or open question.

- Make it clear which recommendations are
  influenced by historical memory.

Your output must contain:

1. Executive Summary
2. Client-Specific Context
3. Proposed Solution
4. Technical Architecture
5. Security & Compliance
6. Delivery Plan
7. Commercial Considerations
8. Assumptions / Open Questions
9. Memory-Driven Decisions
"""

                user_prompt = f"""
CLIENT:

{client_name.strip()}


CURRENT RFP:

{rfp_question.strip()}


RELEVANT HINDSIGHT MEMORIES:

{memory_context}


Generate the context-aware proposal.
"""

                proposal = groq_generate(
                    groq_key,
                    system_prompt,
                    user_prompt,
                )

                st.session_state.last_proposal = proposal

                st.session_state.last_client = (
                    client_name.strip()
                )

                st.session_state.last_rfp = (
                    rfp_question.strip()
                )

                st.session_state.learning_tier += 1

                log(
                    "Context-aware proposal generated "
                    "using retrieved Hindsight memory."
                )


            # ------------------------------------------------
            # STEP 3 — RETAIN EXPERIENCE
            # ------------------------------------------------

            try:

                retain_hindsight(

                    hindsight_key,

                    bank_id,

                    content=(
                        f"RFP interaction for "
                        f"{client_name.strip()} completed. "
                        f"The proposal was generated using "
                        f"{len(memories)} retrieved "
                        f"historical memories."
                    ),

                    context=(
                        "RFP proposal generation experience"
                    ),

                    document_id=(
                        "rfp-interaction-"
                        + datetime.datetime.now()
                        .strftime("%Y%m%d%H%M%S")
                    ),
                )

                log(
                    "RFP interaction experience "
                    "retained in Hindsight."
                )

            except Exception as exc:

                log(
                    "Post-generation memory retain failed: "
                    + type(exc).__name__
                )

        except Exception as exc:

            log(
                "Context-aware generation failed: "
                + type(exc).__name__
            )

            st.error(
                f"Context-aware generation failed: {exc}"
            )


# ============================================================
# OUTPUT
# ============================================================

if st.session_state.baseline_proposal:

    st.markdown("---")

    st.markdown(
        "## 📄 Baseline — Without Hindsight"
    )

    st.markdown(
        st.session_state.baseline_proposal
    )


if st.session_state.last_proposal:

    st.markdown("---")

    st.markdown(
        "## 🧠 Context-Aware Proposal — With Hindsight"
    )

    st.markdown(
        f"""
        <div class='success-box'>

        Retrieved
        {st.session_state.last_memory_count}
        relevant memories before proposal generation.

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        st.session_state.last_proposal
    )

    st.markdown(
        "### 🔎 Why This Proposal Changed"
    )

    if st.session_state.retrieved_memories:

        for memory in st.session_state.retrieved_memories:

            st.markdown(
                f"""
                <div class='decision-badge'>

                <b>Memory used:</b>
                {memory['text']}

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "No historical memory was retrieved "
            "for this proposal."
        )


    # ========================================================
    # OUTCOME LEARNING
    # ========================================================

    st.markdown(
        "### 📈 3. Learn: Record RFP Outcome"
    )

    outcome = st.selectbox(
        "What happened to this proposal?",

        [
            "Pending",
            "Won",
            "Lost",
            "Cancelled",
        ],

        key="rfp_outcome",
    )

    outcome_reason = st.text_area(

        "Outcome / lesson to remember",

        placeholder=(
            "e.g., Lost because pricing was above "
            "the client's threshold; technical "
            "architecture was accepted."
        ),

        key="rfp_outcome_reason",
    )

    if st.button(
        "🧠 Store Outcome as Hindsight Experience",
        use_container_width=True,
    ):

        if not hindsight_key:

            st.error(
                "Hindsight token is required."
            )

        elif (
            outcome == "Pending"
            and not outcome_reason.strip()
        ):

            st.error(
                "Add a short observation or choose "
                "a final outcome."
            )

        else:

            try:

                content = (

                    f"Client: "
                    f"{st.session_state.last_client}\n"

                    f"RFP: "
                    f"{st.session_state.last_rfp}\n"

                    f"Outcome: {outcome}\n"

                    f"Lesson: "
                    f"{outcome_reason.strip() or 'No additional lesson provided.'}"
                )

                retain_hindsight(

                    hindsight_key,

                    bank_id,

                    content=content,

                    context=(
                        "RFP outcome and learning"
                    ),

                    document_id=(
                        "rfp-outcome-"
                        + datetime.datetime.now()
                        .strftime("%Y%m%d%H%M%S")
                    ),
                )

                st.session_state.learning_tier += 2

                log(
                    f"RFP outcome RETAIN successful: "
                    f"{outcome} for "
                    f"{st.session_state.last_client}."
                )

                st.success(
                    "Outcome stored in Hindsight. "
                    "A future RFP can retrieve this experience."
                )

            except Exception as exc:

                log(
                    "Outcome retain failed: "
                    + type(exc).__name__
                )

                st.error(
                    f"Outcome storage failed: {exc}"
                )


# ============================================================
# DEMO SEEDING
# ============================================================

with st.expander(
    "🎬 Judge Demo: Seed a realistic organization memory set"
):

    st.write(
        "Use this once before your demo to create "
        "real Hindsight memories. These are stored "
        "in Hindsight, not only in Streamlit session state."
    )

    if st.button(
        "Seed Acme Corp Demo Memories",
        use_container_width=True,
    ):

        if not hindsight_key:

            st.error(
                "Enter the Hindsight Production Token first."
            )

        else:

            demo_memories = [

                (
                    "Acme Corp prefers Microsoft Azure "
                    "for enterprise cloud architecture.",
                    "Client Preference",
                ),

                (
                    "Acme Corp infrastructure proposals "
                    "must address ISO 27001 compliance.",
                    "Compliance Mandate",
                ),

                (
                    "A previous Acme Corp proposal was "
                    "rejected because pricing was considered "
                    "too aggressive.",
                    "RFP Outcome",
                ),

                (
                    "Successful enterprise proposals should "
                    "include a phased migration plan and "
                    "explicit security controls.",
                    "Successful Proposal Pattern",
                ),
            ]

            success_count = 0

            for idx, (
                content,
                category
            ) in enumerate(
                demo_memories,
                start=1
            ):

                try:

                    retain_hindsight(

                        hindsight_key,

                        bank_id,

                        content=(
                            "Client: Acme Corp\n"
                            f"Type: {category}\n"
                            f"Fact: {content}"
                        ),

                        context=(
                            "Acme Corp RFP demo — "
                            f"{category}"
                        ),

                        document_id=(
                            f"acme-demo-{idx}"
                        ),
                    )

                    success_count += 1

                except Exception as exc:

                    log(
                        f"Demo seed item {idx} failed: "
                        + type(exc).__name__
                    )

            if success_count == len(
                demo_memories
            ):

                st.session_state.learning_tier += (
                    success_count
                )

                log(
                    f"Seeded {success_count} real "
                    "Hindsight memories for Acme Corp."
                )

                st.success(
                    f"{success_count} demo memories "
                    "stored in Hindsight successfully."
                )

            else:

                st.warning(
                    f"Only {success_count}/"
                    f"{len(demo_memories)} demo memories "
                    "were stored."
                )