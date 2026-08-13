import asyncio

import pytest

from app.api import endpoints


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_execute_workflow_times_out(monkeypatch):
    async def stalled_execute(**_kwargs):
        await asyncio.sleep(1)

    monkeypatch.setattr(endpoints, "WORKFLOW_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(endpoints.workflow_executor, "execute", stalled_execute)

    request = endpoints.ChatStreamRequest(
        message="hello",
        conversation_id="conversation-1",
        user_id="user-1",
    )

    with pytest.raises(asyncio.TimeoutError):
        await endpoints._execute_workflow(request, {})
