from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from config import SETTINGS
from ingest import main as ingest_main
from rag_classifier import RAGIncidentClassifier


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="RAG 警情分类系统（建库+查询一体入口）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_ingest = sub.add_parser("ingest", help="读取历史警情并入库到 ChromaDB")
    ap_ingest.add_argument("--input", required=True, help="历史警情 CSV/JSONL/JSON 文件路径")
    ap_ingest.add_argument("--persist_dir", default=SETTINGS.CHROMA_PERSIST_DIR)
    ap_ingest.add_argument("--collection", default=SETTINGS.CHROMA_COLLECTION)
    ap_ingest.add_argument("--embedding_model", default=SETTINGS.EMBEDDING_MODEL_NAME)

    ap_query = sub.add_parser("query", help="输入新警情，检索相似案例并调用大模型分类")
    ap_query.add_argument("--persist_dir", default=SETTINGS.CHROMA_PERSIST_DIR)
    ap_query.add_argument("--collection", default=SETTINGS.CHROMA_COLLECTION)
    ap_query.add_argument("--embedding_model", default=SETTINGS.EMBEDDING_MODEL_NAME)
    ap_query.add_argument("--llm_provider", choices=["openai", "ollama"], default="openai")
    ap_query.add_argument("--ollama_model", default=SETTINGS.OLLAMA_MODEL)
    ap_query.add_argument("--query", required=True, help="新警情文本")
    ap_query.add_argument("--top_k", type=int, default=5)
    ap_query.add_argument("--candidates", default="", help="可选：候选类别，用英文逗号分隔")
    ap_query.add_argument("--pretty", action="store_true")

    return ap


def _run_ingest(args: argparse.Namespace) -> None:
    # 复用 ingest.py 的 CLI：直接构造 argv 调用其 main()
    argv = [
        "ingest.py",
        "--input",
        args.input,
        "--persist_dir",
        args.persist_dir,
        "--collection",
        args.collection,
        "--embedding_model",
        args.embedding_model,
    ]
    sys.argv = argv
    ingest_main()


def _run_query(args: argparse.Namespace) -> None:
    if args.llm_provider == "ollama":
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
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))


def main(argv: Optional[list[str]] = None) -> None:
    ap = _build_parser()
    args = ap.parse_args(argv)

    if args.cmd == "ingest":
        _run_ingest(args)
        return
    if args.cmd == "query":
        _run_query(args)
        return

    raise ValueError(f"Unknown cmd: {args.cmd}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
