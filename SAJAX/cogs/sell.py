import json
import os

import nextcord
from nextcord.ext import commands
from nextcord import SlashOption, Interaction, SelectOption
from nextcord.ui import View, Select, button
from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = [1387525150752378940, 1389313345986756708]

class SellCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(
        name="sell",
        description="Sell a character from your SAJAX cards!",
        guild_ids=GUILD_ID,
    )
    async def sell(self, interaction: Interaction,
                   character_name: str = SlashOption(description="Name of the character")):
        user_id = str(interaction.user.id)

        if self.db.is_on_cooldown(user_id, cooldown=5):
            return await interaction.response.send_message(embed=Templates.sell_cooldown(), ephemeral=True)

        user_data = self.db.get_user(user_id) or {}
        chars = user_data.get("characters", [])

        character_name = character_name.strip().lower()
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
                        # Get char rarity and calculate shards
                        rarity = char.get("rarity")
                        if not rarity:
                            rarity = char.get("top_rarity", "Unknown")
                        rarities_path = os.path.join(os.path.dirname(__file__), "rarities.json")
                        with open(rarities_path, "r", encoding="utf-8") as f:
                            rarities_data = json.load(f)
                        # Map tier to shard worth
                        self.rarity_worth = {
                            rarity["tier"]: rarity["worth"] for rarity in rarities_data.get("rarities", [])
                        }
                        shards = self.rarity_worth.get(rarity, 10)  # Default to 10 if not found
                        self.db.add_shards(user_id, int(shards))
                        await i2.response.edit_message(embed=Templates.sell_success(shards), view=None)

                    @button(label="❌ No", style=nextcord.ButtonStyle.danger)
                    async def no(self, button, i2: Interaction):
                        await i2.response.edit_message(embed=Templates.sell_cancelled(), view=None)

                await ctx.response.edit_message(embed=Templates.sell_confirm(char), view=ConfirmView())

        view = View(timeout=60)
        view.add_item(CharacterSelect())

        await interaction.response.send_message(embed=Templates.sell_prompt(matching), view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(SellCog(bot))
