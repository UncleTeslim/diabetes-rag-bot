import json
import os
import re
import uuid
from typing import Dict

from dotenv import load_dotenv
from flask import (Flask, Response, render_template, request, session,
                   stream_with_context)
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from src.helpers import download_embeddings
from src.prompt import system_prompt, system_prompt_no_context

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise EnvironmentError("PINECONE_API_KEY and OPENAI_API_KEY must be set in environment.")

set_llm_cache(InMemoryCache())

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", os.urandom(32))

# LLM (streaming=True enables token-by-token generation)
llm = ChatOpenAI(
    temperature=0.4,
    model="gpt-4.1-mini",
    openai_api_key=OPENAI_API_KEY,
    max_tokens=1500,
    streaming=True,
)

# Embeddings + Vector Store
embeddings = download_embeddings()
index_name = "diabetesbot"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
)
retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4},
)

# RAG prompt template
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# Conversational memory fallback graph
memory_graph = StateGraph(state_schema=MessagesState)

def call_model(state: MessagesState) -> Dict:
    sys_msg = SystemMessage(content=system_prompt_no_context)
    response = llm.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}

memory_graph.add_node("model", call_model)
memory_graph.add_edge(START, "model")
memory_graph.add_edge("model", END)
memory = MemorySaver()
workflow = memory_graph.compile(checkpointer=memory)

# ── Helpers ────────────────────────────────────────────────────────────────

EMERGENCY_KEYWORDS = [
    "unconscious", "not breathing", "seizure", "convulsion",
    "severe hypoglycemia", "dka", "ketoacidosis", "very high blood sugar",
    "cant wake", "passing out", "loss of consciousness",
]
STOP_MARKERS = ("FOLLOWUPS:", "SOURCES:")


def _is_emergency(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in EMERGENCY_KEYWORDS)


def _build_augmented(question: str, mode: str, profile: dict) -> str:
    """Build the augmented question with mode and optional patient profile context."""
    lines = []
    name = str(profile.get("name") or "").strip()[:60]
    age  = str(profile.get("age")  or "").strip()[:4]
    gender = str(profile.get("gender") or "").strip()[:30]
    if name or age or gender:
        parts = []
        if name:   parts.append(f"Name: {name}")
        if age:    parts.append(f"Age: {age}")
        if gender: parts.append(f"Gender: {gender}")
        lines.append(f"[Patient context: {', '.join(parts)}]")
    lines.append(f"[Mode: {mode}]")
    lines.append(question)
    return "\n".join(lines)


def _parse_structured(raw: str) -> dict:
    answer = raw
    sources = []
    followups = []

    fu_match = re.search(r"FOLLOWUPS:\s*\n((?:\s*-[^\n]+\n?)+)", raw, re.IGNORECASE)
    src_match = re.search(r"SOURCES:\s*\n((?:\s*-[^\n]+\n?)+)", raw, re.IGNORECASE)

    if fu_match:
        followups = [
            l.strip().lstrip("- ").strip()
            for l in fu_match.group(1).splitlines()
            if l.strip().startswith("-")
        ]
        answer = raw[: fu_match.start()].strip()

    if src_match:
        sources = [
            l.strip().lstrip("- ").strip()
            for l in src_match.group(1).splitlines()
            if l.strip().startswith("-")
        ]
        answer = re.sub(r"SOURCES:\s*\n((?:\s*-[^\n]+\n?)+)", "", answer, flags=re.IGNORECASE).strip()

    return {"answer": answer, "sources": sources, "followups": followups}


def _extract_sources_from_docs(docs: list) -> list:
    seen, out = set(), []
    for doc in docs:
        meta  = doc.metadata or {}
        label = meta.get("source", meta.get("file_path", "Diabetes Reference Document"))
        page  = meta.get("page")
        entry = f"{label}, p.{int(page)+1}" if page is not None else label
        if entry not in seen:
            seen.add(entry)
            out.append(entry)
    return out or ["Diabetes Reference Document"]


def _safety_note(mode: str) -> str:
    if mode == "newly_diagnosed":
        return (
            "Remember: this information is for education only. "
            "Your diabetes care team is the best source of guidance for your personal situation."
        )
    return "For educational purposes only. Always consult a qualified healthcare professional for medical advice."


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "GET":
        return render_template("ask.html")

    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    mode     = data.get("mode", "learning")
    profile  = data.get("profile") or {}

    # Input validation — yield error as SSE so client handling is uniform
    if not question:
        return Response(_sse({"error": "Question cannot be empty."}),
                        mimetype="text/event-stream")
    if len(question) > 2000:
        return Response(_sse({"error": "Question too long. Keep it under 2000 characters."}),
                        mimetype="text/event-stream")
    if mode not in ("learning", "newly_diagnosed"):
        mode = "learning"

    augmented = _build_augmented(question, mode, profile)

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]

    def generate():
        # ── Emergency fast path ─────────────────────────────────────────
        if _is_emergency(question):
            msg = (
                "This sounds like a medical emergency. "
                "Please call emergency services (999/911) immediately.\n\n"
                "Do not wait — emergency symptoms like loss of consciousness, "
                "severe low blood sugar, or diabetic ketoacidosis require "
                "immediate in-person medical attention."
            )
            yield _sse({"token": msg})
            yield _sse({
                "done": True, "answer": msg, "sources": [], "followups": [],
                "safety_note": "Call 999/911 immediately.",
                "mode": mode, "retrieved": False, "emergency": True,
            })
            return

        # ── Primary: retrieve then stream ───────────────────────────────
        full_response = ""
        stop_streaming = False
        retrieved_docs = []

        try:
            retrieved_docs = retriever.invoke(augmented)
            context_str    = "\n\n".join(doc.page_content for doc in retrieved_docs)
            messages       = rag_prompt.format_messages(
                context=context_str, input=augmented
            )

            for chunk in llm.stream(messages):
                token = (chunk.content or "") if hasattr(chunk, "content") else ""
                if not token:
                    continue
                full_response += token

                if not stop_streaming:
                    upper = full_response.upper()
                    if "FOLLOWUPS:" in upper or "SOURCES:" in upper:
                        stop_streaming = True
                    else:
                        yield _sse({"token": token})

            parsed = _parse_structured(full_response)
            if retrieved_docs and not parsed["sources"]:
                parsed["sources"] = _extract_sources_from_docs(retrieved_docs)

            yield _sse({
                "done":        True,
                "answer":      parsed["answer"],
                "sources":     parsed["sources"],
                "followups":   parsed["followups"],
                "safety_note": _safety_note(mode),
                "mode":        mode,
                "retrieved":   bool(retrieved_docs),
            })

        except Exception as e:
            app.logger.error("Streaming error: %s", str(e))

            # ── Fallback: LangGraph memory graph ───────────────────────
            try:
                thread   = {"configurable": {"thread_id": session_id}}
                fallback = workflow.invoke(
                    {"messages": [HumanMessage(content=augmented)]}, thread
                )
                raw    = fallback["messages"][-1].content
                parsed = _parse_structured(raw)
                fb_ans = parsed["answer"] or raw

                yield _sse({"token": fb_ans})
                yield _sse({
                    "done":        True,
                    "answer":      fb_ans,
                    "sources":     parsed["sources"] or ["General knowledge (fallback mode)"],
                    "followups":   parsed["followups"],
                    "safety_note": _safety_note(mode),
                    "mode":        mode,
                    "retrieved":   False,
                })

            except Exception as e2:
                app.logger.error("Fallback error: %s", str(e2))
                msg = "I am sorry, I could not generate a response right now. Please try again."
                yield _sse({"token": msg})
                yield _sse({
                    "done":        True,
                    "answer":      msg,
                    "sources":     [],
                    "followups":   [],
                    "safety_note": _safety_note(mode),
                    "mode":        mode,
                    "retrieved":   False,
                })

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=False)
