"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """Extract description, size, and max_price from a user query."""
    normalized = query.strip()
    max_price = None
    size = None

    price_match = re.search(r"\b(?:under|below|up to)\s*\$?\s*(\d+(?:\.\d+)?)\b", normalized, re.I)
    if price_match:
        try:
            max_price = float(price_match.group(1))
        except ValueError:
            max_price = None
        normalized = re.sub(re.escape(price_match.group(0)), "", normalized, flags=re.I)

    size_match = re.search(r"\b(?:size|sz)\s*([A-Za-z0-9/().+-]+)\b", normalized, re.I)
    if size_match:
        size = size_match.group(1).strip()
        normalized = re.sub(re.escape(size_match.group(0)), "", normalized, flags=re.I)

    normalized = re.sub(r"\b(looking for|looking|searching for|find|find me|want|need)\b", "", normalized, flags=re.I)
    normalized = re.sub(r"[\.,;!]+", " ", normalized)
    description = " ".join(normalized.split()).strip()
    if not description:
        description = query.strip()

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
    """
    session = _new_session(query, wardrobe)
    parsed = _parse_query(query)
    session["parsed"] = parsed

    search_results = search_listings(
        parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = search_results

    if not search_results:
        session["error"] = (
            "No listings matched your search. Try broadening the description, "
            "removing the size filter, or increasing the price limit."
        )
        return session

    session["selected_item"] = search_results[0]
    session["outfit_suggestion"] = suggest_outfit(session["selected_item"], wardrobe)
    session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
