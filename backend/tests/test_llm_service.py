from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_resolve_llm_config_rejects_missing_user_context():
    service = LLMService(AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await service._resolve_llm_config_with_policy(None, require_api_key=True)

    assert exc_info.value.status_code == 400
    assert "默认 LLM 配置已禁用" in exc_info.value.detail


@pytest.mark.asyncio
async def test_resolve_llm_config_requires_complete_user_level_config():
    service = LLMService(AsyncMock())
    service.llm_repo = SimpleNamespace(
        get_by_user=AsyncMock(
            return_value=SimpleNamespace(
                llm_provider_url="https://api.example.com/v1",
                llm_provider_api_key="",
                llm_provider_model="",
            )
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await service._resolve_llm_config_with_policy(7, require_api_key=True)

    assert exc_info.value.status_code == 400
    assert "API Key" in exc_info.value.detail
    assert "Model" in exc_info.value.detail


@pytest.mark.asyncio
async def test_resolve_llm_config_returns_user_level_values():
    service = LLMService(AsyncMock())
    service.llm_repo = SimpleNamespace(
        get_by_user=AsyncMock(
            return_value=SimpleNamespace(
                llm_provider_url="https://api.example.com/v1",
                llm_provider_api_key="test-key",
                llm_provider_model="gpt-test",
            )
        )
    )

    config = await service._resolve_llm_config_with_policy(9, require_api_key=True)

    assert config == {
        "api_key": "test-key",
        "base_url": "https://api.example.com/v1",
        "model": "gpt-test",
    }
