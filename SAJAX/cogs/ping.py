import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from SAJAX.database import Database
from SAJAX.templates import get_emoji

GUILD_ID = [1387525150752378940, 1369853145827770368]
TARGET_USER_ID = 1152734418109206548

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(name="ping", description="Give all users +1 card reroll", guild_ids=GUILD_ID)
    async def ping(self, interaction: Interaction):
        if interaction.user.id != TARGET_USER_ID:
            return await interaction.response.send_message(f"Pong! {get_emoji('makane_zoey')}", ephemeral=True)

        added_count = self.db.add_card_reroll_to_all_users()
        await interaction.response.send_message(
            f"✅ Successfully added `1x card reroll` to **{added_count}** users.", ephemeral=True
        )

def setup(bot):
    bot.add_cog(Ping(bot))
