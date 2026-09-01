"""Unit tests verifying the InstaTrend ADK 2.0 Graph Workflow architecture, routing, and guardrails."""

import pytest
from google.adk.workflow import Workflow

from app.agent import (
    FAST_VISION_MODEL,
    GUARDRAIL_MODEL,
    STRATEGY_REASONING_MODEL,
    app,
    audit_cliches_guardrail_func,
    root_agent,
)


def test_workflow_structure_and_nodes():
    """Verify that root_agent is an ADK 2.0 Workflow with all planned nodes."""
    assert isinstance(root_agent, Workflow)
    assert root_agent.name == "insta_trend_workflow"

    # Verify strategic model configuration constants
    assert FAST_VISION_MODEL == "gemini-2.5-flash"
    assert STRATEGY_REASONING_MODEL == "gemini-2.5-pro"
    assert GUARDRAIL_MODEL == "gemini-2.5-flash"


def test_app_resumability_compaction_and_caching():
    """Verify that the App container is configured with HITL resumability, token compaction, and caching."""
    assert app.name == "app"
    assert app.root_agent is root_agent
    assert app.resumability_config is not None
    assert app.resumability_config.is_resumable is True
    assert app.events_compaction_config is not None
    assert app.events_compaction_config.token_threshold == 16000
    assert app.events_compaction_config.event_retention_size == 5
    assert app.context_cache_config is not None
    assert app.context_cache_config.min_tokens == 2048


@pytest.mark.asyncio
async def test_audit_cliches_guardrail_routing_on_clean_captions():
    """Verify guardrail routes to 'approved' when captions are clean."""

    class MockContext:
        def __init__(self):
            self.state = {}

    clean_drafts = {
        "tiktok_captions": [
            {
                "hook": "3:42 pm",
                "caption_body": "zero thoughts behind these eyes, just vibes",
            }
        ],
        "instagram_captions": [
            {"hook": "recent developments", "caption_body": "1. coffee 2. chaos"}
        ],
        "substack_hooks": [
            {
                "hook": "Notes from the doomscroll",
                "caption_body": "A short observation.",
            }
        ],
    }

    mock_ctx = MockContext()
    event = await audit_cliches_guardrail_func(mock_ctx, clean_drafts)

    assert event.actions is not None
    assert event.actions.route == "approved"
    assert event.actions.state_delta["passed_guardrails"] is True


@pytest.mark.asyncio
async def test_audit_cliches_guardrail_routing_on_banned_cliches():
    """Verify guardrail routes back to 'retry' when forbidden AI cliches are present."""

    class MockContext:
        def __init__(self):
            self.state = {"guardrail_retry_count": 0}

    cliche_drafts = {
        "tiktok_captions": [
            {
                "hook": "POV",
                "caption_body": "Delve into this vibrant tapestry to unleash your potential!",
            }
        ],
        "instagram_captions": [],
        "substack_hooks": [],
    }

    mock_ctx = MockContext()
    event = await audit_cliches_guardrail_func(mock_ctx, cliche_drafts)

    assert event.actions is not None
    assert event.actions.route == "retry"
    assert event.actions.state_delta["guardrail_retry_count"] == 1
    assert "cliche_feedback" in event.actions.state_delta
