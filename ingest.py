from __future__ import annotations

import argparse
from typing import Dict, List

from tqdm import tqdm

from config import SETTINGS
from data_io import load_incidents
from rag_core import chroma_add_texts, get_vectorstore


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest historical incidents into ChromaDB.")
    ap.add_argument("--input", required=True, help="Path to CSV/JSONL historical incidents.")
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
    args = ap.parse_args()

    rows = load_incidents(args.input)
    vs = get_vectorstore(
        persist_dir=args.persist_dir,
        collection=args.collection,
        embedding_model_name=args.embedding_model,
    )

    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[Dict] = []
    for r in tqdm(rows, desc="Preparing documents"):
        ids.append(r.id)
        texts.append(r.text)
        metadatas.append({"id": r.id, "label": r.label, "source": args.input})

    chroma_add_texts(vs, ids=ids, texts=texts, metadatas=metadatas)
    print(
        f"✅ Ingested {len(rows)} records into collection='{args.collection}' at '{args.persist_dir}'."
    )


if __name__ == "__main__":
    main()

