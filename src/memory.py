"""memory.py — optional ChromaDB-backed lesson memory.

Stores generated lessons and retrieves related ones (or prior-chapter context)
so the graph can keep continuity across a curriculum. Entirely optional: if
chromadb is not installed, disabled, or errors, every function degrades to a
safe no-op (returns ``False``/``[]``/``""``) and the graph runs unchanged.

Memory is **opt-in**: set ``CHROMA_MEMORY=true`` to enable it (the first call then
downloads a small embedding model). It is off by default so the graph runs fast
with no extra downloads. Choose the store location with ``CHROMA_DIR`` (default
``.chroma``).
"""

from __future__ import annotations

import hashlib
import os
import re

_COLLECTION_NAME = "alphachem_lessons"
_PERSIST_DIR = os.environ.get("CHROMA_DIR", ".chroma")


def _truthy(value: str | None) -> bool:
    return str(value).lower() in ("1", "true", "yes", "on")


def is_enabled() -> bool:
    """True only if memory is switched on AND chromadb imports successfully."""
    if not _truthy(os.environ.get("CHROMA_MEMORY", "false")):
        return False
    try:
        import chromadb  # noqa: F401
    except ImportError:
        return False
    return True


def _get_collection():
    """Return the Chroma collection, or None if memory is unavailable."""
    if not is_enabled():
        return None
    try:
        import chromadb

        client = chromadb.PersistentClient(path=_PERSIST_DIR)
        return client.get_or_create_collection(_COLLECTION_NAME)
    except Exception:
        return None


def _lesson_id(lesson: dict) -> str:
    key = "|".join(
        str(lesson.get(k, ""))
        for k in ("unit_name", "chapter_name", "lesson_name")
    )
    return hashlib.md5(key.encode()).hexdigest()


def _chapter_number(name: str) -> int | None:
    match = re.search(r"\d+", name or "")
    return int(match.group()) if match else None


def save_lesson_memory(lesson: dict, content: str, summary: str = "",
                       evaluation: dict | None = None) -> bool:
    """Upsert a lesson's summary into the vector store. Returns True on success."""
    collection = _get_collection()
    if collection is None:
        return False
    try:
        document = summary.strip() or content[:2000]
        metadata = {
            "unit": lesson.get("unit_name", ""),
            "chapter": lesson.get("chapter_name", ""),
            "lesson": lesson.get("lesson_name", ""),
            "chapter_number": _chapter_number(lesson.get("chapter_name", "")) or -1,
            "summary": (summary or "")[:1500],
        }
        if evaluation:
            rd = evaluation.get("readability", {})
            metadata["flesch"] = float(rd.get("flesch_reading_ease", 0) or 0)
        collection.upsert(ids=[_lesson_id(lesson)], documents=[document],
                          metadatas=[metadata])
        return True
    except Exception:
        return False


def retrieve_related_lessons(query: str, n_results: int = 3) -> list[dict]:
    """Semantic search for related lessons. Returns a list of {summary, ...meta}."""
    collection = _get_collection()
    if collection is None or not query:
        return []
    try:
        res = collection.query(query_texts=[query], n_results=n_results)
        documents = (res.get("documents") or [[]])[0]
        metadatas = (res.get("metadatas") or [[]])[0]
        return [{"summary": doc, **(meta or {})}
                for doc, meta in zip(documents, metadatas)]
    except Exception:
        return []


def retrieve_previous_chapter_context(lesson: dict) -> str:
    """Return concatenated summaries from the immediately preceding chapter.

    Used to give the planner continuity with what students just learned. Returns
    an empty string if memory is off or nothing is stored for that chapter.
    """
    collection = _get_collection()
    if collection is None:
        return ""
    current = _chapter_number(lesson.get("chapter_name", ""))
    if not current or current <= 1:
        return ""
    try:
        res = collection.get(where={
            "$and": [
                {"unit": lesson.get("unit_name", "")},
                {"chapter_number": current - 1},
            ]
        })
        summaries = [
            (meta or {}).get("summary", "")
            for meta in (res.get("metadatas") or [])
        ]
        return "\n".join(s for s in summaries if s)[:1500]
    except Exception:
        return ""
