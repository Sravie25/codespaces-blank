import streamlit as st
from groq import Groq

st.set_page_config(page_title="RFP Proposal Agent", layout="wide")
st.title("💼 RFP Proposal Intelligence Agent")
st.caption("Powered by Persistent Memory Simulation & Groq")

with st.sidebar:
    st.header("🔑 API Credentials")
    groq_key = st.text_input("Paste your Groq API Key here:", type="password")

if "memory_bank" not in st.session_state:
    st.session_state.memory_bank = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Input System")
    with st.expander("🧠 Step 1: Feed Memory (Post-Mortem / Rule)"):
        context_input = st.text_area("Paste a past company rejection or rule here:", placeholder="e.g., Acme Corp hates AWS. They only use Microsoft Azure.")
        if st.button("Save to Hindsight Memory"):
            if context_input:
                st.session_state.memory_bank.append(context_input)
                st.success("Saved to memory successfully!")

    st.markdown("---")
    st.write("### 📝 Step 2: Run New RFP Question")
    client_name = st.text_input("Client Name", placeholder="e.g., Acme Corp")
    rfp_question = st.text_area("RFP Prompt Question", placeholder="e.g., Draft a cloud server proposal for our business.")
    generate_btn = st.button("Generate Proposal", type="primary")

with col2:
    st.subheader("🖥️ AI Results & Memory Log")
    if generate_btn:
        if not groq_key:
            st.error("Please paste your Groq API Key in the left sidebar first!")
        elif not client_name or not rfp_question:
            st.error("Please enter a Client Name and RFP Question.")
        else:
            with st.spinner("Searching memory and generating..."):
                recalled = [m for m in st.session_state.memory_bank if client_name.lower() in m.lower()]
                
                with st.chat_message("assistant", avatar="🧠"):
                    st.write("**[Memory Check Active]**")
                    if recalled:
                        st.info(f"Hindsight recalled {len(recalled)} constraint(s) for {client_name}:")
                        for r in recalled:
                            st.caption(f"• Recalled: '{r}'")
                    else:
                        st.warning("No historical rules found for this company.")

                mem_context = "\n".join(recalled) if recalled else "No history."
                sys_prompt = f"You are a professional proposal writer. Answer the question. IMPORTANT: Review these client notes. If notes mention technology limits or platform preferences, you MUST follow them completely!\nNotes:\n{mem_context}"
                user_prompt = f"Company: {client_name}\nQuestion: {rfp_question}"
                
                try:
                    client = Groq(api_key=groq_key)
                    completion = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                        temperature=0.2
                    )
                    st.markdown("### 📄 Final Tailored Proposal Output")
                    st.write(completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error: {e}")
