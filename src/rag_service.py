"""PDF extraction, chunking, embeddings, and retrieval-augmented answers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf as fitz

from src.database import get_connection
from src.llm_service import LLMError, embed_texts, generate_response

# Roughly 400-600 tokens if we treat 1 token as ~4 characters.
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 200


def extract_pdf_text(path: str | Path) -> str:
    document = fitz.open(path)
    pages = []
    for page in document:
        pages.append(page.get_text("text"))
    document.close()
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError("This PDF has no extractable text. Try a text-based PDF, not a scanned image.")
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap.")

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = end - overlap
    return chunks


def list_documents() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT d.*, COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.uploaded_at DESC
            """
        ).fetchall()
    return list(rows)


def ingest_pdf(path: str | Path, filename: str | None = None) -> dict[str, Any]:
    file_path = Path(path)
    text = extract_pdf_text(file_path)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No text chunks were created from this PDF.")

    embeddings = embed_texts(chunks)
    stored_name = filename or file_path.name

    with get_connection() as conn:
        document = conn.execute(
            "INSERT INTO documents (filename) VALUES (%s) RETURNING *",
            (stored_name,),
        ).fetchone()
        for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            conn.execute(
                """
                INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (document["id"], index, content, embedding),
            )

    return {
        "document": document,
        "chunk_count": len(chunks),
    }


def retrieve_chunks(question: str, limit: int = 4) -> list[dict[str, Any]]:
    question_embedding = embed_texts([question])[0]
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.content,
                c.chunk_index,
                d.filename,
                (c.embedding <=> %s::vector) AS distance
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
            """,
            (question_embedding, question_embedding, limit),
        ).fetchall()
    return list(rows)


def answer_question(question: str) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise LLMError("Please enter a non-empty question.")

    chunks = retrieve_chunks(question)
    if not chunks:
        return {
            "answer": "No document chunks are stored yet. Upload a PDF first.",
            "sources": [],
        }

    context = "\n\n".join(
        f"Source {index + 1} ({row['filename']}, chunk {row['chunk_index']}):\n{row['content']}"
        for index, row in enumerate(chunks)
    )
    messages = [
        {
            "role": "user",
            "content": (
                "Answer the question using only the sources below. "
                "If the sources do not contain the answer, say you do not know. "
                "Mention source numbers in your answer.\n\n"
                f"Sources:\n{context}\n\nQuestion: {question}"
            ),
        }
    ]
    message = generate_response(messages)
    return {
        "answer": (message.content or "").strip(),
        "sources": chunks,
    }
