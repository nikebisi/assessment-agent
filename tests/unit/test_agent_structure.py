"""Unit tests verifying the InstaTrend multi-agent pipeline architecture and state callbacks."""

import pytest

from app.agent import (
    FAST_VISION_MODEL,
    GUARDRAIL_MODEL,
    STRATEGY_REASONING_MODEL,
    app,
    humanizer_guardrail,
    initialize_session_state,
    platform_strategist,
    root_agent,
    visual_analyst,
)


def test_multi_agent_pipeline_structure():
    """Verify that root_agent is a SequentialAgent with 3 specialized sub-agents."""
    assert root_agent.name == "insta_trend_pipeline"
    sub_names = [agent.name for agent in root_agent.sub_agents]
    assert sub_names == ["visual_analyst", "platform_strategist", "humanizer_guardrail"]


def test_sub_agent_models_and_tools():
    """Verify sub-agent models, instructions, and tool assignments."""
    # Agent 1: Visual Analyst
    assert visual_analyst.model.model == FAST_VISION_MODEL
    assert isinstance(visual_analyst.instruction, str)
    assert "Visual Trend Analyst" in visual_analyst.instruction
    assert visual_analyst.output_key == "visual_analysis"

    # Agent 2: Platform Strategist
    assert platform_strategist.model.model == STRATEGY_REASONING_MODEL
    assert isinstance(platform_strategist.instruction, str)
    assert "Platform Trend Strategist" in platform_strategist.instruction
    tool_names = [t.__name__ for t in platform_strategist.tools]
    assert "fetch_tiktok_trends" in tool_names
    assert "fetch_instagram_meme_formats" in tool_names
    assert "fetch_substack_narrative_hooks" in tool_names
    assert "search_user_vibe_history" in tool_names
    assert "save_vibe_memory" in tool_names
    assert platform_strategist.output_key == "draft_captions"

    # Agent 3: Humanizer Guardrail
    assert humanizer_guardrail.model.model == GUARDRAIL_MODEL
    guardrail_tools = [t.__name__ for t in humanizer_guardrail.tools]
    assert "scrub_ai_cliches" in guardrail_tools
    assert humanizer_guardrail.output_key == "final_polished_captions"


def test_app_compaction_and_cache_configuration():
    """Verify context compaction and caching are active on the App instance."""
    assert app.name == "app"
    assert app.root_agent is root_agent
    assert app.events_compaction_config is not None
    assert app.events_compaction_config.token_threshold == 16000
    assert app.events_compaction_config.event_retention_size == 5
    assert app.context_cache_config is not None
    assert app.context_cache_config.min_tokens == 2048


@pytest.mark.asyncio
async def test_initialize_session_state_callback():
    """Verify async state initialization sets default keys and preserves user profiles."""

    class MockContext:
        def __init__(self):
            self.state = {"user:vibe_profile": "chaotic office dread"}
            self.user_id = "test_user_123"

    mock_ctx = MockContext()
    await initialize_session_state(mock_ctx)

    assert mock_ctx.state["user_vibe_profile"] == "chaotic office dread"
    assert "visual_analysis" in mock_ctx.state
    assert "recalled_memories" in mock_ctx.state
    assert "user:saved_captions" in mock_ctx.state
