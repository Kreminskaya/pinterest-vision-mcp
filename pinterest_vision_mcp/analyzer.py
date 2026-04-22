from __future__ import annotations
import base64
import os
import json
from pathlib import Path
from typing import Optional
import httpx

from pinterest_vision_mcp.schemas import VisualAnalysis, VisualFashionTags

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANALYZE_MODEL = os.getenv("PINTEREST_VISION_MODEL", "anthropic/claude-sonnet-4-6")

FASHION_ANALYSIS_PROMPT = (
    "You are an expert fashion analyst and art director. "
    "Analyze this image and return a JSON object with exactly these fields: "
    '{"lighting_type": "...", "composition_type": "...", "camera_distance": "...", '
    '"mood": "...", "palette": "...", "segment": "...", "shot_type": "...", '
    '"garment_focus": "...", "styling_signals": "...", "brand_feel": "...", '
    '"overall_quality": "reference-worthy OR average OR not useful", '
    '"raw_description": "2-3 sentence summary"} '
    "Return ONLY valid JSON, no markdown."
)


def _image_to_base64(path: str) -> Optional[str]:
    try:
        return base64.b64encode(Path(path).read_bytes()).decode("utf-8")
    except Exception:
        return None


def _get_mime_type(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"):
        return "image/png"
    if p.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def analyze_image(local_path: str, model: Optional[str] = None) -> VisualAnalysis:
    used_model = model or ANALYZE_MODEL
    result = VisualAnalysis(local_path=local_path, analyzed_by=used_model)

    if not OPENROUTER_API_KEY:
        result.ok = False
        result.error = "OPENROUTER_API_KEY not set"
        return result

    b64 = _image_to_base64(local_path)
    if not b64:
        result.ok = False
        result.error = f"Cannot read image: {local_path}"
        return result

    payload = {
        "model": used_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{_get_mime_type(local_path)};base64,{b64}"
                        },
                    },
                    {"type": "text", "text": FASHION_ANALYSIS_PROMPT},
                ],
            }
        ],
        "max_tokens": 800,
        "temperature": 0.1,
    }

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            tags_dict = json.loads(content)
            result.tags = VisualFashionTags(**tags_dict)
            result.ok = True
    except json.JSONDecodeError as e:
        result.ok = False
        result.error = f"JSON parse error: {e}"
    except Exception as e:
        result.ok = False
        result.error = str(e)

    return result


def analyze_batch(
    local_paths: list[str], model: Optional[str] = None
) -> list[VisualAnalysis]:
    return [analyze_image(p, model) for p in local_paths]
