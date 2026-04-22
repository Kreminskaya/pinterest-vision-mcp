from __future__ import annotations
import os
import uuid
from typing import Optional
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from pinterest_vision_mcp.schemas import VisualAnalysis, IngestResult

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
COLLECTION_NAME = "visual_references"


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
    )


def ingest_analyses(
    analyses: list[VisualAnalysis],
    session_id: str = "",
    query: str = "",
) -> IngestResult:
    result = IngestResult(session_id=session_id)
    successful = [a for a in analyses if a.ok and a.tags.raw_description]
    if not successful:
        return result

    collection = _get_collection()
    ids, documents, metadatas = [], [], []

    for analysis in successful:
        doc_id = f"ref_{str(uuid.uuid4())[:12]}"
        tags = analysis.tags
        doc_text = (
            f"{tags.raw_description} Lighting: {tags.lighting_type}. "
            f"Mood: {tags.mood}. Palette: {tags.palette}. "
            f"Segment: {tags.segment}. Shot type: {tags.shot_type}. "
            f"Brand feel: {tags.brand_feel}."
        )
        metadata = {
            "local_path": analysis.local_path,
            "query": query,
            "session_id": session_id,
            "lighting_type": tags.lighting_type,
            "composition_type": tags.composition_type,
            "camera_distance": tags.camera_distance,
            "mood": tags.mood,
            "palette": tags.palette,
            "segment": tags.segment,
            "shot_type": tags.shot_type,
            "garment_focus": tags.garment_focus,
            "styling_signals": tags.styling_signals,
            "brand_feel": tags.brand_feel,
            "overall_quality": tags.overall_quality,
            "analyzed_by": analysis.analyzed_by,
            "analyzed_at": analysis.analyzed_at,
        }
        ids.append(doc_id)
        documents.append(doc_text)
        metadatas.append(metadata)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    result.ingested_count = len(ids)
    result.chroma_ids = ids
    return result


def search_visual_references(
    query: str,
    n_results: int = 10,
    filters: Optional[dict] = None,
) -> list[dict]:
    collection = _get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=filters if filters else None,
        include=["documents", "metadatas", "distances"],
    )
    output = []
    for i, doc_id in enumerate(results["ids"][0]):
        output.append(
            {
                "id": doc_id,
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return output
