import json
import os
import random

from SAJAX.database import Database

db = Database()

rarities_path = os.path.join(os.path.dirname(__file__), "data/rarities.json")
characters_path = os.path.join(os.path.dirname(__file__), "data/characters.json")

# Cache JSON data at module level to avoid repeated file I/O
_rarities_data = None
_characters_data = None

def _load_rarities():
    """Load rarities data with caching."""
    global _rarities_data
    if _rarities_data is None:
        with open(rarities_path) as f:
            _rarities_data = json.load(f)["rarities"]
    return _rarities_data

def _load_characters():
    """Load characters data with caching."""
    global _characters_data
    if _characters_data is None:
        with open(characters_path) as f:
            _characters_data = json.load(f)
    return _characters_data

rarities_data = _load_rarities()
characters_data = _load_characters()

RARITY_ORDER = ["B", "A", "R", "UR", "S"]

rarity_choices = [rarity["tier"] for rarity in rarities_data]
rarity_weights = [rarity["drop_rate"] for rarity in rarities_data]


def rarity_index(tier):
    return RARITY_ORDER.index(tier)


def select_random_character():
    # Remove "S" from rarity pool so it's never chosen
    filtered_rarity_choices = [r for r in rarity_choices if r != "S"]
    filtered_rarity_weights = [
        w for r, w in zip(rarity_choices, rarity_weights) if r != "S"
    ]

    # Step 1 — choose rarity first
    chosen_rarity = random.choices(filtered_rarity_choices, weights=filtered_rarity_weights, k=1)[0]

    # Step 2 — only select characters that allow this rarity
    eligible_characters = [
        char for char in characters_data
        if rarity_index(char["lowest_rarity"]) <= rarity_index(chosen_rarity) <= rarity_index(char["top_rarity"])
    ]

    # Step 3 — fallback if none available
    if not eligible_characters:
        return select_random_character()

    # Step 4 — pick one character
    selected_character = random.choice(eligible_characters)

    # Step 5 — Limited character check
    if "(Limited)" in selected_character["name"]:
        global_setting = db.get_global_settings("global_setting_limited_cards")
        limited_cards_enabled = global_setting.get("value", "false").lower() == "true"

        if not limited_cards_enabled:
            return select_random_character()

    return {
        "character": selected_character,
        "rarity": chosen_rarity
    }

