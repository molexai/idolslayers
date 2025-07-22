import time
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()

class Database:
    def __init__(self):
        self.uri = "mongodb+srv://sajax:sajax@sajax.t2kzc70.mongodb.net/"
        self.client = MongoClient(self.uri, tls=True)
        self.db = self.client["sajax"]
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
        # Removed cache check here
        user = {"user_id": user_id, "cards": [], "shards": 0, "characters": []}
        self.users.insert_one(user)
        return user

    def get_user(self, user_id: str):
        user_id = str(user_id)
        user = self.users.find_one({"user_id": user_id})
        if not user:
            user = {"user_id": user_id, "cards": [], "shards": 0, "characters": []}
            self.users.insert_one(user)
        return user

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
