"""Culture-Aware Meme & Viral Caption Agent (InstaTrend Agent).

Implements a multi-agent sequential pipeline with:
- Visual Trend Analyst (gemini-2.5-flash)
- Platform Trend Strategist (gemini-2.5-pro)
- Humanizer & Polish Guardrail (gemini-2.5-flash)
With asynchronous memory operations, vector memory integration,
token-based history compaction, and context caching.
"""

from __future__ import annotations

import logging

from google.adk.agents import Agent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini
from google.genai import types

from app.prompts import (
    HUMANIZER_GUARDRAIL_INSTRUCTION,
    PLATFORM_STRATEGIST_INSTRUCTION,
    SYSTEM_CONSTITUTION,
    VISUAL_ANALYST_INSTRUCTION,
)
from app.tools import (
    fetch_instagram_meme_formats,
    fetch_substack_narrative_hooks,
    fetch_tiktok_trends,
    save_vibe_memory,
    scrub_ai_cliches,
    search_user_vibe_history,
)

logger = logging.getLogger("instatrend.agent")

# Models for cognitive separation of concerns
FAST_VISION_MODEL = "gemini-2.5-flash"
STRATEGY_REASONING_MODEL = "gemini-2.5-pro"
GUARDRAIL_MODEL = "gemini-2.5-flash"


# =====================================================================
# Asynchronous State & Memory Callbacks
# =====================================================================


async def initialize_session_state(callback_context: CallbackContext) -> None:
    """Asynchronously initializes session and user state variables to prevent KeyError crashes.

    Args:
        callback_context: ADK execution context containing state and session metadata.
    """
    state = callback_context.state

    # Initialize default state keys for prompt template interpolation
    if "user_vibe_profile" not in state:
        state["user_vibe_profile"] = state.get(
            "user:vibe_profile", "authentic, witty, self-aware creator"
        )

    if "visual_analysis" not in state:
        state["visual_analysis"] = "No prior visual analysis recorded."

    if "recalled_memories" not in state:
        state["recalled_memories"] = "[]"

    if "user:saved_captions" not in state:
        state["user:saved_captions"] = []

    logger.info(
        "Session state initialized asynchronously for user_id=%s",
        getattr(callback_context, "user_id", "default"),
    )


async def sync_memory_bank_callback(
    callback_context: CallbackContext,
) -> types.Content | None:
    """Asynchronously persists completed session events to long-term memory.

    Args:
        callback_context: ADK execution context.

    Returns:
        None to proceed with normal event propagation.
    """
    try:
        if hasattr(callback_context, "add_session_to_memory"):
            await callback_context.add_session_to_memory()
            logger.info("Session events asynchronously synchronized to Memory Bank.")
    except Exception as e:
        logger.warning("Memory bank async synchronization skipped: %s", e)
    return None


async def compact_session_history(callback_context: CallbackContext) -> None:
    """Asynchronously compacts old turn state to prevent context bloat across long sessions."""
    state = callback_context.state
    if "temp:history_turns" in state and len(state["temp:history_turns"]) > 10:
        # Keep only the last 5 turns in immediate state
        state["temp:history_turns"] = state["temp:history_turns"][-5:]
        logger.info("Session history state window compacted.")


# =====================================================================
# Specialized Sub-Agent Definitions
# =====================================================================

# 1. Visual Trend Analyst: Rapid image perception, micro-expressions, and aesthetic archetype extraction
visual_analyst = Agent(
    name="visual_analyst",
    model=Gemini(
        model=FAST_VISION_MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=f"{SYSTEM_CONSTITUTION}\n\n{VISUAL_ANALYST_INSTRUCTION}",
    description="Analyzes image inputs, visual descriptions, micro-expressions, aesthetic archetypes, and ironic visual contrast.",
    output_key="visual_analysis",
)

# 2. Platform Trend Strategist: Deep reasoning, live cultural trend queries, and viral humor synthesis
platform_strategist = Agent(
    name="platform_strategist",
    model=Gemini(
        model=STRATEGY_REASONING_MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=f"{SYSTEM_CONSTITUTION}\n\n{PLATFORM_STRATEGIST_INSTRUCTION}",
    description="Synthesizes visual cues with real-time cultural meme formats and viral slang across TikTok, Instagram, and Substack.",
    tools=[
        fetch_tiktok_trends,
        fetch_instagram_meme_formats,
        fetch_substack_narrative_hooks,
        search_user_vibe_history,
        save_vibe_memory,
    ],
    output_key="draft_captions",
)

# 3. Humanizer & Polish Guardrail: Anti-cliché scrub audit, de-cringe filtering, and final creator formatting
humanizer_guardrail = Agent(
    name="humanizer_guardrail",
    model=Gemini(
        model=GUARDRAIL_MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=f"{SYSTEM_CONSTITUTION}\n\n{HUMANIZER_GUARDRAIL_INSTRUCTION}\n\nDraft captions to audit: {{draft_captions}}",
    description="Audits and humanizes draft captions using deterministic cliché scrubbing to guarantee authentic creator voice.",
    tools=[scrub_ai_cliches],
    output_key="final_polished_captions",
)


# =====================================================================
# Root Multi-Agent Orchestrator
# =====================================================================

root_agent = SequentialAgent(
    name="insta_trend_pipeline",
    sub_agents=[visual_analyst, platform_strategist, humanizer_guardrail],
    description="Sequential multi-agent pipeline generating culture-aware viral captions and meme hooks.",
    before_agent_callback=initialize_session_state,
    after_agent_callback=sync_memory_bank_callback,
)


# =====================================================================
# Application Configuration: Compaction, Caching & Session Management
# =====================================================================

# Token-based sliding window history compaction with LLM event summarizer
compaction_config = EventsCompactionConfig(
    token_threshold=16000,
    event_retention_size=5,
    summarizer=LlmEventSummarizer(llm=Gemini(model=FAST_VISION_MODEL)),
)

# Context caching for immutable constitution and meme database
cache_config = ContextCacheConfig(
    min_tokens=2048,
    ttl_seconds=1800,
    cache_intervals=5,
)

app = App(
    name="app",
    root_agent=root_agent,
    events_compaction_config=compaction_config,
    context_cache_config=cache_config,
)
