from __future__ import annotations
import os
import re
import uuid
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from pinterest_dl import PinterestDL

    PINTEREST_DL_OK = True
except ImportError:
    PINTEREST_DL_OK = False

from pinterest_vision_mcp.schemas import (
    PinterestPin,
    PinterestSearchResult,
    DownloadedAsset,
    DownloadResult,
)

DATA_ROOT = Path(os.getenv("PINTEREST_DATA_DIR", "./data")) / "pinterest"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", text.lower())[:40]


def search_pinterest(
    query: str,
    limit: int = 20,
) -> PinterestSearchResult:
    sid = str(uuid.uuid4())[:8]
    result = PinterestSearchResult(session_id=sid, query=query)

    if not PINTEREST_DL_OK:
        return result

    try:
        pdl = PinterestDL.with_api()
        pins_raw = pdl.search(query, limit=limit)
        pins = []
        for p in pins_raw:
            if isinstance(p, dict):
                img_url = p.get("image_url") or p.get("src") or ""
                pin_url = p.get("pin_url") or p.get("url") or ""
                title = p.get("title") or p.get("alt_text") or ""
                desc = p.get("description") or ""
            else:
                img_url = getattr(p, "image_url", "") or getattr(p, "src", "")
                pin_url = getattr(p, "url", "") or getattr(p, "pin_url", "")
                title = getattr(p, "title", "") or getattr(p, "alt_text", "")
                desc = getattr(p, "description", "")
            if img_url:
                pins.append(
                    PinterestPin(
                        url=pin_url, image_url=img_url, title=title, description=desc
                    )
                )
        result.pins = pins[:limit]
        result.total_found = len(result.pins)
    except Exception:
        pass

    return result


def download_assets(
    search_result: PinterestSearchResult,
    max_images: int = 10,
) -> DownloadResult:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    slug = _slug(search_result.query)
    save_dir = DATA_ROOT / date_str / slug
    save_dir.mkdir(parents=True, exist_ok=True)

    dr = DownloadResult(
        session_id=search_result.session_id,
        save_dir=str(save_dir),
    )

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for i, pin in enumerate(search_result.pins[:max_images]):
            if not pin.image_url:
                continue
            ext = ".jpg"
            for known_ext in [".jpg", ".jpeg", ".png", ".webp"]:
                if pin.image_url.split("?")[0].lower().endswith(known_ext):
                    ext = known_ext
                    break
            filename = f"{search_result.session_id}_{i:03d}{ext}"
            local_path = save_dir / filename
            asset = DownloadedAsset(
                pin_url=pin.url,
                image_url=pin.image_url,
                local_path=str(local_path),
                filename=filename,
            )
            try:
                resp = client.get(pin.image_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    local_path.write_bytes(resp.content)
                    asset.size_bytes = len(resp.content)
                    dr.downloaded.append(asset)
                else:
                    asset.ok = False
                    asset.error = f"HTTP {resp.status_code}"
                    dr.failed.append(asset)
            except Exception as e:
                asset.ok = False
                asset.error = str(e)
                dr.failed.append(asset)

    return dr
