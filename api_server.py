"""
FastAPI 服务 - 警情分类 API
在 PyCharm 中运行这个文件，提供 HTTP 接口给 Dify 调用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging

from rag_classifier import RAGIncidentClassifier
from config import SETTINGS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="警情分类 API",
    description="基于 RAG 的警情分类服务",
    version="1.0.0"
)

# 添加 CORS 支持，允许 Dify 跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimilarCase(BaseModel):
    """相似案例"""
    id: Optional[str]
    label: Optional[str]
    score: float
    text: str


class ClassifyRequest(BaseModel):
    """分类请求"""
    query: str  # 新警情文本
    top_k: int = 5  # 检索相似案例数量
    llm_provider: str = "openai"  # LLM 提供商：openai 或 ollama


class ClassifyResponse(BaseModel):
    """分类响应"""
    category: str  # 分类类别
    confidence: float  # 置信度 (0-1)
    reason: str  # 分类理由
    similar_cases: List[SimilarCase]  # 相似案例列表


@app.post("/classify", response_model=ClassifyResponse, summary="警情分类")
async def classify_post(req: ClassifyRequest):
    """
    对新警情进行分类（POST 方法）
    
    参数:
    - query: 新警情文本
    - top_k: 检索相似案例数量（默认5）
    - llm_provider: LLM 提供商（openai 或 ollama）
    
    返回:
    - category: 分类类别
    - confidence: 置信度
    - reason: 分类理由
    - similar_cases: 相似案例
    """
    return await _classify_impl(req)


@app.get("/classify", response_model=ClassifyResponse, summary="警情分类")
async def classify_get(req: ClassifyRequest):
    """
    对新警情进行分类（GET 方法，接受 JSON body）
    
    参数:
    - query: 新警情文本
    - top_k: 检索相似案例数量（默认5）
    - llm_provider: LLM 提供商（openai 或 ollama）
    
    返回:
    - category: 分类类别
    - confidence: 置信度
    - reason: 分类理由
    - similar_cases: 相似案例
    """
    return await _classify_impl(req)


async def _classify_impl(req: ClassifyRequest):
    """分类实现"""
    try:
        logger.info(f"收到分类请求: {req.query[:50]}...")
        
        # 创建分类器
        clf = RAGIncidentClassifier(
            persist_dir=SETTINGS.CHROMA_PERSIST_DIR,
            collection=SETTINGS.CHROMA_COLLECTION,
            embedding_model=SETTINGS.EMBEDDING_MODEL_NAME,
            llm_provider=req.llm_provider,
        )
        
        # 执行分类
        result = clf.classify(query=req.query, top_k=req.top_k)
        
        logger.info(f"分类完成: {result['category']}")
        return result
        
    except Exception as e:
        logger.error(f"分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")


@app.get("/health", summary="健康检查")
async def health():
    """检查服务是否正常运行"""
    return {"status": "ok", "message": "服务正常运行"}


@app.get("/", summary="API 文档")
async def root():
    """返回 API 信息"""
    return {
        "name": "警情分类 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "classify": "POST /classify - 对警情进行分类",
            "health": "GET /health - 健康检查"
        }
    }


if __name__ == "__main__":
    import uvicorn
    # 启动服务：http://localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

