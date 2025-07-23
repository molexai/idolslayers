from lib2to3.pgen2.tokenize import group

import nextcord
from nextcord.ext import commands, tasks
from nextcord import SlashOption, Interaction, ButtonStyle
from nextcord.ui import View, button
import asyncio
import time

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
        embed = self.templates.card_details(name, rarity, description, group)
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

    def cog_unload(self):
        self.process_queue.cancel()

    @nextcord.slash_command(
        name="mycards",
        description="View your SAJAX cards!",
        guild_ids=GUILD_ID
    )
    async def mycards(self, ctx: Interaction):
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
                default=3
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
            dm = await user.create_dm()
            for i in range(amount):
                character, rarity = await self.generate_drop_return_card(user)

                embed = Templates.drop_summon()
                embed.title = f"SAJAX Admin Drop #{i + 1}"
                embed.description = f"You pulled a {rarity} character: {character['name']}"
                await dm.send(embed=embed)

                await asyncio.sleep(1)
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
        rarity = formatted_rarity[formatted_drop["rarity"]]

        print(f"{user}, You pulled a {rarity} character: {character['name']}")

        character_with_rarity = character.copy()
        character_with_rarity["rarity"] = formatted_drop["rarity"]

        self.db.add_character(user_id_str, character_with_rarity)
        self.db.add_card(user_id_str, character["character_id"])

        return f"You pulled a {rarity} character: {character['name']}"

    async def generate_drop_return_card(self, user):
        from SAJAX.selection import select_random_character

        user_id_str = str(user.id)
        if not self.db.get_user(user_id_str):
            self.db.insert_user(user_id_str)

        formatted_drop = select_random_character()
        formatted_rarity = {"B": "Balanced", "A": "Amazing", "R": "Rare", "UR": "Ultra Rare"}

        character = formatted_drop["character"]
        rarity = formatted_rarity[formatted_drop["rarity"]]

        character_with_rarity = character.copy()
        character_with_rarity["rarity"] = formatted_drop["rarity"]

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
            drops = []
            for i in range(amount):
                desc = await self.generate_drop(user)
                embed = Templates.drop_summon()
                embed.title = f"SAJAX Drop Summon #{i + 1}"
                embed.description = desc
                drops.append(embed)

            self.queued_users.discard(user.id)

            async def send_drops_later(user, drops):
                try:
                    self.db.add_shards(str(user.id), 20)
                    dm = await user.create_dm()
                    for embed in drops:
                        await dm.send(embed=embed)
                        await asyncio.sleep(1)
                except nextcord.Forbidden:
                    print(f"Could not DM {user}.")

            self.db.add_shards(str(user.id), 20)
            asyncio.create_task(send_drops_later(user, drops))

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
