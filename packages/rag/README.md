# Dubai Crab RAG 모듈

한국 공문서 벡터 검색 파이프라인

## 설치

```bash
pip install -e .
```

## 사용법

```python
from src.rag import vector_store, embeddings

# 벡터 스토어 초기화
client = vector_store.get_client()
collection = vector_store.get_or_create_collection(client)

# 임베딩 생성
embedder = embeddings.get_embedder()
vectors = embedder.embed_documents(["문서 텍스트"])
```

## 환경 변수

- `CHROMA_PERSIST_DIR`: Chroma 영구 저장 경로
- `EMBEDDING_MODEL`: 임베딩 모델 (기본: BAAI/bge-m3)
- `EMBEDDING_DEVICE`: 디바이스 (cuda/mps/cpu)
