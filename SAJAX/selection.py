import json
import random

with open("data/rarities.json") as f:
    rarities_data = json.load(f)["rarities"]

with open("data/characters.json") as f:
    characters_data = json.load(f)

RARITY_ORDER = ["B", "A", "R", "UR"]

rarity_choices = [rarity["tier"] for rarity in rarities_data]
rarity_weights = [rarity["drop_rate"] for rarity in rarities_data]


def rarity_index(tier):
    return RARITY_ORDER.index(tier)


def select_random_character():
    chosen_rarity = random.choices(rarity_choices, weights=rarity_weights, k=1)[0]

    eligible_characters = [
        char for char in characters_data
        if rarity_index(char["lowest_rarity"]) <= rarity_index(chosen_rarity) <= rarity_index(char["top_rarity"])
    ]

    if not eligible_characters:
        return select_random_character()

    selected_character = random.choice(eligible_characters)

    return {
        "character": selected_character,
        "rarity": chosen_rarity
    }
