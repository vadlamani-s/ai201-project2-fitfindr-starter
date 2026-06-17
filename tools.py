"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _tokenize_text(text: str) -> set[str]:
    """Split text into normalized lowercase tokens for matching."""
    if not text:
        return set()
    normalized = text.lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    return set(tokens)


def _score_listing(query_tokens: set[str], listing: dict) -> int:
    """Score a listing by how many query tokens appear in its searchable fields."""
    if not query_tokens:
        return 0

    title_tokens = _tokenize_text(listing.get("title", ""))
    description_tokens = _tokenize_text(listing.get("description", ""))
    category_tokens = _tokenize_text(listing.get("category", ""))
    brand_tokens = _tokenize_text(listing.get("brand", ""))
    style_tokens = {tag.lower() for tag in listing.get("style_tags", []) if isinstance(tag, str)}
    color_tokens = {color.lower() for color in listing.get("colors", []) if isinstance(color, str)}
    platform_tokens = _tokenize_text(listing.get("platform", ""))

    searchable_tokens = (
        title_tokens
        | description_tokens
        | category_tokens
        | brand_tokens
        | style_tokens
        | color_tokens
        | platform_tokens
    )

    return len(query_tokens & searchable_tokens)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    description = description or ""
    query_tokens = _tokenize_text(description)
    normalized_size = size.strip().lower() if size else None

    filtered_listings = []
    for listing in load_listings():
        if max_price is not None and listing.get("price") is not None:
            try:
                price = float(listing["price"])
            except (TypeError, ValueError):
                continue
            if price > max_price:
                continue

        if normalized_size:
            listing_size = str(listing.get("size", "")).lower()
            if normalized_size not in listing_size:
                continue

        score = _score_listing(query_tokens, listing)
        if score <= 0:
            continue

        filtered_listings.append((score, listing))

    filtered_listings.sort(key=lambda item: item[0], reverse=True)
    return [listing for _, listing in filtered_listings]


def _summarize_new_item(new_item: dict) -> str:
    title = new_item.get("title") or new_item.get("name") or "This item"
    category = new_item.get("category", "")
    colors = ", ".join(new_item.get("colors", [])).strip()
    style_tags = ", ".join(new_item.get("style_tags", [])).strip()
    brand = new_item.get("brand")
    price = new_item.get("price")
    platform = new_item.get("platform")
    description = new_item.get("description", "").strip()

    fields = [f"Name: {title}"]
    if category:
        fields.append(f"Category: {category}")
    if colors:
        fields.append(f"Colors: {colors}")
    if style_tags:
        fields.append(f"Style tags: {style_tags}")
    if brand:
        fields.append(f"Brand: {brand}")
    if price is not None:
        fields.append(f"Price: ${price}")
    if platform:
        fields.append(f"Platform: {platform}")
    if description:
        fields.append(f"Description: {description}")

    return "\n".join(fields)


def _summarize_wardrobe_items(wardrobe: dict) -> str:
    items = wardrobe.get("items") or []
    summaries = []
    for item in items[:8]:
        name = item.get("name", "Unnamed piece")
        category = item.get("category", "piece")
        colors = ", ".join(item.get("colors", [])).strip() or "neutral colors"
        style_tags = ", ".join(item.get("style_tags", [])).strip() or "versatile"
        notes = item.get("notes")
        summary = f"- {name} ({category}; colors: {colors}; styles: {style_tags}"
        if notes:
            summary += f"; notes: {notes}"
        summary += ")"
        summaries.append(summary)
    return "\n".join(summaries)


def _generate_fallback_suggestion(new_item: dict, wardrobe: dict) -> str:
    item_name = new_item.get("title") or new_item.get("name") or "This item"
    colors = ", ".join(new_item.get("colors", [])).strip()
    if not colors:
        colors = "neutral tones"
    if not wardrobe.get("items"):
        return (
            f"{item_name} has a great vibe on its own — pair it with simple staple pieces like a white tee, straight-leg jeans, or a tailored blazer for a clean look. "
            "Choose accessories that echo its colors and keep the outfit balanced with minimal layers."
        )

    first_piece = wardrobe["items"][0].get("name", "a wardrobe piece")
    return (
        f"Pair {item_name} with {first_piece} for an easy outfit, then add a neutral shoe and a simple accessory to keep the look cohesive. "
        "Look for pieces in similar color families or complementary textures to make it feel polished."
    )


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    items = wardrobe.get("items") if isinstance(wardrobe, dict) else []
    if items is None:
        items = []

    new_item_summary = _summarize_new_item(new_item)
    wardrobe_summary = _summarize_wardrobe_items(wardrobe)

    if not items:
        prompt = (
            "You are a friendly personal stylist. "
            "A user just found this thrifted item and wants styling advice: \n"
            f"{new_item_summary}\n\n"
            "Give 1-2 outfit ideas or styling directions for this item on its own, "
            "including what kinds of wardrobe staples would pair best with it, "
            "what vibe it suits, and why. Keep the response helpful and concise."
        )
    else:
        prompt = (
            "You are a friendly personal stylist. "
            "A user has the following wardrobe items and is considering adding a "
            "new thrifted piece. Suggest 1-2 specific outfit combinations that use "
            "the new item together with named pieces from the user's wardrobe. \n"
            f"New item:\n{new_item_summary}\n\n"
            f"Wardrobe items:\n{wardrobe_summary}\n\n"
            "Make the advice practical and easy to follow. Mention the wardrobe pieces "
            "by name and explain why they work together."
        )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="gemma-7b-it",
            messages=[
                {"role": "system", "content": "You are a fashion stylist helping a user build outfits."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=400,
        )
        content = ""
        if response and getattr(response, "choices", None):
            first_choice = response.choices[0]
            message = getattr(first_choice, "message", None)
            content = message.content if message and getattr(message, "content", None) else ""
        if content and content.strip():
            return content.strip()
    except Exception:
        pass

    return _generate_fallback_suggestion(new_item, wardrobe)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    if not outfit or not outfit.strip():
        return "I couldn't create a caption because there wasn't an outfit suggestion to work from. Try generating an outfit first."

    item_name = new_item.get("title") or new_item.get("name") or "This thrifted piece"
    platform = new_item.get("platform") or "a secondhand platform"
    price = new_item.get("price")
    price_text = f"${price}" if price is not None else "an affordable price"

    item_details = (
        f"Item name: {item_name}\n"
        f"Price: {price_text}\n"
        f"Platform: {platform}\n"
        f"Additional info: {new_item.get('description', '').strip()}"
    ).strip()

    prompt = (
        "You are a social-media caption writer for a fashion-loving audience. "
        "Write a casual, authentic 2-4 sentence caption for an Instagram/TikTok post. "
        "Do not sound like a product description. Mention the item name, its price, "
        "and the platform naturally once each. Capture the outfit vibe in specific terms, "
        "and make it feel fresh, confident, and shareable.\n\n"
        f"Item details:\n{item_details}\n\n"
        f"Outfit suggestion:\n{outfit}\n\n"
        "Return only the caption text, without extra explanation or formatting notes."
    )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="gemma-7b-it",
            messages=[
                {"role": "system", "content": "You are a creative fashion caption writer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=120,
        )
        caption = ""
        if response and getattr(response, "choices", None):
            first_choice = response.choices[0]
            message = getattr(first_choice, "message", None)
            caption = message.content if message and getattr(message, "content", None) else ""
        if caption and caption.strip():
            return caption.strip()
    except Exception:
        pass

    return (
        f"{item_name} is giving major styling energy — layered with your favorite wardrobe staples, it's a perfect look for everyday outings. "
        f"Found it for {price_text} on {platform}, and it makes the outfit feel effortless and polished."
    )
