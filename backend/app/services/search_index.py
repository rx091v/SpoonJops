from __future__ import annotations

import json
import logging
from collections.abc import Sequence

import httpx

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _base_url(settings: Settings) -> str | None:
    if not settings.elasticsearch_url:
        return None
    return settings.elasticsearch_url.rstrip("/")


async def ensure_index(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    base_url = _base_url(settings)
    if not base_url:
        return False

    mapping = {
        "mappings": {
            "properties": {
                "job_id": {"type": "keyword"},
                "title": {"type": "text"},
                "company": {"type": "text"},
                "location": {"type": "text"},
                "remote_type": {"type": "text"},
                "source": {"type": "keyword"},
                "source_url": {"type": "keyword"},
                "description": {"type": "text"},
                "matched_keywords": {"type": "text"},
            }
        }
    }

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.get(f"{base_url}/{settings.elasticsearch_index}")
            if response.status_code == 200:
                return True
            create_response = await client.put(f"{base_url}/{settings.elasticsearch_index}", json=mapping)
            create_response.raise_for_status()
            return True
        except httpx.HTTPError as exc:  # pragma: no cover - network dependent
            logger.warning("elasticsearch ensure_index failed: %s", exc)
            return False


async def index_job_documents(documents: Sequence[dict], settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    base_url = _base_url(settings)
    if not base_url or not documents:
        return

    await ensure_index(settings)
    payload_lines: list[str] = []
    for document in documents:
        job_id = document.get("job_id")
        if not job_id:
            continue
        payload_lines.append(f'{{"index": {{"_id": "{job_id}"}}}}')
        payload_lines.append(json.dumps(document, ensure_ascii=False))

    if not payload_lines:
        return

    bulk_body = "\n".join(payload_lines) + "\n"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{base_url}/_bulk",
                content=bulk_body,
                headers={"Content-Type": "application/x-ndjson"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network dependent
            logger.warning("elasticsearch bulk index failed: %s", exc)


async def search_job_ids(query: str, *, size: int = 250, settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    base_url = _base_url(settings)
    if not base_url or not query.strip():
        return []

    search_body = {
        "size": size,
        "_source": ["job_id"],
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^4", "company^3", "location^2", "remote_type", "description", "matched_keywords"],
                "fuzziness": "AUTO",
            }
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.post(f"{base_url}/{settings.elasticsearch_index}/_search", json=search_body)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:  # pragma: no cover - network dependent
            logger.warning("elasticsearch search failed: %s", exc)
            return []

    hits = payload.get("hits", {}).get("hits", [])
    ids: list[str] = []
    for hit in hits:
        source = hit.get("_source") or {}
        job_id = source.get("job_id") or hit.get("_id")
        if job_id:
            ids.append(str(job_id))
    return ids
