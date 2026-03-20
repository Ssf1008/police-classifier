from __future__ import annotations

import argparse
import json
import sys

from config import SETTINGS
from rag_classifier import RAGIncidentClassifier


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG incident classification CLI.")
    ap.add_argument(
        "--persist_dir",
        default=SETTINGS.CHROMA_PERSIST_DIR,
        help="Chroma persist directory.",
    )
    ap.add_argument(
        "--collection",
        default=SETTINGS.CHROMA_COLLECTION,
        help="Chroma collection name.",
    )
    ap.add_argument(
        "--embedding_model",
        default=SETTINGS.EMBEDDING_MODEL_NAME,
        help="HuggingFace embedding model name.",
    )
    ap.add_argument(
        "--llm_provider",
        choices=["openai", "ollama"],
        default="openai",
        help="LLM provider.",
    )
    ap.add_argument(
        "--ollama_model",
        default=SETTINGS.OLLAMA_MODEL,
        help="Ollama model (used when --llm_provider=ollama).",
    )
    ap.add_argument("--query", required=True, help="New incident text to classify.")
    ap.add_argument("--top_k", type=int, default=5, help="Retrieve top k similar cases.")
    ap.add_argument(
        "--candidates",
        default="",
        help="Optional candidate categories, separated by commas.",
    )
    ap.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = ap.parse_args()

    # Allow overriding settings via CLI for Ollama model.
    if args.llm_provider == "ollama":
        # Late import to avoid confusion; settings are frozen dataclass, so set env for runtime only.
        import os

        os.environ["OLLAMA_MODEL"] = args.ollama_model

    candidates = [c.strip() for c in args.candidates.split(",") if c.strip()] or None

    clf = RAGIncidentClassifier(
        persist_dir=args.persist_dir,
        collection=args.collection,
        embedding_model=args.embedding_model,
        llm_provider=args.llm_provider,
    )
    result = clf.classify(query=args.query, top_k=args.top_k, candidate_categories=candidates)

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)

