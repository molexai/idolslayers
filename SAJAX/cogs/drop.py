from nextcord.ext import commands
import nextcord
from nextcord import SlashOption, Interaction, ButtonStyle
from nextcord.ui import View, button, Button, Select
import asyncio
import time
import random
import json
import os

from SAJAX.database import Database
from SAJAX.templates import Templates, get_emoji

GUILD_ID = 1369853145827770368

class CardPageView(View):
    def __init__(self, user_cards, templates, owner_id, db: Database, timeout=180):
        super().__init__(timeout=timeout)
        self.cards = user_cards
        self.index = 0
        self.templates = templates
        self.owner_id = owner_id
        self.db = db
        self.displayed_cards = set()
        self.update_buttons()

        self.user_enabled_items = self.db.get_enabled_items(str(owner_id)) or []
        self.has_reroll = "card_reroll" in self.user_enabled_items

        if self.has_reroll:
            reroll_button = Button(label="Reroll", style=ButtonStyle.red)
            reroll_button.callback = self.reroll_callback
            self.add_item(reroll_button)

    def update_buttons(self):
        for child in self.children:
            if isinstance(child, Button):
                if child.label == "Previous":
                    child.disabled = self.index == 0
                elif child.label == "Next":
                    child.disabled = self.index == len(self.cards) - 1
                elif child.custom_id == "display_card":
                    child.disabled = self.index in self.displayed_cards

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

    @button(label="Skip to Page", style=ButtonStyle.gray)
    async def skip_to_page(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You can't use this button.", ephemeral=True)
            return

        await interaction.response.send_modal(SkipPageModal(self))

    @button(label="Display", style=ButtonStyle.green, custom_id="display_card")
    async def display(self, button: Button, interaction: Interaction):
        card = self.cards[self.index]
        self.displayed_cards.add(self.index)
        button.disabled = True
        self.update_buttons()
        await interaction.response.edit_message(view=self)
        name = card.get('name', 'Unknown')
        rarity = card.get('rarity', card.get('top_rarity', 'Unknown'))
        description = card.get('description', 'No description available.').replace('â€™', "")
        group = card.get('group', 'Unknown')
        embed = self.templates.card_details(name, rarity, description, group, card.get('thumbnail_url'))
        embed.set_footer(text=f"Card {self.index + 1} of {len(self.cards)}")
        owner_mention = f"<@{self.owner_id}>"
        await interaction.channel.send(f"> {Templates.pastel_emojis[5]} **Card displayed by {owner_mention}:**", embed=embed)

    async def reroll_callback(self, interaction: Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You can't use this reroll button.", ephemeral=True)
            return

        for child in self.children:
            if isinstance(child, Button) and child.label == "Reroll":
                child.disabled = True
        await interaction.response.edit_message(view=self)

        user_id_str = str(self.owner_id)
        old_card = self.cards[self.index]

        self.db.remove_character_and_card(user_id_str, old_card)

        new_card, rarity_str = await self.generate_drop_return_card(interaction.user)

        self.cards[self.index] = new_card

        enabled_items = self.db.get_enabled_items(user_id_str) or []
        if "card_reroll" in enabled_items:
            enabled_items.remove("card_reroll")
            self.db.update_user(user_id_str, {"enabled_items": enabled_items})

            embed = Templates.drop_success()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Card Rerolled! ｡☁︎ﾟ｡⋆`"
            embed.description = (
                f"> {Templates.pastel_emojis[5]} <@{self.owner_id}>, your card has been rerolled!"
                f"\nNew card: **{new_card.get('name', 'Unknown')}** with rarity **{rarity_str}**."
                "\nUse `/mycards` to view it."
            )
            embed.set_image(url=new_card.get('thumbnail_url', ''))
            print(f"[reroll] User {user_id_str} rerolled card {old_card.get('name', 'Unknown')} to {new_card.get('name', 'Unknown')}")
            await interaction.channel.send(embed=embed)
        else:
            embed = Templates.drop_error()
            embed.description = "> You do not have the Card Rerolls item enabled."
            await interaction.channel.send(embed=embed)
            return

        self.clear_items()
        self.update_buttons()
        self.add_item(Button(label="Previous", style=ButtonStyle.blurple, disabled=self.index == 0))
        self.add_item(Button(label="Next", style=ButtonStyle.blurple, disabled=self.index == len(self.cards) - 1))
        display_btn = Button(label="Display", style=ButtonStyle.green, custom_id="display_card", disabled=False)
        self.add_item(display_btn)

        async def display_callback(button_interaction: Interaction):
            card = self.cards[self.index]
            display_btn.disabled = True
            await button_interaction.response.edit_message(view=self)
            name = card.get('name', 'Unknown')
            rarity = card.get('rarity', card.get('top_rarity', 'Unknown'))
            description = card.get('description', 'No description available.').replace('â€™', "")
            group = card.get('group', 'Unknown')
            embed_display = self.templates.card_details(name, rarity, description, group, card.get('thumbnail_url'))
            embed_display.set_footer(text=f"Card {self.index + 1} of {len(self.cards)}")
            owner_mention = f"<@{self.owner_id}>"
            await button_interaction.channel.send(f"> {Templates.pastel_emojis[5]} **Card displayed by {owner_mention}:**", embed=embed_display)
        display_btn.callback = display_callback

        await interaction.edit_original_message(embed=self.generate_embed(), view=self)

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

    def assign_thumbnail(self, character_name: str, rarity: str) -> str:
        with open(os.path.join(os.path.dirname(__file__), "characters_card_images.json"), "r", encoding="utf-8") as file:
            data = json.load(file)
        for character in data["characters"]:
            if character["name"].lower() == character_name.lower():
                for rarity_block in character["rarities"]:
                    if rarity_block["rarity"].upper() == rarity.upper():
                        urls = [url for key, url in rarity_block.items() if key.startswith("image_url_") and url.strip()]
                        if not urls:
                            return ""
                        random.shuffle(urls)
                        return random.choice(urls)
        return ""

class SkipPageModal(nextcord.ui.Modal):
    def __init__(self, view: CardPageView):
        super().__init__(
            "Skip to Page",
            timeout=60
        )
        self.view = view
        self.page_input = nextcord.ui.TextInput(
            label="Enter page number (1 to {})".format(len(self.view.cards)),
            placeholder="e.g. 5",
            min_length=1,
            max_length=4,
            required=True
        )
        self.add_item(self.page_input)

    async def callback(self, interaction: Interaction):
        try:
            page = int(self.page_input.value.strip())
            if not (1 <= page <= len(self.view.cards)):
                raise ValueError()
        except ValueError:
            error_embed = Templates.drop_error()
            error_embed.description = f"> Invalid input. Please enter a number between **1** and **{len(self.view.cards)}**."
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        self.view.index = page - 1
        self.view.update_buttons()
        await interaction.response.edit_message(embed=self.view.generate_embed(), view=self.view)


class CardSelect(Select):
    def __init__(self, cards, templates, owner_id):
        options = [
            nextcord.SelectOption(
                label=card.get('name', 'Unknown'),
                description=f"Rarity: {card.get('rarity', card.get('top_rarity', 'Unknown'))}",
                value=str(i)
            )
            for i, card in enumerate(cards[:25])
        ]
        super().__init__(placeholder="Select a card to view details...", min_values=1, max_values=1, options=options)
        self.cards = cards
        self.templates = templates
        self.owner_id = owner_id
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
        view = View(timeout=180)
        view.displayed_cards = set()
        view.add_item(self)
        display_button = Button(label="Display", style=ButtonStyle.green, custom_id="display_card")

        async def display_callback(button_interaction: Interaction):
            display_button.disabled = True
            view.displayed_cards.add(index)
            await button_interaction.response.edit_message(view=view)
            owner_mention = f"<@{self.owner_id}>"
            embed_display = self.templates.card_details(name, rarity, description, group, card.get('thumbnail_url'))
            embed_display.set_footer(text=f"Card details for {name}")
            await button_interaction.channel.send(f"> {Templates.pastel_emojis[5]} **Card displayed by {owner_mention}:**", embed=embed_display)

        display_button.callback = display_callback
        if index in view.displayed_cards:
            display_button.disabled = True
        view.add_item(display_button)
        await interaction.response.edit_message(embed=embed, view=view)

class CardMenuView(View):
    def __init__(self, cards, templates, owner_id, timeout=180):
        super().__init__(timeout=timeout)
        self.select = CardSelect(cards, templates, owner_id)
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
        self.cooldowns = {}
        self.COOLDOWN_SECONDS = 3600
        self.locks = {}
        self.mycards_cooldowns = {}
        self.MYCARDS_COOLDOWN = 10
        self.myshards_cooldowns = {}
        self.MYSHARDS_COOLDOWN = 5
        self.db = Database()
        self.json_path = os.path.join(os.path.dirname(__file__), "characters_card_images.json")
        self.characters_json_path = os.path.join(os.path.dirname(__file__), "characters.json")

    def assign_thumbnail(self, character_name: str, rarity: str) -> str:
        with open(self.json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        for character in data["characters"]:
            if character["name"].lower() == character_name.lower():
                for rarity_block in character["rarities"]:
                    if rarity_block["rarity"].upper() == rarity.upper():
                        urls = [url for key, url in rarity_block.items() if key.startswith("image_url_") and url.strip()]
                        if not urls:
                            return ""
                        random.shuffle(urls)
                        return random.choice(urls)
        return ""

    @nextcord.slash_command(name="mycards", description="View your SAJAX cards!", guild_ids=[GUILD_ID])
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

        if self.db.is_card_muted(str(user.id)):
            embed = Templates.card_muted()
            embed.description = f"> You are card muted and cannot view your cards."
            await ctx.send(embed=embed, ephemeral=True)
            return

        now = time.time()
        last_used = self.mycards_cooldowns.get(user.id, 0)
        if ctx.guild and ctx.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

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
            view = CardMenuView(cards, Templates, user.id)
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
            view = CardPageView(cards, Templates, user.id, self.db)
            await ctx.send(embed=view.generate_embed(), view=view, ephemeral=True)


    @nextcord.slash_command(name="myshards", description="View your current shard count", guild_ids=[GUILD_ID])
    async def myshards(self, ctx: Interaction):
        user = ctx.user

        if self.db.is_card_muted(str(user.id)):
            embed = Templates.card_muted()
            embed.description = f"> You are card muted and cannot view your shards."
            await ctx.send(embed=embed, ephemeral=True)
            return

        now = time.time()
        last_used = self.myshards_cooldowns.get(user.id, 0)
        if ctx.guild and ctx.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.MYSHARDS_COOLDOWN:
            remaining = round(self.MYSHARDS_COOLDOWN - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            await ctx.send(embed=embed, ephemeral=True)
            return
        self.myshards_cooldowns[user.id] = now
        shards = self.db.get_shards(str(user.id))
        embed = Templates.drop_success()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 Your Shards ｡☁︎ﾟ｡⋆`"
        embed.description = f"> You currently have **{shards}** shards."
        return await ctx.send(embed=embed, ephemeral=True)

    async def fast_drop(self, user):
        """
        Fast drop method to generate cards without queue delays or cooldown skips.
        Used for drop_queue_priority users.
        """
        user_id_str = str(user.id)
        user_enabled_items = self.db.get_enabled_items(user_id_str) or []

        drop_amount = 3
        base_shard_amount = 20

        if "drop_booster" in user_enabled_items:
            drop_amount += random.choice([1, 2])
            user_enabled_items.remove("drop_booster")
        self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})

        shard_amount = base_shard_amount * 2 if "shard_multiplier" in user_enabled_items else base_shard_amount

        if "shard_multiplier" in user_enabled_items:
            user_enabled_items.remove("shard_multiplier")
            self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})

        print(
            f"[fast_drop] user: {user_id_str}, drop_amount: {drop_amount}, shard_amount: {shard_amount}, items: {user_enabled_items}")

        if user.id not in self.locks:
            self.locks[user.id] = asyncio.Lock()

        async with self.locks[user.id]:
            for _ in range(drop_amount):
                await self.generate_drop(user)

            self.db.add_shards(user_id_str, shard_amount)

    @nextcord.slash_command(name="drop", description="Summon your next SAJAX cards with this command!",
                            guild_ids=[GUILD_ID])
    async def drop(self, interaction: Interaction):
        global double_drop_activated_embed, drop_booster_embed, shard_muliplier_embed
        user = interaction.user
        user_id_str = str(user.id)
        user_enabled_items = self.db.get_enabled_items(user_id_str) or []

        if self.db.is_card_muted(user_id_str):
            embed = Templates.card_muted()
            embed.description = "> You are card muted and cannot view your cards."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        now = time.time()
        last_used = self.cooldowns.get(user.id, 0)
        if interaction.guild and interaction.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        cooldown_time = self.COOLDOWN_SECONDS
        if "drop_cooldown_reducer" in user_enabled_items:
            cooldown_time = cooldown_time // 2
            user_enabled_items.remove("drop_cooldown_reducer")
        self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})


        if now - last_used < cooldown_time:
            remaining = int(cooldown_time - (now - last_used))
            mins, secs = divmod(remaining, 60)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {mins}m {secs}s."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.cooldowns[user.id] = now

        if "drop_queue_priority" in user_enabled_items:
            await self.fast_drop(user)
            embed = Templates.drop_success()
            embed.description = (
                f"> {Templates.pastel_emojis[5]} <@{user.id}>, cards have been summoned instantly due to your **Drop Queue Priority**!"
                "\nUse `/mycards` to view them."
            )
            await interaction.response.send_message(embed=embed)
            user_enabled_items.remove("drop_queue_priority")
            self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})
            return

        embed = Templates.drop_summon()
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if user.id not in self.locks:
            self.locks[user.id] = asyncio.Lock()

        drop_amount = 3
        base_shard_amount = 20
        double_drop = False
        drop_booster = False
        shard_muliplier = False

        shard_amount = base_shard_amount * 2 if "shard_multiplier" in user_enabled_items else base_shard_amount

        if "shard_multiplier" in user_enabled_items:
            user_enabled_items.remove("shard_multiplier")
            self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})
            shard_muliplier = True
            if shard_muliplier:
                shard_muliplier_embed = Templates.drop_success()
                shard_muliplier_embed.description = (
                    f"> {Templates.pastel_emojis[5]} <@{user.id}>, your **Shard Multiplier** activated!"
                    f"\nYou received **{shard_amount}**{get_emoji('shard_non_pink')}"
                )
                shard_muliplier_embed.title = "`⋆｡ﾟ☁︎｡𖦹 Shard Multiplier Activated! ｡☁︎ﾟ｡⋆`"
                shard_muliplier_embed.color = nextcord.Color.from_rgb(255, 182, 193)


        if "double_drop_chance" in user_enabled_items:
            # 75% chance to double the drop amount
            if random.random() < 0.75:
                print(f"[double_drop] User {user_id_str} activated double drop chance!")
                drop_amount *= 2
                shard_amount *= 2
                user_enabled_items.remove("double_drop_chance")
                self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})
                double_drop = True

                double_drop_activated_embed = Templates.drop_success()
                if double_drop:
                    double_drop_activated_embed.description = (
                        f"> {Templates.pastel_emojis[5]} <@{user.id}>, your **Double Drop Chance** activated!"
                        f"\nYou received **{shard_amount}** shards and **{drop_amount}** cards!"
                    )
                    double_drop_activated_embed.title = "`⋆｡ﾟ☁︎｡𖦹 Double Drop Activated! ｡☁︎ﾟ｡⋆`"
                    double_drop_activated_embed.color = nextcord.Color.from_rgb(255, 105, 180)

        if "drop_booster" in user_enabled_items:
            drop_amount += random.choice([1, 2])
            drop_booster = True
            print(f"[normal_drop] User {user_id_str} has Drop Booster enabled, increasing drop amount to {drop_amount}.")
            user_enabled_items.remove("drop_booster")

            if drop_booster:
                drop_booster_embed = Templates.drop_success()
                drop_booster_embed.description = (
                    f"> {Templates.pastel_emojis[5]} <@{user.id}>, your **Drop Booster** activated!"
                    f"\nYou received **{drop_amount}** cards!"
                )
                drop_booster_embed.title = "`⋆｡ﾟ☁︎｡𖦹 Drop Booster Activated! ｡☁︎ﾟ｡⋆`"
                drop_booster_embed.color = nextcord.Color.from_rgb(255, 165, 0) #

        self.db.update_user(user_id_str, {"enabled_items": user_enabled_items})

        print(
            f"[normal_drop] user: {user_id_str}, drop_amount: {drop_amount}, shard_amount: {shard_amount}, items: {user_enabled_items}")

        async with self.locks[user.id]:
            for _ in range(drop_amount):
                await self.generate_drop(user)

            self.db.add_shards(user_id_str, shard_amount)

            response_embed = Templates.drop_success()
            response_embed.description = (
                f"> {Templates.pastel_emojis[5]} <@{user.id}>, cards have been summoned!"
                "\nUse `/mycards` to view them. Enjoy!"
            )
            await interaction.followup.send(embed=response_embed)
            if double_drop:
                await interaction.followup.send(embed=double_drop_activated_embed)
            if drop_booster:
                await interaction.followup.send(embed=drop_booster_embed)
            if shard_muliplier:
                await interaction.followup.send(embed=shard_muliplier_embed)

    @nextcord.slash_command(
        name="addcard",
        description="Add a specific card to a user’s collection (Admin only)",
        guild_ids=[GUILD_ID],
    )
    async def addcard(
            self,
            interaction: nextcord.Interaction,
            character: str = SlashOption(description="Character name to add", required=True),
            rarity: str = SlashOption(
                description="Rarity of the character (B, A, R, UR)",
                required=True,
                choices={"B": "B", "A": "A", "R": "R", "UR": "UR"}
            ),
            target: nextcord.User = SlashOption(description="User to give the card to", required=False, default=None)
    ):
        user = target or interaction.user
        user_id_str = str(user.id)

        if not interaction.guild or not interaction.guild.get_member(interaction.user.id).guild_permissions.administrator:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Permission Denied ｡☁︎ﾟ｡⋆`"
            embed.description = "> You do not have permission to use this command."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            with open(self.characters_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Error Loading Characters ｡☁︎ﾟ｡⋆`"
            embed.description = "> Could not load characters data file."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        character = next((char for char in data if char.get("name", "").lower() == character.lower()), None)

        if not character:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Invalid Character ｡☁︎ﾟ｡⋆`"
            embed.description = f"> Could not find character with name `{character}`."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        thumbnail_url = self.assign_thumbnail(character.get("name", ""), rarity)

        character_data = character.copy()
        character_data["rarity"] = rarity
        if thumbnail_url:
            character_data["thumbnail_url"] = thumbnail_url

        if not self.db.get_user(user_id_str):
            self.db.insert_user(user_id_str)

        if self.db.is_card_muted(user_id_str):
            embed = Templates.card_muted()
            embed.description = f"> {user.mention} is card muted and cannot receive cards."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.db.add_character(user_id_str, character_data)
        self.db.add_card(user_id_str, character.get("character_id"))

        embed = Templates.drop_success()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 Card Added! ｡☁︎ﾟ｡⋆`"
        if user == interaction.user:
            embed.description = f"> Successfully added **{character.get('name', 'Unknown')}** ({rarity}) to your collection."
        else:
            embed.description = f"> Successfully added **{character.get('name', 'Unknown')}** ({rarity}) to {user.mention}'s collection."
        if thumbnail_url:
            embed.set_image(url=thumbnail_url)

        if target and target != interaction.user:
            try:
                dm = await target.create_dm()
                dm_embed = Templates.drop_success()
                dm_embed.title = "`⋆｡ﾟ☁︎｡𖦹 Card Added! ｡☁︎ﾟ｡⋆`"
                dm_embed.description = f"> You have received **{character.get('name', 'Unknown')}** ({rarity}) from {interaction.user.mention}."
                if thumbnail_url:
                    dm_embed.set_image(url=thumbnail_url)
                await dm.send(embed=dm_embed)
            except nextcord.Forbidden:
                print(f"Could not DM {target}.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="admindrop",
                            description="Admin-only version of drop that allows setting drop amount.",
                            guild_ids=[GUILD_ID])
    async def admin_drop(self, interaction: Interaction,
                         amount: int = SlashOption(description="Number of cards to summon", required=False,
                                                   default=10)):
        user = interaction.user

        if not interaction.guild or not interaction.guild.get_member(
                interaction.user.id).guild_permissions.administrator:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Permission Denied ｡☁︎ﾟ｡⋆`"
            embed.description = "> You do not have permission to use this command."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = Templates.drop_summon()
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if user.id not in self.locks:
            self.locks[user.id] = asyncio.Lock()

        async with self.locks[user.id]:
            for _ in range(amount):
                await self.generate_drop(user)

            embed_success = Templates.drop_success()
            embed_success.description = f"> {Templates.pastel_emojis[5]} <@{user.id}>, **{amount}** cards have been admin dropped!\nUse `/mycards` to view them."
            await interaction.followup.send(embed=embed_success)

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

def setup(bot):
    bot.add_cog(Drop(bot))