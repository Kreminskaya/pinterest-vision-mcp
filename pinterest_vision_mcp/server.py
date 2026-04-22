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
from pinterest_vision_mcp.storage import ingest_analyses, search_nasmotrennost

mcp = FastMCP(
    "pinterest-vision-mcp",
    instructions=(
        "Visual intelligence pipeline for fashion/e-commerce production. "
        "Use pinterest_pipeline for full workflow. "
        "Use nasmotrennost_search to retrieve past visual analyses."
    ),
)


@mcp.tool()
def pinterest_search(
    query: str,
    limit: int = 20,
    session_id: str = "",
    project_id: str = "",
    shot_id: str = "",
) -> dict:
    """Search Pinterest for fashion/e-commerce references.
    Returns list of pins with image URLs and metadata.
    Args:
        query: e.g. 'quiet luxury beige coat editorial'
        limit: max pins (default 20)
        project_id: optional project tracking
        shot_id: optional shot tracking
    """
    result = search_pinterest(
        query=query,
        limit=limit,
        session_id=session_id or None,
        project_id=project_id,
        shot_id=shot_id,
    )
    return result.model_dump()


@mcp.tool()
def pinterest_download(
    search_result: dict,
    project_id: str = "",
    max_images: int = 10,
) -> dict:
    """Download images from a pinterest_search result to local filesystem.
    Saves to {PINTEREST_DATA_DIR}/pinterest/{date}/{query_slug}/
    Args:
        search_result: output dict from pinterest_search
        max_images: max to download (default 10)
    """
    sr = PinterestSearchResult(**search_result)
    result = download_assets(sr, project_id=project_id, max_images=max_images)
    return result.model_dump()


@mcp.tool()
def pinterest_analyze(
    image_paths: list[str],
    model: str = "",
) -> list[dict]:
    """Analyze fashion images with LLM vision. Returns structured fashion tags per image.
    Tags: lighting_type, composition_type, camera_distance, mood, palette, segment,
    shot_type, garment_focus, styling_signals, brand_feel, overall_quality.
    Args:
        image_paths: local file paths
        model: optional OpenRouter model override
    """
    analyses = analyze_batch(image_paths, model=model or None)
    return [a.model_dump() for a in analyses]


@mcp.tool()
def pinterest_ingest(
    analyses: list[dict],
    query: str = "",
    session_id: str = "",
    project_id: str = "",
    agent_name: str = "",
) -> dict:
    """Store visual analyses in ChromaDB vector base for future retrieval.
    Args:
        analyses: output list from pinterest_analyze
        agent_name: optional label for who triggered this ingestion
    """
    analysis_objects = [VisualAnalysis(**a) for a in analyses]
    result = ingest_analyses(
        analyses=analysis_objects,
        session_id=session_id,
        project_id=project_id,
        agent_name=agent_name,
        query=query,
    )
    return result.model_dump()


@mcp.tool()
def pinterest_pipeline(
    query: str,
    limit: int = 15,
    max_download: int = 8,
    project_id: str = "",
    agent_name: str = "",
    shot_id: str = "",
    analyze: bool = True,
    ingest: bool = True,
) -> dict:
    """Full visual intelligence pipeline: search -> download -> analyze -> ingest.
    Args:
        query: fashion search query
        limit: max pins to search (15)
        max_download: max images to download and analyze (8)
        project_id: optional project tracking
        agent_name: optional label for the requesting agent
        analyze: run LLM visual analysis (default True)
        ingest: store in vector base (default True)
    """
    pipeline_result = PipelineResult(
        query=query, project_id=project_id, agent_name=agent_name
    )

    search_result = search_pinterest(
        query=query, limit=limit, project_id=project_id, shot_id=shot_id
    )
    pipeline_result.session_id = search_result.session_id
    pipeline_result.search = search_result

    if not search_result.pins:
        pipeline_result.summary = f"No pins found for: {query}"
        return pipeline_result.model_dump()

    download_result = download_assets(
        search_result, project_id=project_id, max_images=max_download
    )
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
            project_id=project_id,
            agent_name=agent_name,
            query=query,
        )
        pipeline_result.ingest = ingest_result
        pipeline_result.summary = (
            f"Complete: {search_result.total_found} found, "
            f"{len(downloaded_paths)} downloaded, "
            f"{len(pipeline_result.analyses)} analyzed, "
            f"{ingest_result.ingested_count} ingested"
        )
    else:
        pipeline_result.summary = (
            f"Complete (no ingest): {search_result.total_found} found, "
            f"{len(downloaded_paths)} downloaded"
        )

    return pipeline_result.model_dump()


@mcp.tool()
def nasmotrennost_search(
    query: str,
    n_results: int = 10,
    segment: str = "",
    shot_type: str = "",
    mood: str = "",
) -> list[dict]:
    """Semantic search in visual intelligence base.
    Find past visual references by style, mood, segment, or description.
    Args:
        query: e.g. 'dark editorial masculine streetwear close-up'
        segment: filter by (luxury/premium/contemporary/streetwear)
        shot_type: filter by (campaign editorial/e-commerce product/lookbook/...)
        mood: filter by mood string
    """
    filters = {}
    if segment:
        filters["segment"] = {"$eq": segment}
    if shot_type:
        filters["shot_type"] = {"$eq": shot_type}
    if mood:
        filters["mood"] = {"$eq": mood}

    return search_nasmotrennost(
        query=query,
        n_results=n_results,
        filters=filters if filters else None,
    )


if __name__ == "__main__":
    mcp.run()
