#!/usr/bin/env python3
"""
build_index.py — Idempotent Pinecone index builder for DiaWise.

Behaviour:
  - If the 'diabetesbot' index already exists and has vectors → skip (fast path).
  - If the index is missing or empty → build it from data/ PDFs.
  - --force flag (or FORCE_INDEX_REBUILD=true env var) → always delete and rebuild.

Usage:
  python build_index.py              # smart skip if already populated
  python build_index.py --force      # force full rebuild (e.g. after adding PDFs)
"""

import argparse
import concurrent.futures
import os
import sys
import uuid

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

from src.helpers import download_embeddings, load_file, text_splitter

load_dotenv()

INDEX_NAME = "diabetesbot"
INDEX_DIMENSION = 1536
INDEX_METRIC = "cosine"
DATA_DIR = "data/"


def build(force: bool = False) -> None:
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not pinecone_api_key or not openai_api_key:
        print(
            "[ERROR] PINECONE_API_KEY and OPENAI_API_KEY must be set in the environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Honour the Railway dashboard toggle without requiring a code push
    if not force:
        force = os.getenv("FORCE_INDEX_REBUILD", "").lower() in ("true", "1", "yes")

    pc = Pinecone(api_key=pinecone_api_key)
    existing = pc.list_indexes().names()

    # ── Fast path: index exists and is populated ──────────────────────────
    if INDEX_NAME in existing and not force:
        stats = pc.Index(INDEX_NAME).describe_index_stats()
        vector_count = stats.total_vector_count
        if vector_count > 0:
            print(
                f"[INFO] Index '{INDEX_NAME}' already has {vector_count:,} vectors. "
                "Skipping rebuild — app will start immediately.",
            )
            print("[INFO] To force a rebuild: set FORCE_INDEX_REBUILD=true or run with --force.")
            return
        else:
            print(f"[INFO] Index '{INDEX_NAME}' exists but is empty. Proceeding with build.")

    # ── Tear down existing index when force-rebuilding ────────────────────
    if INDEX_NAME in existing and force:
        print(f"[INFO] --force active: deleting existing index '{INDEX_NAME}'...")
        pc.delete_index(INDEX_NAME)
        # Refresh the list after deletion
        existing = pc.list_indexes().names()
        print(f"[INFO] Deleted '{INDEX_NAME}'.")

    # ── Create index if it doesn't exist ─────────────────────────────────
    if INDEX_NAME not in existing:
        print(
            f"[INFO] Creating index '{INDEX_NAME}' "
            f"({INDEX_DIMENSION}-dim, metric={INDEX_METRIC}, AWS us-east-1)..."
        )
        pc.create_index(
            name=INDEX_NAME,
            dimension=INDEX_DIMENSION,
            metric=INDEX_METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"[INFO] Index '{INDEX_NAME}' created.")

    # ── Load PDFs, chunk, embed, upsert ──────────────────────────────────
    print(f"[INFO] Loading PDFs from '{DATA_DIR}'...")
    documents = load_file(data=DATA_DIR)
    print(f"[INFO] Loaded {len(documents)} document pages.")

    chunks = text_splitter(data=documents)
    print(f"[INFO] Split into {len(chunks)} chunks.")

    embeddings = download_embeddings()
    texts    = [c.page_content for c in chunks]
    metadatas = [c.metadata   for c in chunks]

    # ── Step 1: embed ALL texts in one OpenAI call (their API batches internally) ──
    total = len(texts)
    print(f"[INFO] Embedding {total} chunks via OpenAI (single batched call)...")
    vectors = embeddings.embed_documents(texts)
    print(f"[INFO] Embeddings done. Upserting to Pinecone in parallel batches...")

    # ── Step 2: upsert to Pinecone using the raw SDK in parallel batches ──────────
    # Pinecone REST limit: 4 MB / request. At 1536-dim float32 + metadata, 
    # 100 chunks ≈ 700 KB — safe headroom.
    UPSERT_BATCH = 100
    index = pc.Index(INDEX_NAME)

    def _upsert_batch(start: int) -> int:
        batch_vecs = []
        for j in range(start, min(start + UPSERT_BATCH, total)):
            batch_vecs.append({
                "id":     str(uuid.uuid4()),
                "values": vectors[j],
                "metadata": {
                    **{k: str(v) for k, v in metadatas[j].items()},
                    "text": texts[j],
                },
            })
        index.upsert(vectors=batch_vecs)
        return min(start + UPSERT_BATCH, total)

    starts = list(range(0, total, UPSERT_BATCH))
    # Run up to 5 upsert batches concurrently — respects Pinecone rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_upsert_batch, s): s for s in starts}
        done_count = 0
        for fut in concurrent.futures.as_completed(futures):
            done_count += 1
            print(f"[INFO]   batch {done_count}/{len(starts)} upserted ({fut.result()}/{total} chunks)")

    final_count = pc.Index(INDEX_NAME).describe_index_stats().total_vector_count
    print(f"[INFO] Done. Index '{INDEX_NAME}' now has {final_count:,} vectors. Ready to serve.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build or verify the DiaWise Pinecone vector index.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and rebuild the index even if it already exists and is populated.",
    )
    args = parser.parse_args()
    build(force=args.force)
