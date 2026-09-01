"""Custom Toolset for InstaTrend Agent.

Provides culture-aware meme format retrieval, viral hook synthesis,
and deterministic AI-cliché scrubbing guardrails.
"""

import re
from typing import Any

from google.adk.tools import ToolContext

from app.models import (
    InstagramMemeFormatItem,
    InstagramMemeResponse,
    ScrubResult,
    SubstackHookItem,
    SubstackHookResponse,
    TikTokTrendItem,
    TikTokTrendResponse,
)
from app.observability import log_intent, log_outcome

# Comprehensive catalog of banned AI-generated clichés and robotic cadences
BANNED_AI_CLICHES: list[str] = [
    "delve into",
    "delve deeper",
    "delving into",
    "unleash your inner",
    "unleashing your",
    "in a world where",
    "elevate your",
    "elevating your",
    "testament to",
    "testament of",
    "look no further",
    "game changer",
    "game-changer",
    "vibrant tapestry",
    "rich tapestry",
    "tapestry of",
    "nestled in",
    "nestled between",
    "embark on",
    "embarking on",
    "supercharge your",
    "seamlessly blends",
    "seamless blend",
    "symphony of",
    "beacon of",
    "captivating",
    "culinary journey",
    "not just a",
    "it's not just",
    "journey begins",
    "masterpiece of",
    "bustling streets",
    "whispers of",
    "unmatched elegance",
    "pure bliss",
    "hidden gem",
]

# TikTok meme repository indexed by topic and tone
TIKTOK_TREND_DATABASE: dict[str, list[dict[str, str]]] = {
    "corporate": [
        {
            "format_name": "Sent from my iPhone at 4:58 PM",
            "sound_or_trope": "Distorted elevator music / corporate Teams notification chime",
            "structure_template": "POV: you closed your laptop at 4:59 PM and immediately entered a state of catatonic dissociation.",
            "humor_style": "corporate burnout dread",
            "example": "the way 'per my last email' actually translates to 'i am staring directly into the sun'.",
        },
        {
            "format_name": "Corporate Speak vs Internal Monologue",
            "sound_or_trope": "Aggressive typing followed by dead silence",
            "structure_template": "What I said in the quarterly sync: '{corporate_phrase}' vs what my soul was doing: '{unhinged_truth}'.",
            "humor_style": "satirical workplace irony",
            "example": "What I typed: 'Circling back!' vs What I meant: 'I have aged 14 lunar cycles since Monday.'",
        },
    ],
    "lifestyle": [
        {
            "format_name": "The Romanticize Everything Delusion",
            "sound_or_trope": "Lana Del Rey slow reverb audio",
            "structure_template": "pretending my $9 iced oat latte and crippling indecision is a cinematic aesthetic.",
            "humor_style": "self-deprecating aesthetic irony",
            "example": "romanticizing my morning routine as if i didn't hit snooze 6 times and sprint for the bus in mismatched socks.",
        },
        {
            "format_name": "Girl Dinner / Boy Lunch Reality",
            "sound_or_trope": "Cheery 1950s jingle with discordant finish",
            "structure_template": "3 pickles, a spoonful of peanut butter, and a dream.",
            "humor_style": "hyper-relatable chaotic dining",
            "example": "my nutritionist watching me call 4 saltines and a cold cold-brew 'a balanced Mediterranean lunch'.",
        },
    ],
    "food": [
        {
            "format_name": "Culinary Chaos / Chef Delusion",
            "sound_or_trope": "Ratatouille theme on a kazoo",
            "structure_template": "watching a 45-second cooking reel vs the crime scene currently in my kitchen.",
            "humor_style": "cooking expectation vs reality",
            "example": "the recipe said 'prep time 10 mins' but didn't account for the 40 minutes i spent negotiating with a stubborn shallot.",
        }
    ],
    "dating": [
        {
            "format_name": "Red Flag Collector",
            "sound_or_trope": "Circus music crescendo",
            "structure_template": "He's a 10 but {bizarre_specific_habit}.",
            "humor_style": "modern dating absurdism",
            "example": "he's a 10 but he types 'haha' with zero facial emotion while staring dead into your eyes.",
        }
    ],
    "general": [
        {
            "format_name": "Dissociative Stare POV",
            "sound_or_trope": "Muffled underwater synth bass",
            "structure_template": "POV: you're physically present at {event} but spiritually you are on a distant asteroid.",
            "humor_style": "deadpan dissociation",
            "example": "nodding politely in the group chat while having an out-of-body realization about the passage of time.",
        }
    ],
}

# Instagram meme and photo dump formats
INSTAGRAM_MEME_DATABASE: dict[str, list[dict[str, str]]] = {
    "carousel_dump": [
        {
            "format_name": "The Chaotic Understated Photo Dump",
            "hook_style": "dry deadpan one-liner",
            "caption_structure": "{dry_lower_case_sentence} + slide breakdown indicator (e.g., 'slide 4 is a warning').",
            "visual_pairing_advice": "Put the aesthetic hero image on slide 1, followed immediately by an unhinged blurry receipt or pet zoom on slide 2.",
            "example": "recent developments. slide 3 is legally binding and slide 7 was uncalled for.",
        },
        {
            "format_name": "Micro-Journal of Minor Inconveniences",
            "hook_style": "bulleted aesthetic summary",
            "caption_structure": "1. {aesthetic_item} 2. {chaotic_item} 3. {unrelated_existential_fact}.",
            "visual_pairing_advice": "Alternate between high-contrast daylight photos and grainy flash photography.",
            "example": "1. good coffee 2. questionable life choices 3. an apology to the barista.",
        },
    ],
    "single_photo": [
        {
            "format_name": "The Visual Irony Contrast",
            "hook_style": "extreme understatement",
            "caption_structure": "Treat an elaborate, dramatic visual with casual indifference.",
            "visual_pairing_advice": "Use when the subject looks intensely posed or the background has unintended comedy.",
            "example": "didn't cry once today (the day is not over).",
        },
        {
            "format_name": "Hyper-Specific Time Stamp",
            "hook_style": "chronological snapshot",
            "caption_structure": "{exact_time_and_ambient_vibe}.",
            "visual_pairing_advice": "Perfect for candid, slightly off-center golden hour shots.",
            "example": "3:42 pm. zero thoughts behind these eyes, just vibes.",
        },
    ],
    "reel": [
        {
            "format_name": "Relatable Problem Statement",
            "hook_style": "curiosity gap text overlay",
            "caption_structure": "Text on screen: '{hook}' | Caption: '{witty_punchline_and_community_question}'.",
            "visual_pairing_advice": "Opening 1.5 seconds must feature abrupt movement or dramatic eye contact.",
            "example": "never let them know your next move (i don't even know my current move).",
        }
    ],
}

# Substack hooks indexed by essay theme
SUBSTACK_HOOK_DATABASE: dict[str, list[dict[str, str]]] = {
    "cultural_commentary": [
        {
            "hook_headline": "On the unbearable performance of being 'well-adjusted'",
            "opening_sentence": "We have reached the point in late capitalism where even our hobbies require key performance indicators.",
            "narrative_angle": "societal exhaustion disguised as self-care",
            "wit_tone": "incisive, wry, intellectualized dread",
            "example_expansion": "I bought a ceramic mug last Tuesday with the explicit goal of slowing down. By Wednesday morning, I was optimizing my caffeine absorption curve.",
        },
        {
            "hook_headline": "The curation paradox: why we stopped having fun on camera",
            "opening_sentence": "Nobody simply exists in a room anymore; we are all staging ambient documentaries of our own lives.",
            "narrative_angle": "critique of aestheticized authenticity",
            "wit_tone": "deadpan cultural sociology",
            "example_expansion": "The camera eats first, then the lighting is audited, and finally the lukewarm remains of reality are consumed in silence.",
        },
    ],
    "digital_burnout": [
        {
            "hook_headline": "Notes from the doomscroll: a field guide to chronic online existence",
            "opening_sentence": "My screen time report arrived this Sunday formatted like an indictment from the Hague.",
            "narrative_angle": "technological absurdity and personal complicity",
            "wit_tone": "dark comedy with literary cadence",
            "example_expansion": "Seven hours and forty-two minutes of watching teenagers explain macroeconomics using iced latte analogies. I feel enlightened and thoroughly decomposed.",
        }
    ],
    "daily_absurdity": [
        {
            "hook_headline": "An apology to my inbox and other failed administrative duties",
            "opening_sentence": "There is a specific variety of panic reserved for the email that begins with 'Just bumping this to the top of your inbox.'",
            "narrative_angle": "micro-dread of modern adulting",
            "wit_tone": "gentle satirical introspection",
            "example_expansion": "Where does the email go when it isn't at the top? Why is it climbing? Who authorized this vertical mobility?",
        }
    ],
}


def fetch_tiktok_trends(category: str, tone: str = "ironic") -> dict[str, Any]:
    """Retrieves current viral TikTok meme formats, audio tropes, and POV structures.

    This tool searches our cultural repository for trending TikTok comedic structures
    tailored to specific categories (e.g. corporate, lifestyle, food, dating, general)
    and comedic tones (e.g. ironic, unhinged, relatable, deadpan).

    Args:
        category: Content category to match (e.g. 'corporate', 'lifestyle', 'food',
            'dating', 'general').
        tone: The target comedic tone (e.g. 'ironic', 'unhinged', 'relatable', 'deadpan').

    Returns:
        A dictionary conforming to TikTokTrendResponse containing matching trends,
        sound cues, and structural templates.
    """
    log_intent(
        "fetch_tiktok_trends",
        "fetching_tiktok_trends",
        {"category": category, "tone": tone},
    )
    try:
        normalized_cat = category.strip().lower()
        if not normalized_cat:
            normalized_cat = "general"

        # Match category or fallback gracefully
        matched_category = (
            normalized_cat if normalized_cat in TIKTOK_TREND_DATABASE else "general"
        )
        raw_items = TIKTOK_TREND_DATABASE[matched_category]

        items = [
            TikTokTrendItem(
                format_name=item["format_name"],
                sound_or_trope=item["sound_or_trope"],
                structure_template=item["structure_template"],
                humor_style=f"{item['humor_style']} ({tone})",
                example=item["example"],
            )
            for item in raw_items
        ]

        response = TikTokTrendResponse(
            status="success",
            category=matched_category,
            tone=tone,
            trends=items,
            recovery_guidance=None
            if matched_category == normalized_cat
            else f"Category '{category}' was not found in exact index; defaulted to 'general'. Valid categories are: {list(TIKTOK_TREND_DATABASE.keys())}.",
        )
        result_dict = response.model_dump()
        log_outcome(
            "fetch_tiktok_trends",
            "success",
            {"count": len(items), "category": matched_category},
        )
        return result_dict

    except Exception as e:
        log_outcome("fetch_tiktok_trends", "error", error=str(e))
        return TikTokTrendResponse(
            status="error",
            category=category,
            tone=tone,
            trends=[],
            recovery_guidance=f"Error executing fetch_tiktok_trends: {e!s}. Please retry with category='general' or category='lifestyle'.",
        ).model_dump()


def fetch_instagram_meme_formats(
    post_type: str = "carousel_dump", vibe: str = "casual"
) -> dict[str, Any]:
    """Retrieves high-performing Instagram meme templates, photo dump captions, and visual contrast hooks.

    This tool queries verified viral formats tailored for Instagram posts,
    carousels, single photos, and Reels. It returns structural blueprints,
    pairing advice, and organic, non-cringe community hashtags.

    Args:
        post_type: The Instagram post format (e.g. 'carousel_dump', 'single_photo', 'reel').
        vibe: The visual aesthetic or theme (e.g. 'euro summer', 'corporate dread', 'chaotic cooking').

    Returns:
        A dictionary conforming to InstagramMemeResponse with format templates
        and visual pairing advice.
    """
    log_intent(
        "fetch_instagram_meme_formats",
        "fetching_instagram_formats",
        {"post_type": post_type, "vibe": vibe},
    )
    try:
        normalized_type = post_type.strip().lower()
        if normalized_type not in INSTAGRAM_MEME_DATABASE:
            normalized_type = "carousel_dump"

        raw_items = INSTAGRAM_MEME_DATABASE[normalized_type]
        items = [
            InstagramMemeFormatItem(
                format_name=item["format_name"],
                hook_style=item["hook_style"],
                caption_structure=item["caption_structure"],
                visual_pairing_advice=item["visual_pairing_advice"],
                example=item["example"],
            )
            for item in raw_items
        ]

        hashtags = ["#photodump", "#notesapp", "#casualinstagram", "#currentvibe"]
        if "corporate" in vibe.lower():
            hashtags = ["#corporatelife", "#wfhproblems", "#outdoorsyintheoffice"]
        elif "food" in vibe.lower():
            hashtags = ["#culinarycrimes", "#girldinner", "#foodthoughts"]

        response = InstagramMemeResponse(
            status="success",
            post_type=normalized_type,
            vibe=vibe,
            formats=items,
            recommended_hashtags=hashtags,
            recovery_guidance=None,
        )
        result_dict = response.model_dump()
        log_outcome(
            "fetch_instagram_meme_formats",
            "success",
            {"count": len(items), "post_type": normalized_type},
        )
        return result_dict

    except Exception as e:
        log_outcome("fetch_instagram_meme_formats", "error", error=str(e))
        return InstagramMemeResponse(
            status="error",
            post_type=post_type,
            vibe=vibe,
            formats=[],
            recommended_hashtags=[],
            recovery_guidance=f"Error in fetch_instagram_meme_formats: {e!s}. Retry with post_type='carousel_dump'.",
        ).model_dump()


def fetch_substack_narrative_hooks(
    theme: str = "cultural_commentary", wit_level: str = "deadpan"
) -> dict[str, Any]:
    """Retrieves sophisticated, essayist-style opening hooks and cultural commentary for Substack newsletters.

    This tool provides literary, wry, and observational hooks designed
    to transform mundane visual scenes or lifestyle trends into engaging,
    humorous long-form or newsletter introductions.

    Args:
        theme: Core thematic topic (e.g. 'cultural_commentary', 'digital_burnout', 'daily_absurdity').
        wit_level: Desired humor tone (e.g. 'deadpan', 'subtle', 'scathing', 'reflective').

    Returns:
        A dictionary conforming to SubstackHookResponse with essay headlines,
        opening hooks, and narrative expansions.
    """
    log_intent(
        "fetch_substack_narrative_hooks",
        "fetching_substack_hooks",
        {"theme": theme, "wit_level": wit_level},
    )
    try:
        normalized_theme = theme.strip().lower()
        if normalized_theme not in SUBSTACK_HOOK_DATABASE:
            normalized_theme = "cultural_commentary"

        raw_items = SUBSTACK_HOOK_DATABASE[normalized_theme]
        items = [
            SubstackHookItem(
                hook_headline=item["hook_headline"],
                opening_sentence=item["opening_sentence"],
                narrative_angle=item["narrative_angle"],
                wit_tone=f"{item['wit_tone']} ({wit_level})",
                example_expansion=item["example_expansion"],
            )
            for item in raw_items
        ]

        response = SubstackHookResponse(
            status="success",
            theme=normalized_theme,
            wit_level=wit_level,
            hooks=items,
            recovery_guidance=None
            if normalized_theme == theme
            else f"Theme '{theme}' was normalized to '{normalized_theme}'. Available themes: {list(SUBSTACK_HOOK_DATABASE.keys())}.",
        )
        result_dict = response.model_dump()
        log_outcome(
            "fetch_substack_narrative_hooks",
            "success",
            {"count": len(items), "theme": normalized_theme},
        )
        return result_dict

    except Exception as e:
        log_outcome("fetch_substack_narrative_hooks", "error", error=str(e))
        return SubstackHookResponse(
            status="error",
            theme=theme,
            wit_level=wit_level,
            hooks=[],
            recovery_guidance=f"Error in fetch_substack_narrative_hooks: {e!s}. Try theme='cultural_commentary'.",
        ).model_dump()


def scrub_ai_cliches(caption_text: str) -> dict[str, Any]:
    """Scans and cleans candidate captions for robotic AI clichés, corporate buzzwords, and unnatural cadence.

    This deterministic guardrail tool audits input text against a blacklist of
    forbidden LLM phrases (e.g., 'delve into', 'unleash your inner', 'game changer',
    'rich tapestry'), flags em-dash abuse and excessive exclamation points, and
    provides a cleaned version with actionable critique for humanization.

    Args:
        caption_text: The caption or hook text to be audited.

    Returns:
        A dictionary conforming to ScrubResult containing cleanliness status,
        detected clichés, cringe severity score (0-10), critique, and cleaned text.
    """
    log_intent(
        "scrub_ai_cliches",
        "auditing_caption_cliches",
        {"input_length": len(caption_text)},
    )
    try:
        if not caption_text or not caption_text.strip():
            log_outcome(
                "scrub_ai_cliches", "success", {"is_clean": True, "detected": []}
            )
            return ScrubResult(
                status="success",
                is_clean=True,
                detected_cliches=[],
                severity_score=0,
                cleaned_text="",
                critique="Empty text provided. Ready for human captions.",
                recovery_guidance=None,
            ).model_dump()

        text_lower = caption_text.lower()
        found_cliches: list[str] = []

        # 1. Check for blacklisted phrases
        for phrase in BANNED_AI_CLICHES:
            # Word-boundary matching for cleaner precision
            pattern = rf"\b{re.escape(phrase)}\b"
            if re.search(pattern, text_lower):
                found_cliches.append(phrase)

        # 2. Check for structural AI markers: Em-dashes, excessive exclamations
        has_em_dash = bool(re.search(r"—|--|\s-\s", caption_text))
        exclamation_count = caption_text.count("!")
        if has_em_dash:
            found_cliches.append("em-dash / hyphen cadence")
        if exclamation_count > 1:
            found_cliches.append(f"excessive exclamation marks ({exclamation_count})")

        # 3. Calculate severity score (0-10)
        severity = min(10, len(found_cliches) * 3)

        # 4. Generate clean replacement heuristic
        cleaned = caption_text
        for phrase in found_cliches:
            if phrase not in [
                "em-dash / hyphen cadence",
                f"excessive exclamation marks ({exclamation_count})",
            ]:
                # Case-insensitive replacement
                cleaned = re.sub(
                    rf"\b{re.escape(phrase)}\b", "", cleaned, flags=re.IGNORECASE
                )

        # Replace em dashes with simple comma or period
        cleaned = re.sub(r"—|--", ", ", cleaned)
        # Normalize multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Enforce max 1 exclamation
        if exclamation_count > 1:
            cleaned = cleaned.replace("!", ".")

        # Humanize capitalization if overly title-cased
        if (
            sum(1 for c in cleaned if c.isupper()) > len(cleaned) * 0.4
            and len(cleaned) > 10
        ):
            cleaned = cleaned.lower()

        is_clean = len(found_cliches) == 0
        critique_parts: list[str] = []
        if not is_clean:
            critique_parts.append(
                f"Detected {len(found_cliches)} robotic AI clichés/markers: {', '.join(found_cliches)}."
            )
            critique_parts.append(
                "Human social copy uses casual phrasing, lowercase aesthetics, and dry punchlines."
            )
        else:
            critique_parts.append(
                "Zero AI clichés detected. Phrasing sounds authentic and human-crafted."
            )

        recovery_msg = None
        if not is_clean:
            recovery_msg = (
                "Please regenerate the caption without using any of the detected cliché phrases. "
                "Use dry, self-deprecating, or observational human humor instead."
            )

        result = ScrubResult(
            status="success",
            is_clean=is_clean,
            detected_cliches=found_cliches,
            severity_score=severity,
            cleaned_text=cleaned,
            critique=" ".join(critique_parts),
            recovery_guidance=recovery_msg,
        )
        result_dict = result.model_dump()
        log_outcome(
            "scrub_ai_cliches",
            "success",
            {"is_clean": is_clean, "severity": severity, "cliches": found_cliches},
        )
        return result_dict

    except Exception as e:
        log_outcome("scrub_ai_cliches", "error", error=str(e))
        return ScrubResult(
            status="error",
            is_clean=False,
            detected_cliches=[],
            severity_score=5,
            cleaned_text=caption_text,
            critique=f"Error executing scrub_ai_cliches: {e!s}",
            recovery_guidance="Proceed with caution, ensuring output does not include corporate AI phrases like 'delve into' or 'unleash'.",
        ).model_dump()


async def search_user_vibe_history(
    query: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Asynchronously searches the user's persistent memory bank and vibe history for past styles or humor angles.

    Args:
        query: The semantic search query or theme (e.g. 'preferred tone', 'past captions', 'corporate jokes').

    Returns:
        A dictionary containing matched past memory records, preferred vibes, and status.
    """
    log_intent("search_user_vibe_history", "searching_memory_bank", {"query": query})
    try:
        memories: list[str] = []
        if hasattr(tool_context, "search_memory"):
            try:
                mem_results = await tool_context.search_memory(query)
                if mem_results:
                    memories.extend([str(m) for m in mem_results])
            except Exception:
                pass

        user_vibe = tool_context.state.get(
            "user:vibe_profile", "default authentic creator"
        )
        past_captions = tool_context.state.get("user:saved_captions", [])

        matched = [
            c
            for c in past_captions
            if any(w in c.lower() for w in query.lower().split())
        ]
        if not matched and past_captions:
            matched = past_captions[-3:]

        result = {
            "status": "success",
            "query": query,
            "user_vibe_profile": user_vibe,
            "recalled_memories": memories or matched,
            "count": len(memories or matched),
            "recovery_guidance": None,
        }
        log_outcome(
            "search_user_vibe_history", "success", {"count": len(memories or matched)}
        )
        return result
    except Exception as e:
        log_outcome("search_user_vibe_history", "error", error=str(e))
        return {
            "status": "error",
            "query": query,
            "user_vibe_profile": "casual authentic",
            "recalled_memories": [],
            "recovery_guidance": f"Memory search error: {e!s}. Proceeding with default user profile.",
        }


async def save_vibe_memory(
    vibe: str,
    style_notes: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Asynchronously persists the user's comedic style preferences and viral formulas into long-term user memory.

    Args:
        vibe: The primary comedic vibe or aesthetic preference (e.g. 'unhinged corporate dread', 'minimalist aesthetic irony').
        style_notes: Specific guidelines or rules learned from this conversation.

    Returns:
        A dictionary confirming memory persistence status and updated profile.
    """
    log_intent("save_vibe_memory", "persisting_user_vibe", {"vibe": vibe})
    try:
        updated_profile = f"{vibe} | {style_notes}".strip(" |")
        tool_context.state["user:vibe_profile"] = updated_profile

        saved_captions = tool_context.state.get("user:saved_captions", [])
        if style_notes and style_notes not in saved_captions:
            saved_captions.append(style_notes)
            tool_context.state["user:saved_captions"] = saved_captions[-10:]

        result = {
            "status": "success",
            "vibe_saved": vibe,
            "updated_profile": updated_profile,
            "recovery_guidance": None,
        }
        log_outcome("save_vibe_memory", "success", {"vibe": vibe})
        return result
    except Exception as e:
        log_outcome("save_vibe_memory", "error", error=str(e))
        return {
            "status": "error",
            "vibe_saved": vibe,
            "recovery_guidance": f"Error persisting memory: {e!s}. State will remain in session scope.",
        }
