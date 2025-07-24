# Entire file with modifications

import nextcord
from nextcord.ext import commands, tasks
from nextcord import SlashOption, Interaction, ButtonStyle
from nextcord.ui import View, button, Select
import asyncio
import time
import random
import json
import os

from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = [1387525150752378940, 1389313345986756708]

class CardPageView(View):
    def __init__(self, user_cards, templates, timeout=180):
        super().__init__(timeout=timeout)
        self.cards = user_cards
        self.index = 0
        self.templates = templates

        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.index == 0
        self.children[1].disabled = self.index == len(self.cards) - 1

    def generate_embed(self):
        card = self.cards[self.index]
        name = card.get('name', 'Unknown')
        rarity = card.get('rarity', card.get('top_rarity', 'Unknown'))
        description = card.get('description', 'No description available.').replace('â€™', "")
        group = card.get('group', 'Unknown')
        embed = self.templates.card_details(name, rarity, description, group, card.get('thumbnail_url'))
        embed.set_footer(text=f"Card {self.index + 1} of {len(self.cards)}")
        return embed

    @button(label="Previous", style=ButtonStyle.blurple)
    async def previous(self, button: button, interaction: Interaction):
        if self.index > 0:
            self.index -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Next", style=ButtonStyle.blurple)
    async def next(self, button: button, interaction: Interaction):
        if self.index < len(self.cards) - 1:
            self.index += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

class CardSelect(Select):
    def __init__(self, cards, templates):
        options = [
            nextcord.SelectOption(
                label=card.get('name', 'Unknown'),
                description=f"Rarity: {card.get('rarity', card.get('top_rarity', 'Unknown'))}",
                value=str(i)
            )
            for i, card in enumerate(cards[:25])  # Limit to 25
        ]
        super().__init__(placeholder="Select a card to view details...", min_values=1, max_values=1, options=options)
        self.cards = cards
        self.templates = templates
        self.current_embed = None

    async def callback(self, interaction: Interaction):
        index = int(self.values[0])
        card = self.cards[index]
        name = card.get('name', 'Unknown')
        rarity = card.get('rarity', card.get('top_rarity', 'Unknown'))
        description = card.get('description', 'No description available.').replace('â€™', "")
        group = card.get('group', 'Unknown')
        embed = self.templates.card_details(name, rarity, description, group, card.get('thumbnail_url'))
        embed.set_footer(text=f"Card details for {name}")
        self.current_embed = embed

        await interaction.response.edit_message(embed=embed, view=self.view)

class CardMenuView(View):
    def __init__(self, cards, templates, timeout=180):
        super().__init__(timeout=timeout)
        self.select = CardSelect(cards, templates)
        self.add_item(self.select)
        self.message = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

class Drop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.queued_users = set()
        self.cooldowns = {}
        self.COOLDOWN_SECONDS = 3600
        self.mycards_cooldowns = {}
        self.MYCARDS_COOLDOWN = 10
        self.processing = False
        self.process_queue.start()
        self.db = Database()
        self.json_path = os.path.join(os.path.dirname(__file__), "characters_card_images.json")

    def cog_unload(self):
        self.process_queue.cancel()

    def assign_thumbnail(self, character_name: str, rarity: str) -> str:
        with open(self.json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        for character in data["characters"]:
            if character["name"].lower() == character_name.lower():
                for rarity_block in character["rarities"]:
                    if rarity_block["rarity"].upper() == rarity.upper():
                        urls = [
                            url for key, url in rarity_block.items()
                            if key.startswith("image_url_") and url.strip() != ""
                        ]
                        if not urls:
                            return ""
                        random.shuffle(urls)
                        return random.choice(urls)
        return ""

    @nextcord.slash_command(
        name="mycards",
        description="View your SAJAX cards!",
        guild_ids=GUILD_ID
    )
    async def mycards(
            self,
            ctx: Interaction,
            mode: str = SlashOption(
                description="Choose display mode: menu (dropdown) or normal (pagination)",
                required=False,
                choices={"menu": "menu", "normal": "normal"},
                default="normal"
            )
    ):
        user = ctx.user
        now = time.time()
        last_used = self.mycards_cooldowns.get(user.id, 0)

        if now - last_used < self.MYCARDS_COOLDOWN:
            remaining = round(self.MYCARDS_COOLDOWN - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            await ctx.send(embed=embed, ephemeral=True)
            return

        self.mycards_cooldowns[user.id] = now

        user_data = self.db.get_user(str(user.id))
        cards = user_data.get("characters", [])

        if not cards:
            embed = Templates.drop_error()
            embed.description = "> You have no cards yet! Try using `/drop` to summon some."
            await ctx.send(embed=embed, ephemeral=True)
            return

        if mode == "menu":
            view = CardMenuView(cards, Templates)
            message = await ctx.send(embed=Templates.card_details(
                cards[0].get('name', 'Unknown'),
                cards[0].get('rarity', cards[0].get('top_rarity', 'Unknown')),
                cards[0].get('description', 'No description available.').replace('â€™', ""),
                cards[0].get('group', 'Unknown'),
                cards[0].get('thumbnail_url')),
                view=view,
                ephemeral=True
            )
            view.message = message
        else:
            view = CardPageView(cards, Templates)
            await ctx.send(embed=view.generate_embed(), view=view, ephemeral=True)

    @nextcord.slash_command(
        name="drop",
        description="Summon your next SAJAX cards with this command!",
        guild_ids=GUILD_ID,
    )
    async def drop(self, interaction: nextcord.Interaction):
        user = interaction.user
        now = time.time()
        last_used = self.cooldowns.get(user.id, 0)

        if interaction.guild and interaction.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        if user.id in self.queued_users:
            embed = Templates.drop_error()
            embed.description = "> You are already in the drop queue! Please wait for your turn."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if now - last_used < self.COOLDOWN_SECONDS:
            remaining = int(self.COOLDOWN_SECONDS - (now - last_used))
            mins, secs = divmod(remaining, 60)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {mins}m {secs}s."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.cooldowns[user.id] = now
        embed = Templates.drop_summon()
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.queued_users.add(user.id)
        await self.queue.put((user, 3))
        return

    @nextcord.slash_command(
        name="admin_drop",
        description="Admin-only version of drop that allows setting drop amount.",
        guild_ids=GUILD_ID,
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def admin_drop(
            self,
            interaction: nextcord.Interaction,
            amount: int = SlashOption(
                description="Number of cards to summon",
                required=False,
                default=10
            )
    ):
        user = interaction.user

        if user.id in self.queued_users:
            embed = Templates.drop_error()
            embed.description = "You are already processing a drop! Please wait."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.queued_users.add(user.id)
        embed = Templates.drop_summon()
        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            for _ in range(amount):
                await self.generate_drop_return_card(user)

            embed_success = Templates.drop_success()
            embed_success.description = (
                f"> You have received **{amount}** admin dropped cards!\n"
                "Use `/mycards` to view them."
            )

            dm = await user.create_dm()
            await dm.send(embed=embed_success)

        except nextcord.Forbidden:
            print(f"Could not DM {user}.")

        finally:
            self.queued_users.discard(user.id)

    async def generate_drop(self, user):
        from SAJAX.selection import select_random_character

        user_id_str = str(user.id)
        if not self.db.get_user(user_id_str):
            self.db.insert_user(user_id_str)

        formatted_drop = select_random_character()
        formatted_rarity = {"B": "Balanced", "A": "Amazing", "R": "Rare", "UR": "Ultra Rare"}
        character = formatted_drop["character"]
        rarity_key = formatted_drop["rarity"]
        rarity = formatted_rarity[rarity_key]

        print(f"{user}, You pulled a {rarity} character: {character['name']}")

        thumbnail_url = self.assign_thumbnail(character["name"], rarity_key)
        character_with_rarity = character.copy()
        character_with_rarity["rarity"] = rarity_key
        if thumbnail_url:
            character_with_rarity["thumbnail_url"] = thumbnail_url

        self.db.add_character(user_id_str, character_with_rarity)
        self.db.add_card(user_id_str, character["character_id"])

        embed = Templates.drop_summon()
        embed.title = f"You pulled a {rarity} character!"
        embed.description = f"{character['name']}"
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        return embed

    async def generate_drop_return_card(self, user):
        from SAJAX.selection import select_random_character

        user_id_str = str(user.id)
        if not self.db.get_user(user_id_str):
            self.db.insert_user(user_id_str)

        formatted_drop = select_random_character()
        formatted_rarity = {"B": "Balanced", "A": "Amazing", "R": "Rare", "UR": "Ultra Rare"}

        character = formatted_drop["character"]
        rarity_key = formatted_drop["rarity"]
        rarity = formatted_rarity[rarity_key]

        thumbnail_url = self.assign_thumbnail(character["name"], rarity_key)
        character_with_rarity = character.copy()
        character_with_rarity["rarity"] = rarity_key
        if thumbnail_url:
            character_with_rarity["thumbnail_url"] = thumbnail_url

        self.db.add_character(user_id_str, character_with_rarity)
        self.db.add_card(user_id_str, character["character_id"])

        return character_with_rarity, rarity

    @tasks.loop(seconds=0.5)
    async def process_queue(self):
        if self.queue.empty() or self.processing:
            return

        self.processing = True
        user, amount = await self.queue.get()

        try:
            for _ in range(amount):
                await self.generate_drop(user)

            self.db.add_shards(str(user.id), 20)
            self.queued_users.discard(user.id)

            async def notify_user_drop_complete(user):
                try:
                    dm = await user.create_dm()
                    embed = Templates.drop_success()
                    await dm.send(embed=embed)
                except nextcord.Forbidden:
                    print(f"Could not DM {user}.")

            asyncio.create_task(notify_user_drop_complete(user))

        finally:
            self.processing = False
            await asyncio.sleep(1)

    @process_queue.before_loop
    async def before_queue(self):
        await self.bot.wait_until_ready()

    @process_queue.error
    async def on_error(self, loop, context, exception):
        print(f"Queue error: {exception}")

def setup(bot):
    bot.add_cog(Drop(bot))
