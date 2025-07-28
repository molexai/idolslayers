import json
import os
import time

import nextcord
from nextcord import SlashOption, Interaction, SelectOption
from nextcord.ext import commands
from nextcord.ui import View, Select, button, Button

from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = 1369853145827770368

class SellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        self.COOLDOWN_SECONDS = 5

    @nextcord.slash_command(
        name="sell",
        description="Sell a character from your SAJAX cards!",
        guild_ids=[GUILD_ID],
    )
    async def sell(self, interaction: Interaction,
                   character: str = SlashOption(description="Name of the character")):
        user = interaction.user
        user_id = str(user.id)
        if self.db.is_card_muted(str(user_id)):
            embed = Templates.card_muted()
            embed.description = f"> You are card muted and cannot view your cards."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        now = time.time()
        last_used = self.cooldowns.get(user.id, 0)
        if interaction.guild and interaction.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.COOLDOWN_SECONDS:
            remaining = round(self.COOLDOWN_SECONDS - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.cooldowns[user.id] = now

        user_data = self.db.get_user(user_id) or {}
        chars = user_data.get("characters", [])

        character_name = character.strip().lower()
        matching = [c for c in chars if c.get("name", "").strip().lower() == character_name]

        if not matching:
            return await interaction.response.send_message(embed=Templates.sell_no_character(character_name),
                                                           ephemeral=True)

        class PaginatedSelect(View):
            def __init__(self, db, user_id, matching_chars):
                super().__init__(timeout=60)
                self.db = db
                self.user_id = user_id
                self.matching_chars = matching_chars
                self.page = 0
                self.options_per_page = 25
                self.max_page = (len(matching_chars) - 1) // self.options_per_page if matching_chars else 0

                options = self.get_options()
                if not options:
                    options = [
                        SelectOption(
                            label="No characters available",
                            description="",
                            value="none",
                            default=True
                        )
                    ]
                    self.select = Select(
                        placeholder="No characters to select",
                        min_values=0,
                        max_values=0,
                        options=options,
                        disabled=True
                    )
                else:
                    self.select = Select(
                        placeholder="Select which character to sell…",
                        min_values=1,
                        max_values=1,
                        options=options
                    )
                self.add_item(self.select)

                self.prev_button = Button(label="Previous", style=nextcord.ButtonStyle.blurple, disabled=True)
                self.next_button = Button(label="Next", style=nextcord.ButtonStyle.blurple, disabled=(self.max_page == 0))
                self.add_item(self.prev_button)
                self.add_item(self.next_button)

                self.prev_button.callback = self.prev_page
                self.next_button.callback = self.next_page
                self.select.callback = self.select_callback

            def get_options(self):
                start = self.page * self.options_per_page
                end = start + self.options_per_page
                slice_chars = self.matching_chars[start:end]

                options = [
                    SelectOption(
                        label=f"{start + i + 1}. {c['name']}",
                        description=f"Rarity: {c.get('rarity', c.get('top_rarity', '?'))}",
                        value=str(start + i)
                    )
                    for i, c in enumerate(slice_chars)
                ]
                return options

            async def update_select(self, interaction: Interaction):
                options = self.get_options()
                if not options:
                    self.select.options = []
                    self.select.disabled = True
                    self.prev_button.disabled = True
                    self.next_button.disabled = True
                else:
                    self.select.options = options
                    self.select.disabled = False
                    self.prev_button.disabled = self.page == 0
                    self.next_button.disabled = self.page == self.max_page
                await interaction.response.edit_message(view=self)

            async def prev_page(self, interaction: Interaction):
                if self.page > 0:
                    self.page -= 1
                    await self.update_select(interaction)

            async def next_page(self, interaction: Interaction):
                if self.page < self.max_page:
                    self.page += 1
                    await self.update_select(interaction)

            async def select_callback(self, interaction: Interaction):
                select = self.select
                if select.values[0] == "none":
                    await interaction.response.defer()
                    return

                idx = int(select.values[0])
                user_data = self.db.get_user(self.user_id) or {}
                current_chars = user_data.get("characters", [])

                char = None
                if idx < len(self.matching_chars):
                    candidate = self.matching_chars[idx]
                    for c in current_chars:
                        if c.get("name") == candidate.get("name") and c.get("rarity", c.get("top_rarity", None)) == candidate.get("rarity", candidate.get("top_rarity", None)):
                            char = candidate
                            break

                if not char:
                    await interaction.response.edit_message(embed=Templates.sell_no_character("selected character"),
                                                            view=None)
                    return

                class ConfirmView(View):
                    def __init__(self, db, user_id):
                        super().__init__()
                        self.rarity_worth = None
                        self.db = db
                        self.user_id = user_id

                    @button(label="✅ Yes", style=nextcord.ButtonStyle.success)
                    async def yes(self, button, i2: Interaction):
                        user_data_check = self.db.get_user(self.user_id) or {}
                        chars_check = user_data_check.get("characters", [])
                        found = False
                        for c in chars_check:
                            if c.get("name") == char.get("name") and c.get("rarity", c.get("top_rarity", None)) == char.get("rarity", char.get("top_rarity", None)):
                                found = True
                                break

                        if not found:
                            await i2.response.edit_message(embed=Templates.sell_no_character("selected character"),
                                                          view=None)
                            return

                        self.db.remove_character_and_card(self.user_id, char)
                        rarity = char.get("rarity", char.get("top_rarity", "Unknown"))

                        rarities_path = os.path.join(os.path.dirname(__file__), "rarities.json")
                        with open(rarities_path, "r", encoding="utf-8") as f:
                            rarities_data = json.load(f)

                        self.rarity_worth = {
                            rarity_data["tier"]: rarity_data["worth"]
                            for rarity_data in rarities_data.get("rarities", [])
                        }

                        shards = self.rarity_worth.get(rarity, 10)
                        self.db.add_shards(self.user_id, int(shards))
                        await i2.response.edit_message(embed=Templates.sell_success(shards), view=None)

                    @button(label="❌ No", style=nextcord.ButtonStyle.danger)
                    async def no(self, button, i2: Interaction):
                        await i2.response.edit_message(embed=Templates.sell_cancelled(), view=None)

                await interaction.response.edit_message(embed=Templates.sell_confirm(char),
                                                        view=ConfirmView(self.db, self.user_id))

        view = PaginatedSelect(self.db, user_id, matching)
        await interaction.response.send_message(embed=Templates.sell_prompt(matching), view=view, ephemeral=True)

    @nextcord.slash_command(
        name="sellall",
        description="Sell all your characters at once!",
        guild_ids=[GUILD_ID]
    )
    async def sellall(self, interaction: Interaction):
        user = interaction.user
        user_id = str(user.id)
        if self.db.is_card_muted(str(user_id)):
            embed = Templates.card_muted()
            embed.description = f"> You are card muted and cannot view your cards."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        now = time.time()
        last_used = self.cooldowns.get(user.id, 0)
        if interaction.guild and interaction.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.COOLDOWN_SECONDS:
            remaining = round(self.COOLDOWN_SECONDS - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.cooldowns[user.id] = now

        user_data = self.db.get_user(user_id) or {}
        characters = user_data.get("characters", [])

        if not characters:
            embed = Templates.sell_no_character("any")
            embed.description = f"> You don't have any characters to sell."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        class ConfirmSellAll(View):
            def __init__(self, db):
                super().__init__()
                self.db = db

            @button(label="✅ Yes", style=nextcord.ButtonStyle.success)
            async def confirm(self, button, i2: Interaction):
                rarities_path = os.path.join(os.path.dirname(__file__), "rarities.json")
                with open(rarities_path, "r", encoding="utf-8") as f:
                    rarities_data = json.load(f)

                rarity_worth = {
                    r["tier"]: r["worth"]
                    for r in rarities_data.get("rarities", [])
                }

                total = 0
                for char in characters:
                    rarity = char.get("rarity", char.get("top_rarity", "Unknown"))
                    total += rarity_worth.get(rarity, 10)

                self.db.remove_all_characters(user_id)
                self.db.add_shards(user_id, total)

                await i2.response.edit_message(embed=Templates.sell_all_success(total), view=None)

            @button(label="❌ No", style=nextcord.ButtonStyle.danger)
            async def cancel(self, button, i2: Interaction):
                await i2.response.edit_message(embed=Templates.sell_cancelled(), view=None)

        confirm_embed = Templates.sell_all_confirm()

        await interaction.response.send_message(embed=confirm_embed, view=ConfirmSellAll(self.db), ephemeral=True)

def setup(bot):
    bot.add_cog(SellCog(bot))
