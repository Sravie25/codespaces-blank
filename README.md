# RFP Mind

AI-powered proposal generation with organizational memory.

## Overview

RFP Mind is an AI proposal assistant that uses Hindsight as a persistent memory layer. It remembers client preferences, compliance requirements, previous proposal outcomes, commercial lessons, and successful proposal patterns.

When a new proposal request arrives, RFP Mind recalls relevant organizational knowledge and uses it to generate a more context-aware proposal.

## Core Workflow

**Remember → Recall → Generate → Learn**

- **Remember:** Store important organizational knowledge in Hindsight.
- **Recall:** Retrieve relevant memories for a new proposal.
- **Generate:** Use the retrieved context with an LLM to create a personalized proposal.
- **Learn:** Store proposal outcomes and lessons back into Hindsight.

## Key Features

- Client-specific organizational memory
- Hindsight-powered memory retrieval
- Baseline proposal generation without memory
- Context-aware proposal generation with memory
- Decision-oriented memory insights
- "Why This Proposal Changed" explanation
- Proposal outcome learning
- User issue reporting

## Example

For Acme Corp, RFP Mind can remember:

- Azure as the preferred cloud platform
- ISO 27001 compliance requirements
- Previous pricing lessons
- Successful phased migration and security patterns

When a new RFP is received, these memories influence the generated proposal.

## Technology Stack

- Python
- Streamlit
- Hindsight
- Groq
- `gpt-oss-120b`

## Hindsight Integration

Hindsight is the central memory layer of RFP Mind.

The application uses Hindsight to:

1. Store organizational knowledge.
2. Recall relevant information for new RFPs.
3. Use recalled knowledge during proposal generation.
4. Store proposal outcomes and lessons for future interactions.

This allows the proposal agent to learn from previous experiences instead of treating every proposal as an isolated request.

## Project Structure

```text
RFP Mind
├── app.py
├── requirements.txt
└── README.md
