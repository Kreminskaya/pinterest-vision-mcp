from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

from fastmcp import FastMCP
from pinterest_vision_mcp.schemas import (
    PinterestSearchResult,
    VisualAnalysis,
    PipelineResult,
)
from pinterest_vision_mcp.searcher import search_pinterest, download_assets
from pinterest_vision_mcp.analyzer import analyze_batch
from pinterest_vision_mcp.storage import ingest_analyses, search_visual_references

mcp = FastMCP(
    "pinterest-vision-mcp",
    instructions=(
        "Visual intelligence pipeline for fashion and e-commerce. "
        "Use pinterest_pipeline for the full workflow: search → download → analyze → store. "
        "Use visual_search to retrieve stored visual references by semantic similarity."
    ),
)


@mcp.tool()
def pinterest_search(
    query: str,
    limit: int = 20,
) -> dict:
    """Search Pinterest for visual references.
    Returns list of pins with image URLs and metadata.
    Args:
        query: e.g. 'quiet luxury beige coat editorial'
        limit: max pins to return (default 20)
    """
    result = search_pinterest(query=query, limit=limit)
    return result.model_dump()


@mcp.tool()
def pinterest_download(
    search_result: dict,
    max_images: int = 10,
) -> dict:
    """Download images from a pinterest_search result to local filesystem.
    Saves to {PINTEREST_DATA_DIR}/pinterest/{date}/{query_slug}/
    Args:
        search_result: output dict from pinterest_search
        max_images: max images to download (default 10)
    """
    sr = PinterestSearchResult(**search_result)
    result = download_assets(sr, max_images=max_images)
    return result.model_dump()


@mcp.tool()
def pinterest_analyze(
    image_paths: list[str],
    model: str = "",
) -> list[dict]:
    """Analyze images with LLM vision. Returns structured visual tags per image.
    Tags: lighting_type, composition_type, camera_distance, mood, palette, segment,
    shot_type, garment_focus, styling_signals, brand_feel, overall_quality.
    Args:
        image_paths: local file paths to images
        model: optional OpenRouter model override (default from PINTEREST_VISION_MODEL env)
    """
    analyses = analyze_batch(image_paths, model=model or None)
    return [a.model_dump() for a in analyses]


@mcp.tool()
def pinterest_ingest(
    analyses: list[dict],
    query: str = "",
) -> dict:
    """Store visual analyses in ChromaDB vector base for future semantic retrieval.
    Note: on first run, ChromaDB will download an embedding model (~90 MB).
    Args:
        analyses: output list from pinterest_analyze
        query: optional label for what was searched
    """
    analysis_objects = [VisualAnalysis(**a) for a in analyses]
    result = ingest_analyses(analyses=analysis_objects, query=query)
    return result.model_dump()


@mcp.tool()
def pinterest_pipeline(
    query: str,
    limit: int = 15,
    max_download: int = 8,
    analyze: bool = True,
    ingest: bool = True,
) -> dict:
    """Full visual intelligence pipeline: search → download → analyze → store.
    Note: on first run with ingest=True, ChromaDB will download an embedding model (~90 MB).
    Args:
        query: search query, e.g. 'minimal editorial white shirt studio'
        limit: max pins to search (default 15)
        max_download: max images to download and analyze (default 8)
        analyze: run LLM vision analysis (default True)
        ingest: store results in vector base (default True)
    """
    pipeline_result = PipelineResult(query=query)

    search_result = search_pinterest(query=query, limit=limit)
    pipeline_result.session_id = search_result.session_id
    pipeline_result.search = search_result

    if not search_result.pins:
        pipeline_result.summary = f"No pins found for: {query}"
        return pipeline_result.model_dump()

    download_result = download_assets(search_result, max_images=max_download)
    pipeline_result.download = download_result
    downloaded_paths = [a.local_path for a in download_result.downloaded]

    if not downloaded_paths:
        pipeline_result.summary = (
            f"Found {search_result.total_found} pins but download failed"
        )
        return pipeline_result.model_dump()

    if analyze:
        pipeline_result.analyses = analyze_batch(downloaded_paths)

    if ingest and analyze and pipeline_result.analyses:
        ingest_result = ingest_analyses(
            analyses=pipeline_result.analyses,
            session_id=pipeline_result.session_id,
            query=query,
        )
        pipeline_result.ingest = ingest_result
        pipeline_result.summary = (
            f"Complete: {search_result.total_found} found, "
            f"{len(downloaded_paths)} downloaded, "
            f"{len(pipeline_result.analyses)} analyzed, "
            f"{ingest_result.ingested_count} stored"
        )
    else:
        pipeline_result.summary = (
            f"Complete (no ingest): {search_result.total_found} found, "
            f"{len(downloaded_paths)} downloaded"
        )

    return pipeline_result.model_dump()


@mcp.tool()
def visual_search(
    query: str,
    n_results: int = 10,
    segment: str = "",
    shot_type: str = "",
    mood: str = "",
) -> list[dict]:
    """Semantic search across stored visual references.
    Find past analyses by style, mood, segment, or free-text description.
    Args:
        query: e.g. 'dark editorial masculine streetwear close-up'
        n_results: number of results to return (default 10)
        segment: optional filter (luxury / premium / contemporary / streetwear)
        shot_type: optional filter (campaign editorial / e-commerce product / lookbook / ...)
        mood: optional filter by mood string
    """
    filters = {}
    if segment:
        filters["segment"] = {"$eq": segment}
    if shot_type:
        filters["shot_type"] = {"$eq": shot_type}
    if mood:
        filters["mood"] = {"$eq": mood}

    return search_visual_references(
        query=query,
        n_results=n_results,
        filters=filters if filters else None,
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
