# IMPLEMENTATION PLAN: Culture-Aware Meme & Viral Caption Agent (InstaTrend)

## Overview & Architecture Highlights
This implementation plan defines the step-by-step roadmap for building, testing, and evaluating the **Culture-Aware Meme & Viral Caption Agent** (InstaTrend Agent) using Google ADK 2.0 and Gemini models (`gemini-2.5-flash` and `gemini-2.5-pro`).

---

## Phase 1: Project Scaffolding & Dependency Setup
- **Goal**: Initialize the project structure using `agents-cli scaffold enhance .` with standard ADK conventions.
- **Key Actions**:
  1. Enhance workspace structure with `agents-cli scaffold enhance .` targeting prototype/Cloud Run.
  2. Configure `pyproject.toml` with dependencies:
     - `google-adk>=2.0.0`
     - `google-genai`
     - `pydantic>=2.0.0`
     - `opentelemetry-api`, `opentelemetry-sdk`
     - `pytest`, `pytest-asyncio`
  3. Validate environment configuration template (`.env.example` and `.env`) supporting both Vertex AI (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`) and Google AI Studio (`GEMINI_API_KEY`).

---

## Phase 2: Domain Schemas & Data Contracts (`app/models.py`)
- **Goal**: Define immutable Pydantic models for cross-agent communication and tool interfaces.
- **Key Artifacts**:
  1. `VisualAnalysisResult`:
     - `focal_elements: list[str]`
     - `detected_emotions: list[str]`
     - `aesthetic_vibe: str`
     - `visual_irony_or_contrast: str`
     - `cultural_archetypes: list[str]`
  2. `PlatformTrendItem` & `PlatformTrendCollection`:
     - Platform metadata (TikTok / Instagram / Substack), trending hooks, sound tropes, humor style, examples.
  3. `DraftCaption` & `PlatformDraftCaptions`:
     - `platform: Literal["tiktok", "instagram", "substack"]`
     - `angle: str` (e.g. "self_deprecating", "hyper_relatable", "intellectual_dread")
     - `hook: str`
     - `caption_body: str`
     - `recommended_format: str`
  4. `FinalPolishedCaptions`:
     - Polished multi-platform captions, critique notes, and authenticity verification stamp.

---

## Phase 3: Culture & Trend Toolset Implementation (`app/tools.py`)
- **Goal**: Build robust, typed Python tool functions with Google docstrings and guided error handling.
- **Key Tools**:
  1. `fetch_tiktok_trends`:
     - Queries TikTok cultural tropes (e.g., POV formats, auditory ironies, comment-section slang).
     - Returns `TikTokTrendResponse`.
  2. `fetch_instagram_meme_formats`:
     - Queries carousel hooks, photo dump captions, aesthetic irony structures, and story replies.
     - Returns `InstagramMemeResponse`.
  3. `fetch_substack_narrative_hooks`:
     - Queries essay opening hooks, cultural commentary one-liners, and newsletter titling tropes.
     - Returns `SubstackHookResponse`.
  4. `scrub_ai_cliches`:
     - Deterministic lexical scanner and heuristic cleaner targeting forbidden AI vocabulary (*"delve into", "tapestry", "unleash", "elevate", "testament"*, em-dash abuse, robotic promotional cadence).
     - Returns `ScrubResult` with `is_clean: bool`, `detected_cliches: list[str]`, and `cleaned_text: str`.
  5. Unified Error Boundary:
     - Wrap all tool executions in try/except blocks returning structured error recovery hints rather than throwing unhandled exceptions.

---

## Phase 4: System Constitution & Platform Prompts (`app/prompts.py`)
- **Goal**: Formulate non-negotiable prompt instructions enforcing human authenticity, comedic timing, and zero robotic cliché tolerance.
- **Key Artifacts**:
  1. `SYSTEM_CONSTITUTION`:
     - Core identity as internet-native comedy writer / social strategist.
     - Hard prohibitions against corporate phrasing, superficial enthusiasm, and generic AI structures.
  2. `VISUAL_ANALYST_INSTRUCTION`:
     - Instructions for parsing image semantics, tension, contrast, and subtle human micro-expressions.
  3. `PLATFORM_STRATEGIST_INSTRUCTION`:
     - Deep synthesis instructions mapping visual cues to TikTok, Instagram, and Substack humor conventions.
  4. `HUMANIZER_GUARDRAIL_INSTRUCTION`:
     - Polish and de-cringe instructions, ensuring natural punctuation, lowercasing conventions, and conversational punchlines.

---

## Phase 5: Multi-Agent Workflow Engine (`app/agent.py`)
- **Goal**: Construct the ADK 2.0 Graph Workflow orchestrating the 3 sub-agents.
- **Key Components**:
  1. **Visual Trend Analyst Agent** (`gemini-2.5-flash`):
     - Processes image/multimodal description and emits structured `VisualAnalysisResult`.
  2. **Platform Trend Strategist Agent** (`gemini-2.5-pro`):
     - Equipped with trend tools (`fetch_tiktok_trends`, `fetch_instagram_meme_formats`, `fetch_substack_narrative_hooks`).
     - Synthesizes visual analysis into platform-tailored drafts.
  3. **Humanizer & Polish Guardrail Agent** (`gemini-2.5-flash`):
     - Equipped with `scrub_ai_cliches`.
     - Validates drafts, strips lingering AI markers, and formats final output.
  4. **Graph Workflow (`google.adk.workflow.Workflow`)**:
     - Sequential edge wiring: `('START', visual_analyst) -> (visual_analyst, trend_strategist) -> (trend_strategist, humanizer_guardrail) -> (humanizer_guardrail, output_formatter)`.
  5. **App Configuration (`google.adk.apps.App`)**:
     - `name="app"` (strictly aligned with agent directory).
     - `events_compaction_config`: Token threshold (16,000) with `LlmEventSummarizer`.
     - `context_cache_config`: Context caching for prompts (TTL 1800s).

---

## Phase 6: Observability & Structured JSON Telemetry (`app/observability.py`)
- **Goal**: Implement zero-raw-print structured logging and OpenTelemetry instrumentation.
- **Key Components**:
  1. `StructuredObservabilityPlugin` (ADK BasePlugin):
     - Logs structured JSON before/after agent invocation.
     - Logs structured JSON before/after tool execution.
     - Records **Intent vs. Outcome** pair for each cognitive step.
  2. OpenTelemetry span creation and context propagation linking trace IDs and span IDs.

---

## Phase 7: Evaluation Suite & Quality Flywheel (`tests/eval/`)
- **Goal**: Author comprehensive evaluation datasets and configuration adhering to the Agent Platform evaluation rubric.
- **Key Artifacts**:
  1. `tests/eval/eval_config.yaml`:
     - Configured with `multi_turn_task_success`, `multi_turn_trajectory_quality`.
     - Custom LLM-as-judge metric: `human_authenticity_and_humor_score` (rates wit, natural cadence, and platform appropriateness).
     - Custom deterministic code metric: `banned_cliche_detector` (fails if blacklisted words appear).
  2. `tests/eval/datasets/golden_captions.json`:
     - Test cases spanning 5 core scenario domains (Corporate burnout, Aesthetic vacation dump, Chaotic pet/cooking mishap, Fitness/routine irony, Substack cultural commentary).
  3. Eval Execution:
     - Run `agents-cli eval run` and analyze metrics in `artifacts/grade_results/`.

---

## Phase 8: Unit & Integration Testing (`tests/unit/`, `tests/integration/`)
- **Goal**: Deterministic test coverage verifying code correctness without relying on non-deterministic LLM pytest assertions.
- **Key Tests**:
  1. `tests/unit/test_tools.py`: Unit tests for `scrub_ai_cliches`, `fetch_tiktok_trends`, `fetch_instagram_meme_formats`, and `fetch_substack_narrative_hooks`.
  2. `tests/unit/test_models.py`: Schema validation tests for Pydantic data models.
  3. `tests/integration/test_workflow_graph.py`: Graph topology verification ensuring all nodes and edges validate without cycles or unbound inputs.

---

## Phase 9: Verification & Quality Approval
- **Goal**: End-to-end smoke testing with `agents-cli run` and evaluation benchmarking with `agents-cli eval run`.
- **Validation Criteria**:
  - `agents-cli run` successfully generates 3 platform-tailored authentic captions for sample inputs.
  - `agents-cli eval run` achieves passing thresholds on task success and human authenticity.
  - Structured JSON logs capture intent vs. outcome across all turns.
