import os
import asyncio
import re
import datetime
from difflib import SequenceMatcher

import streamlit as st
from groq import Groq
from hindsight_client import Hindsight


# ============================================================
# RFP MIND — Hindsight-powered Proposal Agent
# ============================================================

HINDSIGHT_API_URL = "https://api.hindsight.vectorize.io"
DEFAULT_BANK_ID = "rfp-mind-cluster-v3"
GROQ_MODEL = "openai/gpt-oss-120b"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RFP Mind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROFESSIONAL LIGHTWEIGHT STYLING
# ============================================================

st.markdown(
    """
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.45rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "hindsight_verified": False,
    "baseline_proposal": "",
    "context_proposal": "",
    "retrieved_memories": [],
    "memory_insights": [],
    "memory_count": 0,
    "current_client": "",
    "current_rfp": "",
    "proposal_runs": 0,
    "learning_events": 0,
    "outcome_lessons": 0,
    "telemetry": [],
    "outcome_saved": False,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# SESSION HELPERS
# ============================================================

def add_log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    st.session_state.telemetry.insert(
        0,
        f"[{timestamp}] {message}"
    )

    st.session_state.telemetry = (
        st.session_state.telemetry[:30]
    )


def reset_workspace():
    """
    Clears the current proposal workspace.

    IMPORTANT:
    This does NOT delete Hindsight memories.
    """

    keys_to_clear = [
        "baseline_proposal",
        "context_proposal",
        "retrieved_memories",
        "memory_insights",
        "memory_count",
        "current_client",
        "current_rfp",
        "outcome_saved",
        "proposal_outcome",
        "proposal_lesson",
        "client_name_input",
        "rfp_input",
    ]

    for key in keys_to_clear:

        if key in st.session_state:
            del st.session_state[key]

    st.session_state.telemetry = []


# ============================================================
# ENVIRONMENT / CODESPACES SECRETS
# ============================================================

groq_key = os.getenv(
    "GROQ_API_KEY",
    ""
).strip()

hindsight_key = os.getenv(
    "HINDSIGHT_API_KEY",
    ""
).strip()

bank_id = os.getenv(
    "HINDSIGHT_BANK_ID",
    DEFAULT_BANK_ID,
).strip() or DEFAULT_BANK_ID


# ============================================================
# HINDSIGHT
# ============================================================

def get_hindsight_client(api_key):

    if not api_key:
        raise ValueError(
            "Hindsight API key is not configured."
        )

    return Hindsight(
        base_url=HINDSIGHT_API_URL,
        api_key=api_key,
        timeout=30.0,
    )


def ensure_memory_bank(
    client,
    memory_bank_id,
):

    try:

        client.create_bank(
            bank_id=memory_bank_id,
            name="RFP Mind Enterprise Memory",
        )

        add_log(
            "Hindsight memory bank initialized."
        )

    except Exception as exc:

        message = str(exc).lower()

        # Ignore only existing-bank errors.
        if not any(
            word in message
            for word in [
                "exist",
                "already",
                "409",
            ]
        ):
            raise


def store_memory(
    api_key,
    memory_bank_id,
    content,
    context,
    document_id,
):

    client = get_hindsight_client(
        api_key
    )

    ensure_memory_bank(
        client,
        memory_bank_id
    )

    client.retain(
        bank_id=memory_bank_id,
        content=content,
        context=context,
        document_id=document_id,
        retain_async=False,
    )


# ============================================================
# MEMORY DEDUPLICATION
# ============================================================

def normalize_text(text):

    return " ".join(
        re.sub(
            r"[^a-z0-9\s]",
            " ",
            str(text).lower(),
        ).split()
    )


def similar_text(
    first,
    second,
):

    return SequenceMatcher(
        None,
        normalize_text(first),
        normalize_text(second),
    ).ratio()


def clean_memory_results(
    result,
    maximum=8,
):

    memories = []

    results = getattr(
        result,
        "results",
        []
    ) or []

    for item in results:

        text_value = str(
            getattr(
                item,
                "text",
                ""
            ) or ""
        ).strip()

        if not text_value:
            continue

        duplicate = False

        for existing in memories:

            if (
                normalize_text(
                    text_value
                )
                ==
                normalize_text(
                    existing["text"]
                )
            ):

                duplicate = True
                break

            if (
                similar_text(
                    text_value,
                    existing["text"]
                )
                >= 0.78
            ):

                duplicate = True
                break

        if duplicate:
            continue

        memories.append(
            {
                "text": text_value,
                "type": str(
                    getattr(
                        item,
                        "type",
                        "memory"
                    )
                    or "memory"
                ),
                "context": str(
                    getattr(
                        item,
                        "context",
                        ""
                    )
                    or ""
                ),
            }
        )

        if len(memories) >= maximum:
            break

    return memories


def recall_memory(
    api_key,
    memory_bank_id,
    query,
):

    client = get_hindsight_client(
        api_key
    )

    ensure_memory_bank(
        client,
        memory_bank_id
    )

    async def async_recall():
        return await client.arecall(
            bank_id=memory_bank_id,
            query=query,
            max_tokens=3500,
            budget="mid",
        )

    result = asyncio.run(
        async_recall()
    )

    return clean_memory_results(
        result,
        maximum=8,
    )

# ============================================================
# GROQ
# ============================================================

def generate_response(
    api_key,
    system_prompt,
    user_prompt,
):

    if not api_key:
        raise ValueError(
            "Groq API key is not configured."
        )

    client = Groq(
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
        max_completion_tokens=3000,
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


# ============================================================
# MEMORY PRESENTATION
# ============================================================

def classify_memory(
    text,
    memory_type="",
):

    combined = (
        f"{memory_type} {text}"
    ).lower()

    if "azure" in combined:

        return (
            "Cloud Preference",
            "Use an Azure-first architecture",
        )

    if (
        "iso 27001" in combined
        or "compliance" in combined
    ):

        return (
            "Compliance",
            "Address ISO 27001 requirements",
        )

    if (
        "pricing" in combined
        or "price" in combined
        or "commercial" in combined
    ):

        return (
            "Commercial Lesson",
            "Use transparent, non-aggressive pricing",
        )

    if (
        "phased migration" in combined
        or "migration" in combined
    ):

        return (
            "Delivery Pattern",
            "Use a phased migration approach",
        )

    if (
        "security" in combined
        or "control" in combined
    ):

        return (
            "Security Pattern",
            "Make security controls explicit",
        )

    if (
        "milestone" in combined
        or "kpi" in combined
    ):

        return (
            "Measurement",
            "Use measurable delivery milestones",
        )

    if (
        "outcome" in combined
        or "rejected" in combined
        or "won" in combined
        or "lost" in combined
    ):

        return (
            "Past Outcome",
            "Apply the historical lesson",
        )

    return (
        "Organizational Knowledge",
        "Use as historical context",
    )


def build_memory_insights(
    memories,
):

    insights = []
    seen = set()

    for memory in memories:

        label, decision = classify_memory(
            memory["text"],
            memory["type"],
        )

        key = normalize_text(
            label + decision
        )

        if key in seen:
            continue

        seen.add(key)

        insights.append(
            {
                "label": label,
                "decision": decision,
                "source": memory["text"],
            }
        )

        if len(insights) >= 5:
            break

    return insights


def format_memory_context(
    memories,
):

    if not memories:

        return (
            "No relevant Hindsight memories "
            "were retrieved."
        )

    return "\n".join(
        f"- [{memory['type']}] "
        f"{memory['text']}"
        for memory in memories
    )


def get_executive_summary(
    proposal,
):

    match = re.search(
        r"(?is)"
        r"(?:##\s*)?"
        r"1\.\s*Executive Summary"
        r"\s*(.*?)"
        r"(?=\n##|\Z)",
        proposal.strip(),
    )

    if match:

        summary = (
            match
            .group(1)
            .strip()
        )

    else:

        summary = proposal.strip()[:1800]

    if len(summary) > 1800:

        summary = (
            summary[:1800]
            .rsplit(" ", 1)[0]
            + "..."
        )

    return summary


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("System Status")

    st.caption(
        "Credentials are loaded securely "
        "from Codespaces secrets."
    )

    if groq_key:

        st.success(
            "Groq connected"
        )

    else:

        st.error(
            "Groq secret missing"
        )

    if hindsight_key:

        st.success(
            "Hindsight credential loaded"
        )

    else:

        st.error(
            "Hindsight secret missing"
        )

    st.caption(
        f"Memory bank: {bank_id}"
    )

    if st.button(
        "Test Hindsight Connection",
        use_container_width=True,
    ):

        try:

            client = get_hindsight_client(
                hindsight_key
            )

            ensure_memory_bank(
                client,
                bank_id
            )

            client.recall(
                bank_id=bank_id,
                query="RFP Mind connection test",
                max_tokens=300,
                budget="low",
            )

            st.session_state.hindsight_verified = (
                True
            )

            add_log(
                "Hindsight connection verified."
            )

            st.success(
                "Hindsight connected successfully."
            )

        except Exception as exc:

            st.session_state.hindsight_verified = (
                False
            )

            add_log(
                "Hindsight connection test failed."
            )

            st.error(
                "Hindsight connection failed."
            )

            st.caption(
                str(exc)[:250]
            )

    st.divider()

    st.subheader(
        "Current Session"
    )

    st.metric(
        "Proposal Runs",
        st.session_state.proposal_runs,
    )

    st.metric(
        "Learning Events",
        st.session_state.learning_events,
    )

    st.metric(
        "Outcome Lessons",
        st.session_state.outcome_lessons,
    )

    st.divider()

    with st.expander(
        "Demo Setup"
    ):

        st.caption(
            "Optional: seed the Acme Corp "
            "memory set for a judge demo."
        )

        if st.button(
            "Initialize Acme Demo Memory",
            use_container_width=True,
        ):

            demo_memories = [

                (
                    "Client Preference",
                    "Acme Corp prefers Microsoft Azure "
                    "for enterprise cloud architecture.",
                ),

                (
                    "Compliance Requirement",
                    "Acme Corp infrastructure proposals "
                    "must address ISO 27001 compliance.",
                ),

                (
                    "RFP Outcome",
                    "A previous Acme Corp proposal was "
                    "rejected because pricing was considered "
                    "too aggressive.",
                ),

                (
                    "Successful Proposal Pattern",
                    "Successful enterprise proposals should "
                    "include a phased migration plan and "
                    "explicit security controls.",
                ),

            ]

            success_count = 0
            errors = []

            for index, (
                category,
                fact,
            ) in enumerate(
                demo_memories,
                start=1,
            ):

                try:

                    store_memory(
                        hindsight_key,
                        bank_id,
                        content=(
                            "Client: Acme Corp\n"
                            f"Information type: "
                            f"{category}\n"
                            f"Fact: {fact}"
                        ),
                        context=(
                            f"RFP Mind demo — "
                            f"{category}"
                        ),
                        document_id=(
                            f"acme-demo-{index}"
                        ),
                    )

                    success_count += 1

                except Exception as exc:

                    errors.append(
                        str(exc)[:150]
                    )

            if success_count:

                st.success(
                    f"{success_count}/4 "
                    "demo memories saved."
                )

            if errors:

                st.warning(
                    "Some demo memories "
                    "could not be saved."
                )

    with st.expander(
        "Technical Details"
    ):

        st.caption(
            "Hindsight Cloud"
        )

        st.caption(
            "Groq GPT-OSS 120B"
        )

        st.caption(
            "Recall → Generate → Learn"
        )


# ============================================================
# MAIN HEADER
# NATIVE STREAMLIT ONLY
# ============================================================

st.title(
    "🧠 REQUEST FOR PROPOSAL (RFP) MIND"
)

st.caption(
    "AI proposal generation with organizational memory. "
    "RFP Mind remembers relevant past knowledge, uses it "
    "for the current proposal, and learns from outcomes."
)

status1, status2, status3 = st.columns(3)

with status1:

    st.success(
        "Hindsight Memory"
    )

with status2:

    st.success(
        "Groq Generation"
    )

with status3:

    st.info(
        "Remember → Recall → Generate → Learn"
    )


# ============================================================
# NEW PROPOSAL
# ============================================================

new_col, _ = st.columns(
    [1, 5]
)

with new_col:

    if st.button(
        "＋ New Proposal",
        use_container_width=True,
    ):

        reset_workspace()

        st.rerun()


# ============================================================
# STEP 1 — CREATE PROPOSAL
# ============================================================

st.divider()

st.subheader(
    "Create a Proposal"
)

st.caption(

    "Enter the client and their proposal requirements. "

    "Compare a standard response with one enhanced "

    "by organizational memory."

)


client_name = st.text_input(
    "Client / Organization",
    placeholder="Example: Acme Corp",
    key="client_name_input",
)


rfp_question = st.text_area(
    "Proposal Requirements",
    placeholder=(
        "Example: Design a cloud infrastructure "
        "proposal for Acme Corp covering architecture, "
        "security, ISO 27001 compliance, migration "
        "strategy, and commercial considerations."
    ),
    height=140,
    key="rfp_input",
)

st.caption(
    "Describe what the client is asking for, including "
    "technical requirements, security, compliance, "
    "delivery, and commercial needs."
)


baseline_col, memory_col = st.columns(
    2
)


with baseline_col:

    baseline_button = st.button(
        "📄 Generate Without Memory",
        use_container_width=True,
    )


with memory_col:

    memory_button = st.button(
        "🧠 Generate With Hindsight",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# BASELINE GENERATION
# ============================================================

if baseline_button:

    if not groq_key:

        st.error(
            "Groq is not configured."
        )

    elif (
        not client_name.strip()
        or not rfp_question.strip()
    ):

        st.error(
            "Enter both the client and "
            "the Request for Proposal."
        )

    else:

        try:

            with st.spinner(
                "Generating baseline proposal..."
            ):

                baseline_system = """
You are an enterprise proposal-writing assistant.

Generate a professional proposal using ONLY
the current Request for Proposal.

Do not use historical client preferences,
previous outcomes, or external assumptions.

Do not invent confirmed client facts.

If you introduce numbers, prices, KPIs, SLAs,
timelines, certifications, or commitments
not supplied by the RFP, clearly label them as:

Proposed
Illustrative
Assumption
or
To Be Confirmed.
"""

                baseline_prompt = f"""
CLIENT:

{client_name.strip()}


CURRENT REQUEST FOR PROPOSAL:

{rfp_question.strip()}


Generate:

1. Executive Summary
2. Proposed Solution
3. Technical Architecture
4. Security & Compliance
5. Delivery Plan
6. Assumptions / Open Questions
7. Commercial Considerations
"""

                st.session_state.baseline_proposal = (
                    generate_response(
                        groq_key,
                        baseline_system,
                        baseline_prompt,
                    )
                )

                add_log(
                    "Baseline proposal generated "
                    "without Hindsight."
                )

        except Exception as exc:

            add_log(
                "Baseline generation failed."
            )

            st.error(
                "The baseline proposal could "
                "not be generated."
            )

            st.caption(
                str(exc)[:300]
            )


# ============================================================
# HINDSIGHT-AWARE GENERATION
# ============================================================

if memory_button:

    if not groq_key:

        st.error(
            "Groq is not configured."
        )

    elif not hindsight_key:

        st.error(
            "Hindsight is not configured."
        )

    elif (
        not client_name.strip()
        or not rfp_question.strip()
    ):

        st.error(
            "Enter both the client and "
            "the Request for Proposal."
        )

    else:

        try:

            with st.spinner(
                "Recalling relevant "
                "organizational memory..."
            ):

                recall_query = f"""
Upcoming Request for Proposal

Client:
{client_name.strip()}

Current RFP:
{rfp_question.strip()}

Retrieve the most useful historical
organizational knowledge for this proposal.

Prioritize:

- client preferences
- compliance requirements
- previous proposal outcomes
- commercial lessons
- successful proposal patterns
- relevant company capabilities

Prefer useful decision-making knowledge
over repetitive raw memories.
"""

                memories = recall_memory(
                    hindsight_key,
                    bank_id,
                    recall_query,
                )

                st.session_state.retrieved_memories = (
                    memories
                )

                st.session_state.memory_count = (
                    len(memories)
                )

                st.session_state.memory_insights = (
                    build_memory_insights(
                        memories
                    )
                )

                add_log(
                    f"Hindsight recalled "
                    f"{len(memories)} useful memories."
                )


            historical_context = (
                format_memory_context(
                    memories
                )
            )


            with st.spinner(
                "Generating memory-informed proposal..."
            ):

                memory_system = """
You are RFP Mind, an enterprise proposal agent.

Generate a professional proposal using:

1. The current Request for Proposal.
2. Relevant historical organizational
   knowledge retrieved from Hindsight.

MEMORY RULES:

- Treat memories as historical context,
  not unquestionable truth.

- Never invent client facts.

- Do not turn a preference into a
  mandatory requirement.

- If a client prefers a platform, use
  wording such as "Azure-first" unless
  the current RFP makes it mandatory.

- If historical information conflicts
  with the current RFP, identify the
  conflict as an assumption or open question.

- Never present invented numbers, prices,
  percentages, SLAs, KPIs, timelines,
  certifications, or commitments as
  confirmed facts.

- Values not supplied by the RFP or memory
  must be labeled:

  Proposed
  Illustrative
  Assumption
  or
  To Be Confirmed.

OUTPUT:

1. Executive Summary
2. Client-Specific Solution
3. Technical Architecture
4. Security & Compliance
5. Migration / Delivery Plan
6. Commercial Strategy
7. Risks and Mitigations
8. Assumptions / Open Questions
9. Memory-Driven Decisions

For Memory-Driven Decisions, explicitly
connect historical knowledge to the
proposal decision it influenced.
"""

                memory_prompt = f"""
CLIENT:

{client_name.strip()}


CURRENT REQUEST FOR PROPOSAL:

{rfp_question.strip()}


RELEVANT HINDSIGHT MEMORY:

{historical_context}


Generate the proposal.
"""

                st.session_state.context_proposal = (
                    generate_response(
                        groq_key,
                        memory_system,
                        memory_prompt,
                    )
                )

                st.session_state.current_client = (
                    client_name.strip()
                )

                st.session_state.current_rfp = (
                    rfp_question.strip()
                )

                st.session_state.proposal_runs += 1

                st.session_state.learning_events += 1

                st.session_state.outcome_saved = (
                    False
                )

                add_log(
                    "Memory-informed proposal generated."
                )

        except Exception as exc:

            add_log(
                "Memory-informed generation failed."
            )

            st.error(
                "The memory-informed proposal "
                "could not be generated."
            )

            st.caption(
                str(exc)[:300]
            )


# ============================================================
# STEP 2 — MEMORY INSIGHTS
# ============================================================

if st.session_state.context_proposal:

    st.divider()

    st.subheader(
        "#What RFP Mind Remembered"
    )

    st.caption(
        "Hindsight results are consolidated "
        "into decision-oriented insights rather "
        "than shown as a long raw memory list."
    )

    insights = (
        st.session_state.memory_insights
    )

    if insights:

        insight_columns = st.columns(
            min(
                3,
                len(insights)
            )
        )

        for index, insight in enumerate(
            insights
        ):

            with insight_columns[
                index
                % len(insight_columns)
            ]:

                with st.container(
                    border=True
                ):

                    st.caption(
                        insight["label"]
                    )

                    st.write(
                        insight["decision"]
                    )

    else:

        st.info(
            "No relevant historical memory "
            "was found for this proposal."
        )


# ============================================================
# BEFORE / AFTER COMPARISON
# ============================================================

if (
    st.session_state.baseline_proposal
    and
    st.session_state.context_proposal
):

    st.divider()

    st.subheader(
        "3. How Hindsight Changed the Proposal"
    )

    st.caption(
        "The baseline uses only the current RFP. "
        "The context-aware version also uses "
        "historical organizational knowledge."
    )

    comparison = [

        (
            "Client preferences",
            "Not available",
            "Historical preferences considered",
        ),

        (
            "Past outcomes",
            "Not available",
            "Historical lessons considered",
        ),

        (
            "Proposal strategy",
            "Current RFP only",
            "RFP + organizational patterns",
        ),

        (
            "Explainability",
            "Generic response",
            "Memory-driven decisions shown",
        ),

    ]

    comparison_columns = st.columns(
        4
    )

    for index, (
        title,
        baseline,
        memory_version,
    ) in enumerate(
        comparison
    ):

        with comparison_columns[index]:

            with st.container(
                border=True
            ):

                st.caption(
                    title
                )

                st.write(
                    "**Without Hindsight**"
                )

                st.write(
                    baseline
                )

                st.write(
                    "**With Hindsight**"
                )

                st.write(
                    memory_version
                )


# ============================================================
# STEP 4 — CONTEXT-AWARE PROPOSAL
# ============================================================

if st.session_state.context_proposal:

    st.divider()

    st.subheader(
        "#Context-Aware Proposal"
    )

    st.success(
        f"Generated using "
        f"{st.session_state.memory_count} "
        f"relevant Hindsight memories."
    )

    with st.container(
        border=True
    ):

        st.caption(
            "Executive Summary"
        )

        st.write(
            get_executive_summary(
                st.session_state.context_proposal
            )
        )

    with st.expander(
        "View Full Proposal"
    ):

        st.markdown(
            st.session_state.context_proposal
        )


# ============================================================
# EXPLAINABILITY
# ============================================================

if st.session_state.context_proposal:

    st.subheader(
        "Why This Proposal Changed"
    )

    if st.session_state.memory_insights:

        for insight in (
            st.session_state.memory_insights
        ):

            with st.container(
                border=True
            ):

                st.write(
                    f"**{insight['label']}**"
                )

                st.write(
                    "Historical knowledge → "
                    f"{insight['decision']}"
                )

    else:

        st.info(
            "No memory-driven decision "
            "was identified."
        )


# ============================================================
# STEP 5 — OUTCOME LEARNING
# ============================================================

if st.session_state.context_proposal:

    st.divider()

    st.subheader(
        "Learn From the Outcome"
    )

    st.caption(
        "Record what happened so future "
        "proposals can retrieve this lesson."
    )

    outcome = st.selectbox(
        "Proposal Outcome",
        [
            "Pending",
            "Won",
            "Lost",
            "Cancelled",
        ],
        key="proposal_outcome",
    )

    outcome_lesson = st.text_area(
        "Lesson to Remember",
        placeholder=(
            "Example: Pricing was too aggressive. "
            "Future proposals should use transparent, "
            "non-aggressive pricing."
        ),
        height=100,
        key="proposal_lesson",
    )

    if st.button(
        "🧠 Save Outcome & Teach Hindsight",
        type="primary",
        use_container_width=True,
    ):

        if not hindsight_key:

            st.error(
                "Hindsight is not configured."
            )

        elif (
            outcome == "Pending"
            and not outcome_lesson.strip()
        ):

            st.error(
                "Choose a final outcome or "
                "provide a lesson to remember."
            )

        else:

            try:

                outcome_content = (
                    f"Client: "
                    f"{st.session_state.current_client}\n"
                    f"RFP: "
                    f"{st.session_state.current_rfp}\n"
                    f"Outcome: "
                    f"{outcome}\n"
                    f"Lesson: "
                    f"{outcome_lesson.strip() or 'No additional lesson provided.'}"
                )

                store_memory(
                    hindsight_key,
                    bank_id,
                    content=outcome_content,
                    context=(
                        "RFP outcome and learning"
                    ),
                    document_id=(
                        "rfp-outcome-"
                        +
                        datetime.datetime.now().strftime(
                            "%Y%m%d%H%M%S%f"
                        )
                    ),
                )

                st.session_state.outcome_lessons += (
                    1
                )

                st.session_state.learning_events += (
                    1
                )

                st.session_state.outcome_saved = (
                    True
                )

                add_log(
                    "Proposal outcome saved to Hindsight."
                )

                st.success(
                    "Outcome saved. Future proposals "
                    "can retrieve this lesson."
                )

            except Exception as exc:

                add_log(
                    "Outcome learning failed."
                )

                st.error(
                    "The outcome could not be saved."
                )

                st.caption(
                    str(exc)[:300]
                )


# ============================================================
# TECHNICAL ACTIVITY
# ============================================================

# ============================================================
# FLOATING CUSTOMER SUPPORT
# ============================================================

st.markdown(
    """
    <style>
    div[data-testid="stPopover"] {
        position: fixed !important;
        right: 20px !important;
        bottom: 20px !important;
        width: 70px !important;
        z-index: 99999 !important;
    }

    div[data-testid="stPopover"] > div {
        width: 70px !important;
    }

    div[data-testid="stPopover"] button {
        border-radius: 50px !important;
        padding: 8px 14px !important;
        white-space: nowrap !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.popover("💬"):

    st.markdown("### ⚠️ Report an Issue")

    st.caption(
        "Report a complaint, problem, service issue, "
        "or anything that needs attention."
    )

    customer_issue = st.text_area(
        "Describe the issue",
        placeholder=(
            "Example: We faced delays during the previous "
            "migration and need better communication and support."
        ),
        height=100,
        key="customer_issue",
    )

    if st.button(
        "📩 Submit Issue",
        use_container_width=True
    ):

        if customer_issue.strip():

            try:
                hindsight_client = get_hindsight(
                    os.getenv("HINDSIGHT_API_KEY")
                )

                ensure_bank(
                    hindsight_client,
                    DEFAULT_BANK_ID
                )

                issue_memories = recall_hindsight(
                    os.getenv("HINDSIGHT_API_KEY"),
                    DEFAULT_BANK_ID,
                    customer_issue.strip(),
                )

                memory_context = build_memory_context(
                    issue_memories
                )

                groq_client = get_groq(
                    os.getenv("GROQ_API_KEY")
                )

                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the RFP Mind customer support "
                                "assistant. Respond professionally and "
                                "helpfully to a reported customer issue. "
                                "Use recalled organizational memory when "
                                "relevant. Do not invent facts, promises, "
                                "timelines, refunds, or actions."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Customer issue:\n"
                                f"{customer_issue.strip()}\n\n"
                                f"Relevant organizational memory:\n"
                                f"{memory_context}"
                            ),
                        },
                    ],
                )

                ai_response = (
                    response.choices[0].message.content.strip()
                )

                hindsight_client.retain(
                    bank_id=DEFAULT_BANK_ID,
                    content=(
                        f"Customer issue: "
                        f"{customer_issue.strip()}\n"
                        f"AI response: {ai_response}"
                    ),
                    context="Customer issue and support resolution",
                    document_id=(
                        "customer-issue-"
                        f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    ),
                )

                st.success(
                    "Issue received and saved to organizational memory."
                )

                st.markdown("### 🤖 RFP Mind Response")
                st.write(ai_response)

            except Exception as e:

                st.error(
                    f"Unable to process the issue: {e}"
                )

        else:

            st.warning(
                "Please describe the issue before submitting."
            )
# ============================================================
# FOOTER
# ============================================================

st.caption(
    "RFP Mind · Hindsight-powered "
    "organizational memory"
)