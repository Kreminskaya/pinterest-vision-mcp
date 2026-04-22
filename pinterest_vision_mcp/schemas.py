from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class PinterestPin(BaseModel):
    url: str = ""
    image_url: str = ""
    title: str = ""
    description: str = ""
    source_domain: str = ""


class PinterestSearchResult(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    query: str = ""
    pins: list[PinterestPin] = Field(default_factory=list)
    total_found: int = 0
    searched_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DownloadedAsset(BaseModel):
    pin_url: str = ""
    image_url: str = ""
    local_path: str = ""
    filename: str = ""
    size_bytes: int = 0
    ok: bool = True
    error: str = ""


class DownloadResult(BaseModel):
    session_id: str = ""
    project_id: str = ""
    downloaded: list[DownloadedAsset] = Field(default_factory=list)
    failed: list[DownloadedAsset] = Field(default_factory=list)
    save_dir: str = ""


class VisualFashionTags(BaseModel):
    lighting_type: str = ""
    composition_type: str = ""
    camera_distance: str = ""
    mood: str = ""
    palette: str = ""
    segment: str = ""
    shot_type: str = ""
    garment_focus: str = ""
    styling_signals: str = ""
    brand_feel: str = ""
    overall_quality: str = ""
    raw_description: str = ""


class VisualAnalysis(BaseModel):
    local_path: str = ""
    tags: VisualFashionTags = Field(default_factory=VisualFashionTags)
    analyzed_by: str = ""
    analyzed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ok: bool = True
    error: str = ""


class IngestResult(BaseModel):
    session_id: str = ""
    project_id: str = ""
    agent_name: str = ""
    ingested_count: int = 0
    collection_name: str = "nasmotrennost"
    chroma_ids: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    session_id: str = ""
    query: str = ""
    project_id: str = ""
    agent_name: str = ""
    search: Optional[PinterestSearchResult] = None
    download: Optional[DownloadResult] = None
    analyses: list[VisualAnalysis] = Field(default_factory=list)
    ingest: Optional[IngestResult] = None
    summary: str = ""
