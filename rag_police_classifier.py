from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import Generation, LLMResult
from sklearn.feature_extraction.text import HashingVectorizer
import numpy as np


PROMPT_TEMPLATE = """你是一个警情分类专家。根据以下参考案例，对新的警情进行分类。
参考案例：
{references}
新警情：
{query}
请按照参考案例的分类标准，给出：
1. 分类类别：[类别名称]
2. 分类理由：[简要说明]
3. 置信度：[高/中/低]
"""


@dataclass(frozen=True)
class RagConfig:
    csv_path: str = "police_cases_labeled.csv"
    persist_dir: str = "./chroma_police_cases"
    collection_name: str = "police_cases"
    top_k: int = 5
    # 默认使用“离线可用”的哈希向量化 Embedding（无需下载模型、无外网也能跑通）
    embedding_backend: str = "hash"  # "hash" | "huggingface"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"  # 仅 huggingface backend 用


class SimulatedPoliceLLM(LLM):
    """
    一个“模拟大模型”，用于离线跑通 RAG + LangChain 流程：
    - 会读取提示词中的“参考案例”，综合相似案例标签 + 关键字规则，输出 3 行固定格式。
    - 之后对接百川/通义千问时，只需替换这个 LLM。
    """

    @property
    def _llm_type(self) -> str:
        return "simulated-police-llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        refs = _parse_references_from_prompt(prompt)
        query = _parse_query_from_prompt(prompt)

        predicted_label, confidence, rationale = _classify_with_refs_and_rules(
            query=query,
            refs=refs,
        )

        return (
            f"1. 分类类别：{predicted_label}\n"
            f"2. 分类理由：{rationale}\n"
            f"3. 置信度：{confidence}"
        )

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> LLMResult:
        gens: List[List[Generation]] = []
        for p in prompts:
            text = self._call(p, stop=stop, **kwargs)
            gens.append([Generation(text=text)])
        return LLMResult(generations=gens)


class HashEmbeddings(Embeddings):
    """
    纯离线 Embedding：HashingVectorizer -> L2 归一化后的稠密向量。
    - 优点：无需网络、无模型文件、可复现、速度快
    - 缺点：语义能力弱于神经网络 embedding（但足以演示 RAG 流程）
    """

    def __init__(self, n_features: int = 512):
        self._vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm=None,
            lowercase=False,
            analyzer="char_wb",
            ngram_range=(2, 4),
        )
        self._n_features = n_features

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        mat = self._vectorizer.transform(texts)
        arr = mat.astype(np.float32).toarray()
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        arr = arr / np.maximum(norms, 1e-12)
        return arr.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


def build_embeddings(cfg: RagConfig) -> Embeddings:
    if cfg.embedding_backend == "hash":
        return HashEmbeddings(n_features=512)

    if cfg.embedding_backend == "huggingface":
        # 延迟导入，避免无网环境直接卡住
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=cfg.embedding_model_name)

    raise ValueError(f"未知 embedding_backend: {cfg.embedding_backend}")


def _parse_references_from_prompt(prompt: str) -> List[Dict[str, str]]:
    """
    从 PROMPT_TEMPLATE 生成的提示词中解析参考案例块。
    参考案例格式（由 build_references_text 生成）：
    [1] 标签=xxx 相似度=0.876 文本=...
    """
    m = re.search(r"参考案例：\s*(.*?)\s*新警情：", prompt, flags=re.S)
    if not m:
        return []
    block = m.group(1).strip()
    if not block:
        return []

    refs: List[Dict[str, str]] = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        m2 = re.match(r"^\[(\d+)\]\s+标签=(.*?)\s+相似度=([0-9.]+)\s+文本=(.*)$", line)
        if not m2:
            continue
        refs.append(
            {
                "rank": m2.group(1),
                "label": m2.group(2).strip(),
                "score": m2.group(3).strip(),
                "text": m2.group(4).strip(),
            }
        )
    return refs


def _parse_query_from_prompt(prompt: str) -> str:
    m = re.search(r"新警情：\s*(.*?)\s*请按照参考案例的分类标准", prompt, flags=re.S)
    return (m.group(1).strip() if m else "").strip()


def _majority_vote(labels: List[str]) -> Tuple[Optional[str], float]:
    if not labels:
        return None, 0.0
    counts: Dict[str, int] = {}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    best = max(counts.items(), key=lambda kv: kv[1])
    return best[0], best[1] / max(1, len(labels))


def _keyword_rule(query: str) -> Optional[str]:
    q = query.strip()
    # 简单规则：真实对接大模型后可删掉/弱化
    rules: List[Tuple[str, List[str]]] = [
        ("诈骗", ["诈骗", "转账", "验证码", "刷流水", "客服", "退款链接", "钓鱼", "刷流水", "中奖", "刷流水"]),
        ("盗窃", ["被盗", "偷", "盗", "撬锁", "冒领", "失窃"]),
        ("抢劫抢夺", ["抢", "抢夺", "抢劫", "夺走"]),
        ("交通事故", ["追尾", "刮擦", "碰撞", "交通事故", "肇事", "赔偿", "交警", "路口事故"]),
        ("急救求助", ["急救", "120", "昏迷", "胸痛", "呼吸困难", "中风", "心梗"]),
        ("救援求助", ["救援", "落水", "走失", "失踪", "被困", "迷路", "搜救"]),
        ("安全隐患", ["煤气", "燃气", "泄漏", "爆炸", "火灾", "塌陷", "井盖", "电线", "安全隐患"]),
        ("噪音扰民", ["扰民", "噪音", "吵", "飙车", "喇叭", "夜间吵闹"]),
        ("财物损坏", ["砸", "损坏", "划车", "玻璃被砸", "镜子被砸"]),
        ("治安案件", ["打架", "斗殴", "威胁", "持刀", "纠纷", "推搡", "寻衅"]),
    ]
    for label, kws in rules:
        for kw in kws:
            if kw in q:
                return label
    return None


def _classify_with_refs_and_rules(query: str, refs: List[Dict[str, str]]) -> Tuple[str, str, str]:
    ref_labels = [r.get("label", "").strip() for r in refs if r.get("label")]
    voted, vote_ratio = _majority_vote(ref_labels)
    rule_label = _keyword_rule(query)

    # 综合：规则优先（更稳），否则多数投票；都没有就回退到“治安案件”
    if rule_label:
        label = rule_label
        confidence = "高" if vote_ratio >= 0.4 and voted == rule_label else "中"
        rationale = _build_rationale(query, refs, chosen_label=label, via="关键词规则")
        return label, confidence, rationale

    if voted:
        label = voted
        confidence = "高" if vote_ratio >= 0.6 else "中"
        rationale = _build_rationale(query, refs, chosen_label=label, via="相似案例标签投票")
        return label, confidence, rationale

    return "治安案件", "低", "缺少明显关键词且相似案例不足，默认归为治安案件。"


def _build_rationale(query: str, refs: List[Dict[str, str]], chosen_label: str, via: str) -> str:
    top = refs[:3]
    if not top:
        return f"基于{via}，新警情更符合“{chosen_label}”特征。"
    hints = "；".join([f"[{r.get('rank')}] {r.get('label')}({r.get('score')})" for r in top])
    return f"基于{via}：新警情与参考案例 {hints} 在语义上相近，且符合“{chosen_label}”的典型特征。"


def load_labeled_cases(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    expected = {"id", "text", "label"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"CSV 缺少字段: {sorted(missing)}，需要列: {sorted(expected)}")
    df["id"] = df["id"].astype(str)
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(str)
    return df


def build_vector_store(df: pd.DataFrame, cfg: RagConfig) -> Chroma:
    embeddings = build_embeddings(cfg)

    docs: List[Document] = []
    ids: List[str] = []
    for row in df.itertuples(index=False):
        ids.append(str(row.id))
        docs.append(
            Document(
                page_content=str(row.text),
                metadata={"id": str(row.id), "label": str(row.label)},
            )
        )

    os.makedirs(cfg.persist_dir, exist_ok=True)

    # 为了可重复运行：每次重建 collection（简单清晰）
    # Chroma 会在同名 collection 下 upsert，因此先删除持久化目录更直接。
    # 这里做最小化处理：如果目录存在则继续写入并覆盖同 id。
    vs = Chroma(
        collection_name=cfg.collection_name,
        persist_directory=cfg.persist_dir,
        embedding_function=embeddings,
    )
    vs.add_documents(documents=docs, ids=ids)
    return vs


def retrieve_similar_cases(
    vector_store: Chroma, query: str, top_k: int
) -> List[Tuple[Document, float]]:
    # 这里用“相似度搜索带分数”，score 越小通常表示越相似（取决于距离度量）。
    # 为了展示直观，把它转换成一个 0~1 的“相似度”近似值。
    results = vector_store.similarity_search_with_score(query, k=top_k)
    return results


def build_references_text(similar: List[Tuple[Document, float]]) -> str:
    lines: List[str] = []
    for i, (doc, score) in enumerate(similar, start=1):
        label = doc.metadata.get("label", "")
        # 将距离分数粗略映射为相似度（越大越相似）
        sim = 1.0 / (1.0 + float(score)) if score is not None else 0.0
        text = (doc.page_content or "").replace("\n", " ").strip()
        lines.append(f"[{i}] 标签={label} 相似度={sim:.3f} 文本={text}")
    return "\n".join(lines) if lines else "（未检索到参考案例）"


def build_chain():
    llm = SimulatedPoliceLLM()
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["references", "query"],
    )
    return {"llm": llm, "prompt": prompt}


def parse_llm_output(text: str) -> Dict[str, str]:
    # 兼容中文冒号/英文冒号
    def _get(pattern: str) -> str:
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""

    category = _get(r"分类类别[:：]\s*(.+)")
    reason = _get(r"分类理由[:：]\s*(.+)")
    confidence = _get(r"置信度[:：]\s*(高|中|低)")
    return {"category": category, "reason": reason, "confidence": confidence}


def classify_incident(query: str, cfg: RagConfig) -> Dict[str, Any]:
    df = load_labeled_cases(cfg.csv_path)
    vs = build_vector_store(df, cfg)

    similar = retrieve_similar_cases(vs, query=query, top_k=cfg.top_k)
    references = build_references_text(similar)

    chain = build_chain()
    prompt_text = chain["prompt"].format(references=references, query=query)
    llm_text = chain["llm"]._call(prompt_text)
    parsed = parse_llm_output(llm_text)

    debug_similar = [
        {
            "rank": i + 1,
            "label": doc.metadata.get("label"),
            "score_raw": float(score),
            "text": doc.page_content,
        }
        for i, (doc, score) in enumerate(similar)
    ]

    return {
        "query": query,
        "references_text": references,
        "llm_output": llm_text,
        "result": parsed,
        "topk_cases": debug_similar,
    }


def main() -> None:
    cfg = RagConfig()

    test_queries = [
        "我父亲突然胸口疼痛出汗，呼吸困难，需要马上急救",
        "我在路口被追尾了，没有人受伤，但对方不愿意赔偿",
        "有人冒充客服让我点退款链接，结果验证码被套走了",
        "小区里有人拿刀威胁我家人，还踹门砸东西",
        "车停在小区里后视镜被砸坏了，麻烦处理",
        "半夜楼上一直吵闹，还有人飙车轰鸣声，影响休息",
    ]

    for q in test_queries:
        out = classify_incident(q, cfg)
        print("=" * 80)
        print("新警情：", out["query"])
        print("-" * 80)
        print("RAG 检索到的参考案例：")
        print(out["references_text"])
        print("-" * 80)
        print("模型输出：")
        print(out["llm_output"])
        print("-" * 80)
        print("结构化结果：")
        print(json.dumps(out["result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

