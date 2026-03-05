# AIMETA P=更新日志API_系统更新记录|R=更新日志查询|NR=不含日志修改|E=route:GET_/api/updates/*|X=http|A=日志查询|D=fastapi,sqlalchemy|S=db|RD=./README.ai
from typing import Any, List, Optional
import re

import httpx

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...db.session import get_session
from ...schemas.admin import UpdateLogRead
from ...services.update_log_service import UpdateLogService

router = APIRouter(prefix="/api/updates", tags=["Updates"])


def get_update_log_service(session: AsyncSession = Depends(get_session)) -> UpdateLogService:
    return UpdateLogService(session)


def _normalize_version(raw_version: Optional[str]) -> Optional[str]:
    if not raw_version:
        return None
    normalized = raw_version.strip().removeprefix("v").strip()
    if (
        not normalized
        or len(normalized) > 64
        or re.search(r"[<>\s]", normalized)
        or not re.fullmatch(r"[\w.+-]+", normalized)
    ):
        return None
    return normalized


def _pick_version_from_payload(payload: Any) -> Optional[str]:
    if isinstance(payload, str):
        return _normalize_version(payload)
    if not isinstance(payload, dict):
        return None

    for key in ("version", "latest_version", "tag_name", "app_version"):
        candidate = payload.get(key)
        if isinstance(candidate, str):
            normalized = _normalize_version(candidate)
            if normalized:
                return normalized

    return None


async def _fetch_payload(url: str) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        if "application/json" in (response.headers.get("content-type") or ""):
            return response.json()
        return response.text


@router.get("/latest", response_model=List[UpdateLogRead])
async def read_latest_updates(
    service: UpdateLogService = Depends(get_update_log_service),
) -> List[UpdateLogRead]:
    logs = await service.list_logs(limit=5)
    return [UpdateLogRead.model_validate(log) for log in logs]


@router.get("/remote-version")
async def read_remote_version() -> dict[str, Any]:
    """从 GitHub 版本 JSON 获取远程版本（服务端代理，避免浏览器跨域问题）。"""
    sources: list[tuple[str, str, Any]] = []
    if settings.version_info_url:
        sources.append(("github_json", str(settings.version_info_url), _pick_version_from_payload))

    if settings.version_check_url:
        sources.append(("custom_url", str(settings.version_check_url), _pick_version_from_payload))

    errors: list[str] = []
    for source_name, source_url, parser in sources:
        try:
            payload = await _fetch_payload(source_url)
            version = parser(payload)
            if version:
                build_time_beijing = None
                if isinstance(payload, dict):
                    raw_build_time = payload.get("build_time_beijing")
                    if isinstance(raw_build_time, str) and raw_build_time.strip():
                        build_time_beijing = raw_build_time.strip()
                return {
                    "version": version,
                    "source": source_name,
                    "build_time_beijing": build_time_beijing,
                }
            errors.append(f"{source_name}: version not found")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source_name}: {type(exc).__name__}")

    return {
        "version": None,
        "source": None,
        "errors": errors,
    }
