"""
litrun Edge Vector Search & Offline Local RAG (Retrieval-Augmented Generation)
Pure-Python + SQLite zero-dependency vector store and embedding engine for embedded Linux.
Runs completely offline on air-gapped SBCs without cloud vector databases.
"""

from __future__ import annotations
import hashlib
import json
import math
import os
import re
import sqlite3
import struct
import time
from typing import List, Dict, Any, Optional, Tuple

DEFAULT_DB_PATH = os.path.expanduser("~/.cache/litrun/rag.db")
DEFAULT_VECTOR_DIM = 128


def _normalize_vector(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm < 1e-9:
        return vec
    return [x / norm for x in vec]


def compute_lightweight_embedding(text: str, dim: int = DEFAULT_VECTOR_DIM) -> List[float]:
    """
    Computes a deterministic, normalized term & n-gram projection embedding.
    Zero floating-point heavy dependencies, ultra-fast on Cortex-A53/A72/A76.
    """
    vec = [0.0] * dim
    tokens = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
    if not tokens:
        return vec

    # Word-level hashed projections with positive term weights
    for i, tok in enumerate(tokens):
        # 1-gram
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0

        # 2-gram for phrase context
        if i < len(tokens) - 1:
            bi = f"{tok}_{tokens[i+1]}"
            hb = int(hashlib.md5(bi.encode("utf-8")).hexdigest()[:8], 16)
            vec[hb % dim] += 1.5

        # Character trigrams for morphological robustness
        if len(tok) >= 3:
            for c in range(len(tok) - 2):
                tri = tok[c:c+3]
                ht = int(hashlib.md5(tri.encode("utf-8")).hexdigest()[:8], 16)
                vec[ht % dim] += 0.3

    return _normalize_vector(vec)


def serialize_vector(vec: List[float]) -> bytes:
    """Serializes float list to compact binary BLOB."""
    return struct.pack(f"{len(vec)}f", *vec)


def deserialize_vector(blob: bytes) -> List[float]:
    """Deserializes binary BLOB to float list."""
    dim = len(blob) // 4
    return list(struct.unpack(f"{dim}f", blob))


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates dot product of normalized vectors."""
    if len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))


class EdgeVectorStore:
    """Embedded SQLite vector database with cosine-similarity ranking."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    chunk_index INTEGER,
                    text TEXT,
                    vector BLOB,
                    created_at REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source)")
            conn.commit()

    def add_document(self, source: str, text: str, chunk_size: int = 300, overlap: int = 50) -> int:
        """Splits document text into overlapping chunks and indexes them."""
        # Clean text
        text = text.strip()
        if not text:
            return 0

        # Split into word chunks
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunks.append(" ".join(chunk_words))
            i += (chunk_size - overlap)
            if i >= len(words):
                break

        now = time.time()
        with self._get_connection() as conn:
            # Clear previous entries from this source
            conn.execute("DELETE FROM chunks WHERE source = ?", (source,))
            for idx, chunk_text in enumerate(chunks):
                vec = compute_lightweight_embedding(chunk_text)
                blob = serialize_vector(vec)
                conn.execute(
                    "INSERT INTO chunks (source, chunk_index, text, vector, created_at) VALUES (?, ?, ?, ?, ?)",
                    (source, idx, chunk_text, blob, now)
                )
            conn.commit()

        return len(chunks)

    def search(self, query: str, top_k: int = 3, min_similarity: float = 0.15) -> List[Dict[str, Any]]:
        """Searches indexed knowledge chunks using cosine similarity."""
        query_vec = compute_lightweight_embedding(query)
        scored_results: List[Tuple[float, int, str, str]] = []

        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, source, text, vector FROM chunks")
            for chunk_id, source, text, blob in cursor.fetchall():
                vec = deserialize_vector(blob)
                sim = cosine_similarity(query_vec, vec)
                if sim >= min_similarity:
                    scored_results.append((sim, chunk_id, source, text))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        top = scored_results[:top_k]

        return [
            {
                "id": r[1],
                "source": r[2],
                "text": r[3],
                "similarity": round(r[0], 4),
            }
            for r in top
        ]

    def list_sources(self) -> List[Dict[str, Any]]:
        """Returns list of indexed documents and their chunk counts."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT source, COUNT(*), MIN(created_at) FROM chunks GROUP BY source")
            return [
                {"source": row[0], "chunks": row[1], "indexed_at": row[2]}
                for row in cursor.fetchall()
            ]

    def clear(self) -> None:
        """Empties all indexed vectors."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks")
            conn.commit()


def build_rag_augmented_prompt(query: str, contexts: List[Dict[str, Any]]) -> str:
    """Formats retrieved context chunks into an augmented RAG prompt."""
    if not contexts:
        return query

    context_str = "\n\n".join(
        f"[Context Chunk {i+1} - Source: {c['source']} (Relevance: {c['similarity']})]\n{c['text']}"
        for i, c in enumerate(contexts)
    )

    return (
        f"You are litrun, an autonomous edge assistant. Use the following retrieved local context to accurately answer the query.\n\n"
        f"--- LOCAL KNOWLEDGE BASE ---\n"
        f"{context_str}\n"
        f"-----------------------------\n\n"
        f"Query: {query}\n"
        f"Answer concisely using the provided context."
    )
