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

    def get_global_settings(self, name: str):
        settings_collection = self.db["global_settings"]
        settings = settings_collection.find_one({name: name})
        return settings

    def set_global_settings(self, name: str, value: bool):
        settings_collection = self.db["global_settings"]
        settings_collection.update_one({name: name}, {"$set": {"value": f"{str(value).lower()}"}}, upsert=True)

    def get_shards(self, user_id: str):
        user_id = str(user_id)
        # Use projection to only fetch the shards field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"shards": 1})
        if not user:
            # User doesn't exist, create and return 0
            self.insert_user(user_id)
            return 0
        return user.get("shards", 0)

    def get_enabled_items(self, user_id: str):
        user_id = str(user_id)
        # Use projection to only fetch the enabled_items field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"enabled_items": 1})
        if not user:
            return []
        return user.get("enabled_items", [])

    def is_enabled(self, user_id: str, item_key: str):
        user_id = str(user_id)
        # Use projection to only fetch the enabled_items field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"enabled_items": 1})
        if not user:
            return False
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
        # Use projection to only fetch the card_mute field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"card_mute": 1})
        if not user:
            return False
        return user.get("card_mute", False)

    def is_card_muted(self, user_id: str):
        user_id = str(user_id)
        # Use projection to only fetch the card_mute field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"card_mute": 1})
        if not user:
            return False
        return user.get("card_mute", False)

    def update_user(self, user_id: str, update_data):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )

    def get_cards(self, user_id: str):
        user_id = str(user_id)
        # Use projection to only fetch the cards field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"cards": 1})
        if not user:
            return []
        return user.get("cards", [])

    def get_characters(self, user_id: str):
        user_id = str(user_id)
        # Use projection to only fetch the characters field for efficiency
        user = self.users.find_one({"user_id": user_id}, {"characters": 1})
        if not user:
            return []
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

    def update_character_thumbnail(self, user_id: str, character_id: str, character_name: str,
                                   thumbnail_url: str) -> bool:
        user_id = str(user_id)
        result = self.users.update_one(
            {
                "user_id": user_id,
                "characters": {
                    "$elemMatch": {
                        "character_id": character_id,
                        "name": character_name
                    }
                }
            },
            {
                "$set": {
                    "characters.$.thumbnail_url": thumbnail_url
                }
            }
        )
        return result.modified_count > 0

    def get_all_users(self):
        return list(self.users.find())

    def remove_user(self, user_id: str):
        user_id = str(user_id)
        result = self.users.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    def remove_advertisement(self, user_id: str, ad_id: str):
        user_id = str(user_id)
        ad_id = str(ad_id)
        result = self.users.update_one(
            {"user_id": user_id},
            {"$pull": {"ad_data": {"ad_id": ad_id}}}
        )
        return result.modified_count > 0

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

    def card_count(self, user_id: str, card_name: str) -> str:
        """
        Returns the number of cards with the specified name for the given user.

        Args:
            user_id (str): The ID of the user.
            card_name (str): The name of the card to count.

        Returns:
            int: The number of cards with the specified name.
        """
        user_id = str(user_id)
        user = self.get_user(user_id)
        characters = user.get("characters", [])
        count = len([c for c in characters if c.get("name", "").strip().lower() == card_name.strip().lower()])
        return str(count)

    def add_shards(self, user_id: str, shards):
        user_id = str(user_id)
        self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"shards": shards}},
            upsert=True
        )

    def global_card_count(self, card_name: str, top_n: int = 3) -> list:
        """
        Returns a list of the top N users with the highest count of the specified card.
        Uses MongoDB aggregation for better performance.

        Args:
            card_name (str): The name of the card to count.
            top_n (int): The number of top users to return. Default is 3.

        Returns:
            list: A list of tuples where each tuple contains (user_id, count) for the top N users.
        """
        card_name_lower = card_name.strip().lower()
        
        # Use MongoDB aggregation pipeline for efficient counting
        pipeline = [
            # Unwind the characters array to process each character individually
            {"$unwind": "$characters"},
            # Filter for matching card names (case-insensitive)
            {"$match": {
                "$expr": {
                    "$eq": [
                        {"$toLower": {"$trim": {"input": "$characters.name"}}},
                        card_name_lower
                    ]
                }
            }},
            # Group by user_id and count occurrences
            {"$group": {
                "_id": "$user_id",
                "count": {"$sum": 1}
            }},
            # Sort by count in descending order
            {"$sort": {"count": -1}},
            # Limit to top N results
            {"$limit": top_n}
        ]
        
        try:
            results = list(self.users.aggregate(pipeline))
            return [(result["_id"], result["count"]) for result in results]
        except Exception as e:
            print(f"Error in global_card_count aggregation: {e}")
            # Fallback to original implementation if aggregation fails
            result = {}
            all_users = self.get_all_users()
            
            for user in all_users:
                user_id = user.get("user_id")
                characters = user.get("characters", [])
                count = len([c for c in characters if c.get("name", "").strip().lower() == card_name_lower])
                if count > 0:
                    result[user_id] = count
            
            sorted_result = sorted(result.items(), key=lambda item: item[1], reverse=True)
            return sorted_result[:top_n]
