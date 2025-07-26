from nextcord.ext import commands
from nextcord import Interaction
import nextcord

from SAJAX.bot import TARGET_USER_ID
from SAJAX.database import Database

from nextcord.ext import commands
from nextcord import Interaction
import nextcord

from SAJAX.database import Database

GUILD_ID = [1387525150752378940]

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(name="ping", description="Give all users +1 card reroll", guild_ids=GUILD_ID)
    async def ping(self, interaction: Interaction):
        if interaction.user.id != TARGET_USER_ID:
            embed = nextcord.Embed(
                title="Permission Denied",
                description="You do not have permission to use this command.",
                color=nextcord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        added_count = self.db.add_card_reroll_to_all_users()
        await interaction.response.send_message(
            f"✅ Successfully added `1x card reroll` to **{added_count}** users.", ephemeral=True
        )

def setup(bot):
    bot.add_cog(Ping(bot))
