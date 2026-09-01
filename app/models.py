"""Pydantic data models and schemas for InstaTrend Agent."""

from typing import Literal

from pydantic import BaseModel, Field

# ==========================================
# Tool Input Request Schemas
# ==========================================


class TikTokTrendsRequest(BaseModel):
    """Input parameters for fetch_tiktok_trends tool."""

    category: str = Field(
        default="general",
        description="Content category to match (e.g. 'corporate', 'lifestyle', 'food', 'dating', 'general').",
    )
    tone: Literal[
        "ironic", "unhinged", "wholesome", "storytime", "relatable", "deadpan"
    ] = Field(
        default="ironic",
        description="The comedic tone of the TikTok meme structure.",
    )


class InstagramMemeRequest(BaseModel):
    """Input parameters for fetch_instagram_meme_formats tool."""

    post_type: Literal["carousel_dump", "single_photo", "reel", "story"] = Field(
        default="carousel_dump",
        description="The Instagram post format (e.g. 'carousel_dump', 'single_photo', 'reel', 'story').",
    )
    vibe: str = Field(
        default="casual",
        description="The visual aesthetic or theme (e.g. 'euro summer', 'corporate dread', 'chaotic cooking').",
    )


class SubstackHooksRequest(BaseModel):
    """Input parameters for fetch_substack_narrative_hooks tool."""

    theme: str = Field(
        default="cultural_commentary",
        description="Core thematic topic (e.g. 'cultural_commentary', 'digital_burnout', 'daily_absurdity').",
    )
    wit_level: Literal["deadpan", "subtle", "scathing", "reflective"] = Field(
        default="deadpan",
        description="Desired humor tone for the essay hook.",
    )


class ScrubAiClichesRequest(BaseModel):
    """Input parameters for scrub_ai_cliches tool."""

    caption_text: str = Field(
        description="The raw caption or hook text to be audited for AI clichés and robotic cadence.",
    )


# ==========================================
# Tool Output Schemas & Entities
# ==========================================


class TikTokTrendItem(BaseModel):
    """Represents a single viral TikTok meme structure or audio trend."""

    format_name: str = Field(
        description="Name of the TikTok meme format or trend structure."
    )
    sound_or_trope: str = Field(
        description="Associated audio cue, meme premise, or sound vibe."
    )
    structure_template: str = Field(
        description="Caption/overlay template with placeholders."
    )
    humor_style: str = Field(
        description="Style of humor (e.g. 'deadpan POV', 'chaotic unhinged', 'relatable dread')."
    )
    example: str = Field(
        description="Fully realized example caption using this format."
    )


class TikTokTrendResponse(BaseModel):
    """Response returned by fetch_tiktok_trends tool."""

    status: Literal["success", "error"] = Field(
        description="Execution status of the tool."
    )
    category: str = Field(description="Category requested or defaulted to.")
    tone: str = Field(description="Comedic tone selected.")
    trends: list[TikTokTrendItem] = Field(
        default_factory=list,
        description="List of matching viral TikTok trend formats.",
    )
    recovery_guidance: str | None = Field(
        default=None,
        description="Actionable guidance for the LLM if parameters need adjustment or errors occurred.",
    )


class InstagramMemeFormatItem(BaseModel):
    """Represents a viral Instagram photo dump / reel caption template."""

    format_name: str = Field(description="Name of the Instagram format.")
    hook_style: str = Field(
        description="Style of the opening hook (e.g. 'one-liner understatement', 'carousel tease')."
    )
    caption_structure: str = Field(description="Structural blueprint of the caption.")
    visual_pairing_advice: str = Field(
        description="How to pair this caption with photo angles or carousel order."
    )
    example: str = Field(description="Fully realized example caption.")


class InstagramMemeResponse(BaseModel):
    """Response returned by fetch_instagram_meme_formats tool."""

    status: Literal["success", "error"] = Field(
        description="Execution status of the tool."
    )
    post_type: str = Field(description="Post format requested.")
    vibe: str = Field(description="Aesthetic vibe matched.")
    formats: list[InstagramMemeFormatItem] = Field(
        default_factory=list,
        description="Matching Instagram meme formats.",
    )
    recommended_hashtags: list[str] = Field(
        default_factory=list,
        description="Niche, non-cringe community hashtags.",
    )
    recovery_guidance: str | None = Field(
        default=None,
        description="Recovery instructions for error handling.",
    )


class SubstackHookItem(BaseModel):
    """Represents a Substack essayist hook or cultural commentary one-liner."""

    hook_headline: str = Field(description="Newsletter subject line or headline.")
    opening_sentence: str = Field(
        description="First sentence designed to stop scrolling."
    )
    narrative_angle: str = Field(
        description="The essayist angle (e.g. 'existential reflection', 'satirical zeitgeist')."
    )
    wit_tone: str = Field(description="The intellectual wit tone.")
    example_expansion: str = Field(
        description="Short 2-3 sentence paragraph illustrating the rhythm."
    )


class SubstackHookResponse(BaseModel):
    """Response returned by fetch_substack_narrative_hooks tool."""

    status: Literal["success", "error"] = Field(
        description="Execution status of the tool."
    )
    theme: str = Field(description="Intellectual or cultural theme matched.")
    wit_level: str = Field(description="Wit level requested.")
    hooks: list[SubstackHookItem] = Field(
        default_factory=list,
        description="List of Substack essayist hooks.",
    )
    recovery_guidance: str | None = Field(
        default=None,
        description="Recovery guidance if theme is too broad or narrow.",
    )


class ScrubResult(BaseModel):
    """Response returned by scrub_ai_cliches tool."""

    status: Literal["success", "error"] = Field(
        description="Execution status of the tool."
    )
    is_clean: bool = Field(
        description="True if no blacklisted AI clichés or robotic cadences were found."
    )
    detected_cliches: list[str] = Field(
        default_factory=list,
        description="List of exact cliché phrases detected.",
    )
    severity_score: int = Field(
        default=0,
        description="Cringe/Robotic severity score from 0 (completely human) to 10 (blatantly AI).",
    )
    cleaned_text: str = Field(
        description="Cleaned version with robotic markers stripped and punctuation humanized.",
    )
    critique: str = Field(
        description="Constructive feedback explaining what made the phrasing sound artificial.",
    )
    recovery_guidance: str | None = Field(
        default=None,
        description="Instructions on how to rewrite the caption if cliches were detected.",
    )


# ==========================================
# Agent Node State & Transfer Schemas
# ==========================================


class VisualAnalysisResult(BaseModel):
    """Structured output from Agent 1: Visual Trend Analyst."""

    focal_elements: list[str] = Field(
        default_factory=list,
        description="Key visual elements and subjects identified in the image or description.",
    )
    detected_emotions: list[str] = Field(
        default_factory=list,
        description="Micro-expressions and emotional nuances detected (e.g. 'dissociative smile', 'corporate panic').",
    )
    aesthetic_vibe: str = Field(
        default="casual",
        description="The aesthetic archetype or cultural vibe (e.g. 'clean girl irony', 'rat girl summer', 'chaotic burnout').",
    )
    visual_irony_or_contrast: str = Field(
        default="",
        description="The comic tension or contrast between foreground/background or appearance/reality.",
    )
    cultural_archetypes: list[str] = Field(
        default_factory=list,
        description="Relevant internet subculture archetypes related to the scene.",
    )
    summary_for_strategist: str = Field(
        default="",
        description="Concise synthesis explaining why this visual is comedic or relatable.",
    )


class CaptionDraftItem(BaseModel):
    """A draft caption item for a specific platform and style."""

    platform: Literal["tiktok", "instagram", "substack"] = Field(
        description="Target social media platform."
    )
    style_variant: str = Field(
        description="The comedic angle, e.g. 'self_deprecating', 'hyper_relatable', 'deadpan_irony'."
    )
    hook: str = Field(description="The text overlay or opening hook.")
    caption_body: str = Field(description="The full caption text.")
    hashtags: list[str] = Field(
        default_factory=list, description="Associated hashtags."
    )


class PlatformDraftCaptions(BaseModel):
    """Output from Agent 2: Platform Trend Strategist."""

    tiktok_captions: list[CaptionDraftItem] = Field(
        default_factory=list,
        description="3 distinct TikTok caption options.",
    )
    instagram_captions: list[CaptionDraftItem] = Field(
        default_factory=list,
        description="3 distinct Instagram caption options.",
    )
    substack_hooks: list[CaptionDraftItem] = Field(
        default_factory=list,
        description="3 distinct Substack essay hooks.",
    )
    strategy_rationale: str = Field(
        default="",
        description="Explanation of why these captions match the visual contrast and current culture.",
    )


class FinalPolishedCaptions(BaseModel):
    """Final output from Agent 3: Humanizer & Polish Guardrail."""

    tiktok_captions: list[str] = Field(
        default_factory=list,
        description="Polished, human-grade TikTok captions ready to copy.",
    )
    instagram_captions: list[str] = Field(
        default_factory=list,
        description="Polished, human-grade Instagram captions ready to copy.",
    )
    substack_hooks: list[str] = Field(
        default_factory=list,
        description="Polished, human-grade Substack essay hooks ready to copy.",
    )
    authenticity_notes: str = Field(
        default="",
        description="Guardrail verification notes confirming zero AI clichés.",
    )
    passed_guardrails: bool = Field(
        default=True,
        description="Whether all generated options passed anti-cliché scrub validation.",
    )
