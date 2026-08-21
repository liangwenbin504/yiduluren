"""轻量级向量知识库 - 基于 numpy 的字符 n-gram 语义检索

使用字符 n-gram TF-IDF + 余弦相似度实现语义搜索。
无需任何外部依赖（仅需 numpy），可作为 ChromaDB 的轻量替代。
当 ChromaDB 可用时自动升级为完整向量数据库。
"""
import numpy as np
import json
import os
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from collections import Counter

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class NgramVectorizer:
    """字符 n-gram TF-IDF 向量化器"""

    def __init__(self, ngram_range: Tuple[int, int] = (2, 4), max_features: int = 5000):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vocab = {}
        self.idf = {}
        self.fitted = False

    def _extract_ngrams(self, text: str) -> List[str]:
        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(text) - n + 1):
                ngrams.append(text[i:i + n])
        return ngrams

    def fit(self, texts: List[str]):
        doc_freq = Counter()
        all_ngrams = Counter()
        for text in texts:
            text = re.sub(r'\s+', '', text)
            ngrams = set(self._extract_ngrams(text))
            doc_freq.update(ngrams)
            all_ngrams.update(ngrams)

        ndocs = len(texts)
        sorted_ngrams = sorted(all_ngrams.items(), key=lambda x: -x[1])
        top_ngrams = [ng for ng, _ in sorted_ngrams[:self.max_features]]
        self.vocab = {ng: i for i, ng in enumerate(top_ngrams)}
        self.idf = {ng: np.log((ndocs + 1) / (doc_freq[ng] + 1)) + 1
                    for ng in self.vocab}
        self.fitted = True
        return self

    def transform(self, texts: List[str]) -> np.ndarray:
        if not self.fitted:
            raise ValueError("向量化器尚未训练，请先调用 fit()")
        matrix = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for i, text in enumerate(texts):
            text = re.sub(r'\s+', '', text)
            ngrams = self._extract_ngrams(text)
            tf = Counter(ngrams)
            total = len(ngrams) if ngrams else 1
            for ng, count in tf.items():
                if ng in self.vocab:
                    tfidf = (count / total) * self.idf[ng]
                    matrix[i, self.vocab[ng]] = tfidf
        return matrix

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        self.fit(texts)
        return self.transform(texts)


class VectorKnowledgeBase:
    """向量知识库 - 语义检索

    支持两种模式：
    1. numpy 模式（默认） - 使用 n-gram TF-IDF + 余弦相似度
    2. chromadb 模式 - 当 chromadb 可用时自动升级
    """

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "vector_store"
        )
        self.vectorizer = NgramVectorizer()
        self.documents = []
        self.metadata = []
        self.embeddings = None
        self.chroma_collection = None
        self._init_chromadb()

    def _init_chromadb(self):
        if HAS_CHROMADB:
            try:
                os.makedirs(self.persist_dir, exist_ok=True)
                client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=Settings(anonymized_telemetry=False)
                )
                self.chroma_collection = client.get_or_create_collection(
                    name="liuren_knowledge",
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                self.chroma_collection = None

    def add_documents(self, documents: List[Dict],
                      text_fields: List[str] = None):
        """添加文档到向量库

        Args:
            documents: 文档列表，每个文档为 dict
            text_fields: 用于向量化的文本字段名列表，默认 ["原文", "预测事情", "实际事情"]
        """
        if not documents:
            return

        text_fields = text_fields or ["原文", "预测事情", "实际事情"]
        existing_ids = set()
        if self.chroma_collection:
            try:
                existing_ids = set(self.chroma_collection.get()["ids"])
            except Exception:
                existing_ids = set()

        for i, doc in enumerate(documents):
            doc_id = doc.get("id", f"doc_{i}")

            texts = []
            for field in text_fields:
                val = doc.get(field, "")
                if val:
                    texts.append(val)
            combined_text = " ".join(texts)

            if not combined_text.strip():
                continue

            self.documents.append(doc)
            self.metadata.append({
                "id": doc_id,
                "zhanshi": doc.get("占事", doc.get("stock_name", "")),
                "text": combined_text,
                "is_correct": doc.get("is_correct", False)
            })

            if self.chroma_collection and doc_id not in existing_ids:
                try:
                    self.chroma_collection.add(
                        ids=[doc_id],
                        documents=[combined_text],
                        metadatas=[{
                            "source": "training",
                            "zhanshi": doc.get("占事", ""),
                            "stock_code": doc.get("stock_code", "")
                        }]
                    )
                except Exception:
                    pass

        if not self.chroma_collection and self.documents:
            texts = [m["text"] for m in self.metadata]
            self.embeddings = self.vectorizer.fit_transform(texts)

    def query(self, query_text: str, top_k: int = 5,
              zhanshi_filter: str = None) -> List[Dict]:
        """语义搜索最相似的案例

        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            zhanshi_filter: 可选，按占事类型过滤

        Returns:
            相似案例列表，每项包含 case 和 similarity 分数
        """
        if not self.documents:
            return []

        candidates = self.documents
        candidate_meta = self.metadata

        if zhanshi_filter:
            filtered = []
            for doc, meta in zip(candidates, candidate_meta):
                doc_zhanshi = doc.get("占事", "") or doc.get("stock_name", "")
                if zhanshi_filter in str(doc_zhanshi):
                    filtered.append((doc, meta))
            if not filtered:
                return []
            candidates = [d for d, _ in filtered]
            candidate_meta = [m for _, m in filtered]

        if self.chroma_collection:
            return self._chroma_search(query_text, candidates, candidate_meta, top_k)
        else:
            return self._numpy_search(query_text, candidates, candidate_meta, top_k)

    def _numpy_search(self, query_text: str, documents: List[Dict],
                      metadata: List[Dict], top_k: int) -> List[Dict]:
        query_vec = self.vectorizer.transform([query_text])
        if query_vec.shape[1] != self.embeddings.shape[1]:
            return []
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
        query_vec = query_vec / query_norm

        doc_norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        doc_norms[doc_norms == 0] = 1
        doc_embs = self.embeddings / doc_norms

        similarities = np.dot(doc_embs, query_vec.T).flatten()

        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        seen_ids = set()
        for idx in top_indices:
            if idx < len(documents):
                doc = documents[idx]
                doc_id = doc.get("id", "")
                if doc_id in seen_ids:
                    continue
                seen_ids.add(doc_id)
                results.append({
                    "case": doc,
                    "similarity": float(similarities[idx]),
                    "method": "numpy_ngram"
                })
        return results

    def _chroma_search(self, query_text: str, documents: List[Dict],
                       metadata: List[Dict], top_k: int) -> List[Dict]:
        try:
            results = self.chroma_collection.query(
                query_texts=[query_text],
                n_results=min(top_k, len(documents))
            )
            chroma_ids = results["ids"][0] if results["ids"] else []
            chroma_distances = results["distances"][0] if results["distances"] else []

            id_to_doc = {d.get("id", ""): d for d in documents}
            matched = []
            for cid, dist in zip(chroma_ids, chroma_distances):
                if cid in id_to_doc:
                    matched.append({
                        "case": id_to_doc[cid],
                        "similarity": float(1.0 - dist / 2.0),
                        "method": "chromadb"
                    })
            return matched
        except Exception:
            return self._numpy_search(query_text, documents, metadata, top_k)

    def save(self, path: str = None):
        """保存向量库到磁盘"""
        save_path = path or os.path.join(self.persist_dir, "vector_index.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        data = {
            "documents": self.documents,
            "metadata": self.metadata
        }
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str = None):
        """从磁盘加载向量库"""
        load_path = path or os.path.join(self.persist_dir, "vector_index.json")
        if not os.path.exists(load_path):
            return False
        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.documents = data.get("documents", [])
        self.metadata = data.get("metadata", [])
        if self.documents and not self.chroma_collection:
            texts = [m["text"] for m in self.metadata]
            self.embeddings = self.vectorizer.fit_transform(texts)
        return True

    def get_statistics(self) -> Dict:
        return {
            "total_documents": len(self.documents),
            "mode": "chromadb" if self.chroma_collection else "numpy_ngram",
            "chromadb_available": HAS_CHROMADB
        }
