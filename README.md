# DiaWise – Evidence-Grounded Diabetes Education Assistant

> A world-class RAG prototype that gives patients, caregivers, and the newly diagnosed clear, source-backed answers about diabetes — powered by GPT-4, LangChain, and Pinecone.

---

## What makes this different

Most AI health tools are just ChatGPT wrappers. DiaWise is different:

| Feature | Generic chatbot | DiaWise |
|---|---|---|
| Source transparency | None | Every answer shows exact source docs/pages |
| Knowledge scope | Anything | Only diabetes-grade medical literature |
| Safety guardrails | Minimal | Emergency escalation, educational disclaimers |
| Mode-aware answers | No | Learning mode vs Newly Diagnosed mode |
| Conversation memory | Session only | Persisted in localStorage (no login needed) |
| Follow-up intelligence | No | AI-generated follow-up question suggestions |

---

## Architecture

```
User
  │
  ▼
Flask /ask endpoint
  │
  ├── Input validation (length, empty, mode)
  │
  ├── Emergency keyword fast-path → immediate safety response
  │
  ├── RAG Chain (primary)
  │     Pinecone vector search (k=4)
  │       └── GPT-4.1-mini with system_prompt + retrieved context
  │             └── Structured output: answer + SOURCES: + FOLLOWUPS:
  │
  └── LangGraph conversational memory (fallback if RAG errors)

Response: { answer, sources[], followups[], safety_note, mode, retrieved }

Frontend
  ├── Two-pane layout: chat (left) + evidence panel (right)
  ├── Source cards: green (retrieved) / amber (general knowledge)
  ├── Follow-up chips: clickable suggestions in evidence panel
  ├── Mode toggle: 📚 Learning | 🩺 Newly Diagnosed
  ├── LocalStorage persistence: chat history + mode preference
  └── Emergency styling, aria-live, keyboard accessible
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS (custom design system), vanilla JS |
| Backend | Python 3.10, Flask |
| LLM | OpenAI GPT-4.1-mini |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| RAG | LangChain + LangGraph |
| Vector Store | Pinecone (serverless) |
| Deployment | Render / Docker |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/diawise.git
cd diawise
pip install -r requirements.txt
```

### 2. Environment variables

Create `.env`:

```env
OPENAI_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=diabetesbot
SECRET_KEY=your_random_secret
```

### 3. Index your documents (first time only)

```bash
python src/store_index.py
```

### 4. Run

```bash
python app.py
```

---

## API contract

**POST /ask**

Request:
```json
{ "question": "What causes type 2 diabetes?", "mode": "learning" }
```

Response:
```json
{
  "answer": "Type 2 diabetes develops when...",
  "sources": ["Textbook of Diabetes, p.42", "Textbook of Diabetes, p.51"],
  "followups": ["How is type 2 diabetes diagnosed?", "Can it be reversed?"],
  "safety_note": "For educational purposes only...",
  "mode": "learning",
  "retrieved": true
}
```

---

## Product decisions

### Target user
Newly diagnosed adults and their caregivers in the first 90 days post-diagnosis — when information need is highest and confusion is greatest.

### North-star metric
`% of sessions where a cited answer is shown` (retrieval hit rate as a quality proxy)

### Intentional non-features
- No login / signup — localStorage is sufficient for a prototype
- No voice input — keeps scope focused
- No telemetry — trust through privacy

### Safety principles
1. Educational only — never diagnosis or prescription
2. Emergency escalation — immediate 999/911 routing for crisis keywords
3. Source transparency — every answer shows where it came from
4. No hallucinated citations — if no document found, says so explicitly

---

## License

MIT. See `LICENSE`.
