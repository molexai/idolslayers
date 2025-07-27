import time

from pymongo import MongoClient, ASCENDING


class Database:
    _client = None

    def __init__(self):
        if Database._client is None:
            uri = "mongodb+srv://sajax:sajax@sajax.t2kzc70.mongodb.net/"
            Database._client = MongoClient(uri, tls=True)

        self.db = Database._client["sajax"]
        self.users = self.db["users"]

        #self.cache = {}
        self.cooldowns = {}

        self.users.create_index([("user_id", ASCENDING)], unique=True)

    def is_on_cooldown(self, user_id: str, cooldown=5):
        user_id = str(user_id)
        now = time.time()
        if user_id in self.cooldowns and now - self.cooldowns[user_id] < cooldown:
            return True
        self.cooldowns[user_id] = now
        return False

    def insert_user(self, user_id: str):
        user_id = str(user_id)
        user = {"user_id": user_id, "cards": [], "shards": 0, "characters": [], "card_mute": False,
                "quests": []}
        self.users.insert_one(user)
        return user

    def get_user(self, user_id: str):
        user_id = str(user_id)
        user = self.users.find_one({"user_id": user_id})
        if not user:
            user = {"user_id": user_id, "cards": [], "shards": 0, "characters": [], "card_mute": False,
                    "quests": []}
            self.users.insert_one(user)
        return user

    def get_shards(self, user_id: str):
        user_id = str(user_id)
        user = self.get_user(user_id)
        return user.get("shards", 0)

    def get_enabled_items(self, user_id: str):
        user_id = str(user_id)
        user = self.get_user(user_id)
        return user.get("enabled_items", [])

    def is_enabled(self, user_id: str, item_key: str):
        user_id = str(user_id)
        user = self.get_user(user_id)
        enabled_items = user.get("enabled_items", [])
        return item_key in enabled_items

    def remove_character_and_card(self, user_id: str, character_data):
        user_id = str(user_id)
        user = self.get_user(user_id)
        characters = user.get("characters", [])
        cards = user.get("cards", [])

        character_to_remove = None
        for char in characters:
            if char == character_data:
                character_to_remove = char
                break

        if character_to_remove:
            characters.remove(character_to_remove)

            char_id_to_remove = character_to_remove.get("character_id")
            if char_id_to_remove in cards:
                cards.remove(char_id_to_remove)

            self.users.update_one(
                {"user_id": user_id},
                {"$set": {"characters": characters, "cards": cards}},
                upsert=True
            )

    def remove_all_characters(self, user_id: str):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"characters": [], "cards": []}},
            upsert=True
        )

    def card_mute(self, user_id: str):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"card_mute": True}},
            upsert=True
        )

    def card_unmute(self, user_id: str):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"card_mute": False}},
            upsert=True
        )

    def card_mute_status(self, user_id: str):
        user_id = str(user_id)
        user = self.get_user(user_id)
        return user.get("card_mute", False)

    def is_card_muted(self, user_id: str):
        user_id = str(user_id)
        user = self.get_user(user_id)
        return user.get("card_mute", False)

    def update_user(self, user_id: str, update_data):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )

    def get_cards(self, user_id: str):
        user = self.get_user(user_id)
        return user.get("cards", [])

    def get_characters(self, user_id: str):
        user = self.get_user(user_id)
        return user.get("characters", [])

    def add_card(self, user_id: str, card):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$push": {"cards": card}},
            upsert=True
        )

    def update_existing_character(self, user_id: str, original_data: dict, new_data: dict) -> bool:
        user_id = str(user_id)
        user = self.get_user(user_id)
        characters = user.get("characters", [])

        for i, char in enumerate(characters):
            if char == original_data:
                characters[i].update(new_data)
                self.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"characters": characters}},
                    upsert=True
                )
                return True
        return False

    def get_all_users(self):
        return list(self.users.find())

    def add_card_reroll_to_all_users(self):
        users = self.get_all_users()
        count = 0

        for user in users:
            user_id = user.get("user_id")
            enabled_items = user.get("enabled_items", [])
            if "card_reroll" not in enabled_items:
                enabled_items.append("card_reroll")
                self.update_user(user_id, {"enabled_items": enabled_items})
                count += 1

        return count


    def add_character(self, user_id: str, character):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$push": {"characters": character}},
            upsert=True
        )

    def add_shards(self, user_id: str, shards):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"shards": shards}},
            upsert=True
        )
