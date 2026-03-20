from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

from config import SETTINGS
from rag_core import chroma_similarity_search, get_vectorstore


class ClassificationOutput(BaseModel):
    category: str = Field(..., description="分类类别（简短）")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 0-1")
    reason: str = Field(..., description="分类理由（简洁、可追溯到相似案例）")


@dataclass(frozen=True)
class SimilarCase:
    id: Optional[str]
    label: Optional[str]
    score: float
    text: str


LLMProvider = Literal["openai", "ollama"]


def _build_llm(provider: LLMProvider, *, temperature: float = 0.0):
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=SETTINGS.OPENAI_MODEL, temperature=temperature)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=SETTINGS.OLLAMA_MODEL, temperature=temperature)

    raise ValueError(f"Unsupported provider: {provider}")


def _format_cases_for_prompt(cases: Sequence[SimilarCase]) -> str:
    lines: List[str] = []
    for i, c in enumerate(cases, start=1):
        label = c.label if c.label is not None else ""
        cid = c.id if c.id is not None else ""
        lines.append(
            f"[{i}] id={cid} label={label} score={c.score:.4f}\n案例文本: {c.text}"
        )
    return "\n\n".join(lines)


class RAGIncidentClassifier:
    def __init__(
        self,
        *,
        persist_dir: str = SETTINGS.CHROMA_PERSIST_DIR,
        collection: str = SETTINGS.CHROMA_COLLECTION,
        embedding_model: str = SETTINGS.EMBEDDING_MODEL_NAME,
        llm_provider: LLMProvider = "openai",
    ) -> None:
        self.vs = get_vectorstore(
            persist_dir=persist_dir,
            collection=collection,
            embedding_model_name=embedding_model,
        )
        self.llm_provider = llm_provider

    def retrieve(self, *, query: str, top_k: int = 5) -> List[SimilarCase]:
        hits = chroma_similarity_search(self.vs, query=query, top_k=top_k)
        cases: List[SimilarCase] = []
        for text, score, meta in hits:
            cases.append(
                SimilarCase(
                    id=meta.get("id") or meta.get("doc_id") or None,
                    label=meta.get("label"),
                    score=score,
                    text=text,
                )
            )
        return cases

    def classify(
        self,
        *,
        query: str,
        top_k: int = 5,
        candidate_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        cases = self.retrieve(query=query, top_k=top_k)

        # If user didn't pass candidate categories, derive from retrieved labels.
        if candidate_categories is None:
            derived = []
            for c in cases:
                if c.label and c.label not in derived:
                    derived.append(c.label)
            candidate_categories = derived[:12]  # keep prompt compact

        llm = _build_llm(self.llm_provider, temperature=0.0)

        cases_text = _format_cases_for_prompt(cases)
        candidate_text = (
            "、".join(candidate_categories) if candidate_categories else "（不限制）"
        )

        system = (
            "你是警情分拣与分类助手。你必须输出严格 JSON，不要输出除 JSON 以外的任何内容。"
            "置信度必须是 0 到 1 的小数。分类应尽量复用候选类别；若不合适可给出新类别，但要简短。"
        )
        user = f"""
请根据新警情与相似历史案例，输出分类结果。

新警情：
{query}

候选类别：
{candidate_text}

相似案例（按相似度检索返回，score 为距离/相似度指标，仅供参考）：
{cases_text}

输出 JSON schema：
{{
  "category": "string",
  "confidence": 0.0,
  "reason": "string"
}}
""".strip()

        # Use plain invoke and parse JSON defensively for broad compatibility.
        resp = llm.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        content = getattr(resp, "content", resp)
        if not isinstance(content, str):
            content = str(content)

        parsed: Dict[str, Any]
        try:
            parsed = json.loads(content)
        except Exception:
            # Try to extract first JSON object if model added extra tokens.
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError(f"Model output is not JSON: {content}")
            parsed = json.loads(content[start : end + 1])

        out = ClassificationOutput.model_validate(parsed).model_dump()
        return {
            **out,
            "similar_cases": [
                {
                    "id": c.id,
                    "label": c.label,
                    "score": c.score,
                    "text": (c.text[:160] + "…") if len(c.text) > 160 else c.text,
                }
                for c in cases
            ],
        }

