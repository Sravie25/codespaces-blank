# RFP Mind

AI proposal generation with organizational memory, built on Hindsight.

## Overview<a href="#overview" class="hash" aria-label="Direct link">#</a>

RFP Mind is an AI proposal generator with organizational memory. You enter a client and a set of proposal requirements, and it drafts a response in two ways: a standard draft from the requirements alone, and a memory-enhanced draft that also uses knowledge recalled from past proposals. Memory comes from [Hindsight](https://github.com/vectorize-io/hindsight). Text generation comes from Groq. The interface is a web app that runs in GitHub Codespaces.

The problem it targets is common in sales teams. RFP answers are rewritten from scratch, past wins are hard to find, and a confident answer can quietly contradict something the company already settled. RFP Mind keeps that history in a memory bank and brings the relevant parts back for each new proposal.

| Component              | Role                                                                                     |
|------------------------|------------------------------------------------------------------------------------------|
| **Web interface**      | Client and requirements form, system status, session counters                            |
| **Hindsight**          | Persistent memory: retain, recall and reflect over the memory bank `rfp-mind-cluster-v3` |
| **Groq**               | Fast LLM generation of the proposal draft                                                |
| **Codespaces secrets** | Holds the Groq and Hindsight credentials; nothing is hard-coded                          |

## Why memory instead of search<a href="#why-memory-instead-of-search" class="hash" aria-label="Direct link">#</a>

Storing past proposals as text and searching them is retrieval, not memory. [Vectorize's agent memory guide](https://vectorize.io/what-is-agent-memory) names three gaps in flat vector search, and each one shows up in proposals:

- **No sense of time.** "What did we promise last quarter?" needs temporal filtering, not similarity.
- **Everything looks the same.** A policy, a one-time exception and a contradicted claim sit in one index.
- **Observation and inference blur.** "We support region X" is a fact. "Buyers prefer phased delivery" is a belief. They need different handling.

Hindsight separates these by structuring knowledge at write time and by running several retrieval strategies at read time. That is why memory is the central component here and not an add-on.

## Architecture<a href="#architecture" class="hash" aria-label="Direct link">#</a>

Both generation modes start from the same request. The standard mode passes an empty context to Groq. The memory-enhanced mode recalls from Hindsight first, filters what comes back, and passes only the selected memories. Outcomes flow back into the memory bank as reviewed lessons.

## The interface<a href="#the-interface" class="hash" aria-label="Direct link">#</a>

![RFP Mind interface](screenshot.png)

| Element                         | What it does                                               |
|---------------------------------|------------------------------------------------------------|
| **Groq connected**              | Confirms the generation model can be reached               |
| **Hindsight credential loaded** | Confirms the memory credential was read from secrets       |
| **Memory bank**                 | Shows the active bank, `rfp-mind-cluster-v3`               |
| **Test Hindsight Connection**   | Checks the memory service on demand, before any generation |
| **Proposal Runs**               | Drafts generated in this session                           |
| **Learning Events**             | Times the system stored new knowledge                      |
| **Outcome Lessons**             | Lessons recorded from proposal results                     |
| **New Proposal**                | Starts a fresh client and requirements entry               |

## How it works: Remember, Recall, Generate, Learn<a href="#how-it-works-remember-recall-generate-learn" class="hash" aria-label="Direct link">#</a>

The banner in the app gives the loop. Each step maps to a Hindsight operation.

| Step         | Hindsight operation  | In RFP Mind                                                 |
|--------------|----------------------|-------------------------------------------------------------|
| **Remember** | `retain`             | Store approved answers, client context and proposal history |
| **Recall**   | `recall`             | Fetch relevant memories for the client and requirements     |
| **Generate** | none (Groq)          | Draft with the selected memories as context                 |
| **Learn**    | `retain` / `reflect` | Record outcomes and consolidate them into lessons           |

The call pattern, using the Hindsight Python client:

    from hindsight_client import Hindsight
    client = Hindsight(base_url="<HINDSIGHT_URL>", api_key="<HINDSIGHT_KEY>")

    # Remember
    client.retain(bank_id="rfp-mind-cluster-v3",
                  content="Approved answer: recovery objective is ...",
                  timestamp="2026-09-01T10:00:00Z")

    # Recall
    memories = client.recall(bank_id="rfp-mind-cluster-v3", query=requirements)

    # Learn
    client.reflect(bank_id="rfp-mind-cluster-v3",
                   query="What patterns explain our recent proposal outcomes?")

Exact argument names depend on your client version; check the [API quick start](https://hindsight.vectorize.io/developer/api/quickstart).

## Memory model<a href="#memory-model" class="hash" aria-label="Direct link">#</a>

Hindsight stores four kinds of memory. This is how each applies to proposals.

| Type             | Definition                              | Proposal example                                      |
|------------------|-----------------------------------------|-------------------------------------------------------|
| **World fact**   | Objective claim the system was told     | "We support deployment in region X"                   |
| **Experience**   | The agent's own action                  | "Sent Client Y a draft citing the recovery objective" |
| **Observation**  | Pattern consolidated from several facts | "Healthcare buyers ask for phased delivery"           |
| **Mental model** | Curated summary for common queries      | Approved security posture answer                      |

During reflect, Hindsight checks mental models first, then observations, then raw facts.

## Generation modes<a href="#generation-modes" class="hash" aria-label="Direct link">#</a>

- **Standard**: Groq drafts from requirements alone (baseline).
- **Memory-enhanced**: requirements plus context recalled from Hindsight.

Keep the requirements, prompt and model settings identical between modes, so any difference comes from memory.

## Setup<a href="#setup" class="hash" aria-label="Direct link">#</a>

| Requirement      | Notes                                                       |
|------------------|-------------------------------------------------------------|
| Python 3.10+     | Use the version your `requirements.txt` targets             |
| Groq API key     | Recommended models: `openai/gpt-oss-120b`, `qwen/qwen3-32b` |
| Hindsight access | Hindsight Cloud or the open-source server                   |

    git clone https://github.com/Sravie25/codespaces-blank.git
    cd codespaces-blank
    pip install -r requirements.txt
    # Set secrets (Codespaces: Settings → Secrets)
    #   <GROQ_API_KEY>, <HINDSIGHT_API_KEY>
    streamlit run <app_file>.py --server.port 8502

## Using the app<a href="#using-the-app" class="hash" aria-label="Direct link">#</a>

1.  Check the sidebar: Groq connected and Hindsight credential loaded.
2.  Select **Test Hindsight Connection**.
3.  Enter the client, for example Acme Corp.
4.  Enter the requirements, for example a cloud infrastructure proposal covering architecture, security, ISO 27001 compliance, migration and commercial terms.
5.  Generate the standard draft and the memory-enhanced draft, and compare them.
6.  Record the outcome so it can become a lesson. Watch the session counters update.

## Design decisions and safeguards<a href="#design-decisions-and-safeguards" class="hash" aria-label="Direct link">#</a>

- **Recall is a decision boundary.** Filter recalled memories for relevance, client authorization and a known source before generation.
- **Keep provenance.** Record which memory IDs fed each draft so reviewers can trace claims.
- **Separate failure states.** An empty recall, an unavailable memory service and a generation error are different, and the UI should say which.
- **Review lessons before reuse.** A win or loss has many causes, so lessons keep their source proposal and scope.
- **Never store secrets in code.** Credentials come from Codespaces secrets.

## Limitations and roadmap<a href="#limitations-and-roadmap" class="hash" aria-label="Direct link">#</a>

- No scored evaluation yet, so quality gains are not measured.
- Supersession of outdated policies needs an explicit review workflow.
- Next: mandatory scope on every write, memory IDs shown beside draft claims, and an evaluation set.

## Troubleshooting<a href="#troubleshooting" class="hash" aria-label="Direct link">#</a>

| Symptom                         | Likely cause and fix                                                        |
|---------------------------------|-----------------------------------------------------------------------------|
| Groq not connected              | Key missing or invalid. Check the secret name and restart the app.          |
| Hindsight credential not loaded | Secret not set in this Codespace. Add it and rebuild the environment.       |
| Recall returns nothing          | The bank may be empty or the query too narrow. Retain sample answers first. |
| Function-calling errors         | Some models fail tool calls. Retry, or switch models.                       |
| Status stuck on "Connecting"    | The Codespace port may have stopped. Reopen the forwarded port.             |

## References<a href="#references" class="hash" aria-label="Direct link">#</a>

- [What is agent memory? (Vectorize)](https://vectorize.io/what-is-agent-memory)
- [Hindsight documentation](https://hindsight.vectorize.io/)
- [Hindsight on GitHub](https://github.com/vectorize-io/hindsight)
