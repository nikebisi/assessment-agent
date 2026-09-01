"""Unit tests for InstaTrend Agent custom tools."""

from app.tools import (
    fetch_instagram_meme_formats,
    fetch_substack_narrative_hooks,
    fetch_tiktok_trends,
    scrub_ai_cliches,
)


def test_fetch_tiktok_trends_valid():
    """Verify fetch_tiktok_trends returns expected structured trends."""
    res = fetch_tiktok_trends(category="corporate", tone="ironic")
    assert res["status"] == "success"
    assert res["category"] == "corporate"
    assert len(res["trends"]) > 0
    assert "format_name" in res["trends"][0]
    assert "example" in res["trends"][0]


def test_fetch_tiktok_trends_fallback():
    """Verify fallback behavior and recovery guidance for unrecognized category."""
    res = fetch_tiktok_trends(category="unknown_category_xyz", tone="deadpan")
    assert res["status"] == "success"
    assert res["category"] == "general"
    assert res["recovery_guidance"] is not None
    assert "Valid categories" in res["recovery_guidance"]


def test_fetch_instagram_meme_formats_valid():
    """Verify fetch_instagram_meme_formats returns formats and hashtags."""
    res = fetch_instagram_meme_formats(
        post_type="carousel_dump", vibe="corporate dread"
    )
    assert res["status"] == "success"
    assert res["post_type"] == "carousel_dump"
    assert len(res["formats"]) > 0
    assert len(res["recommended_hashtags"]) > 0
    assert any("corporate" in tag for tag in res["recommended_hashtags"])


def test_fetch_substack_narrative_hooks_valid():
    """Verify fetch_substack_narrative_hooks returns essay hooks."""
    res = fetch_substack_narrative_hooks(
        theme="cultural_commentary", wit_level="deadpan"
    )
    assert res["status"] == "success"
    assert len(res["hooks"]) > 0
    assert "hook_headline" in res["hooks"][0]
    assert "opening_sentence" in res["hooks"][0]


def test_scrub_ai_cliches_detects_banned_phrases():
    """Verify scrub_ai_cliches detects and calculates severity for AI cliches."""
    bad_caption = (
        "Delve into this vibrant tapestry to unleash your inner creative genius!"
    )
    res = scrub_ai_cliches(bad_caption)
    assert res["is_clean"] is False
    assert "delve into" in res["detected_cliches"]
    assert "vibrant tapestry" in res["detected_cliches"]
    assert "unleash your inner" in res["detected_cliches"]
    assert res["severity_score"] >= 9
    assert res["recovery_guidance"] is not None


def test_scrub_ai_cliches_passes_human_caption():
    """Verify scrub_ai_cliches passes authentic human creator phrasing."""
    human_caption = "3:42 pm. zero thoughts behind these eyes, just vibes."
    res = scrub_ai_cliches(human_caption)
    assert res["is_clean"] is True
    assert len(res["detected_cliches"]) == 0
    assert res["severity_score"] == 0
    assert res["recovery_guidance"] is None


def test_scrub_ai_cliches_empty_string():
    """Verify graceful handling of empty text input."""
    res = scrub_ai_cliches("")
    assert res["is_clean"] is True
    assert res["severity_score"] == 0
