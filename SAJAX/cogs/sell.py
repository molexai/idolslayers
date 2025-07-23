import json
import os
import time

import nextcord
from nextcord.ext import commands
from nextcord import SlashOption, Interaction, SelectOption, Embed, Color
from nextcord.ui import View, Select, button
from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = [1387525150752378940, 1389313345986756708]

class SellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        self.COOLDOWN_SECONDS = 5

    @nextcord.slash_command(
        name="sell",
        description="Sell a character from your SAJAX cards!",
        guild_ids=GUILD_ID,
    )
    async def sell(self, interaction: Interaction,
                   character: str = SlashOption(description="Name of the character")):
        user = interaction.user
        user_id = str(user.id)
        now = time.time()
        last_used = self.cooldowns.get(user.id, 0)

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

        options = [
            SelectOption(
                label=f"{i+1}. {c['name']}",
                description=f"Rarity: {c.get('rarity', c.get('top_rarity','?'))}",
                value=str(i)
            )
            for i, c in enumerate(matching)
        ]

        class CharacterSelect(Select):
            def __init__(self):
                super().__init__(
                    placeholder="Select which character to sell…",
                    min_values=1,
                    max_values=1,
                    options=options
                )

            async def callback(self, ctx: Interaction):
                idx = int(self.values[0])
                char = matching[idx]

                class ConfirmView(View):
                    def __init__(self):
                        super().__init__()
                        self.rarity_worth = None
                        self.db = Database()

                    @button(label="✅ Yes", style=nextcord.ButtonStyle.success)
                    async def yes(self, button, i2: Interaction):
                        self.db.remove_character_and_card(user_id, char)
                        rarity = char.get("rarity", char.get("top_rarity", "Unknown"))

                        rarities_path = os.path.join(os.path.dirname(__file__), "rarities.json")
                        with open(rarities_path, "r", encoding="utf-8") as f:
                            rarities_data = json.load(f)

                        self.rarity_worth = {
                            rarity_data["tier"]: rarity_data["worth"]
                            for rarity_data in rarities_data.get("rarities", [])
                        }

                        shards = self.rarity_worth.get(rarity, 10)
                        self.db.add_shards(user_id, int(shards))
                        await i2.response.edit_message(embed=Templates.sell_success(shards), view=None)

                    @button(label="❌ No", style=nextcord.ButtonStyle.danger)
                    async def no(self, button, i2: Interaction):
                        await i2.response.edit_message(embed=Templates.sell_cancelled(), view=None)

                await ctx.response.edit_message(embed=Templates.sell_confirm(char), view=ConfirmView())

        view = View(timeout=60)
        view.add_item(CharacterSelect())

        await interaction.response.send_message(embed=Templates.sell_prompt(matching), view=view, ephemeral=True)

    @nextcord.slash_command(
        name="sellall",
        description="Sell all your characters at once!",
        guild_ids=GUILD_ID
    )
    async def sellall(self, interaction: Interaction):
        user = interaction.user
        user_id = str(user.id)
        now = time.time()
        last_used = self.cooldowns.get(user.id, 0)

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
            def __init__(self):
                super().__init__()
                self.db = Database()

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

        await interaction.response.send_message(embed=confirm_embed, view=ConfirmSellAll(), ephemeral=True)



def setup(bot):
    bot.add_cog(SellCog(bot))
