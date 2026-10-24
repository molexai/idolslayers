import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from SAJAX.database import Database
from SAJAX.templates import get_emoji, Templates


GUILD_ID = [1387525150752378940]
TARGET_USER_ID = 1152734418109206548

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(name="ping", description="Pong!", guild_ids=GUILD_ID)
    async def ping(self, interaction: Interaction):
        if interaction.user.id != TARGET_USER_ID:
            return await interaction.response.send_message(f"Pong! {get_emoji('makane_zoey')}", ephemeral=True)

        added_count = self.db.add_card_reroll_to_all_users()
        await interaction.response.send_message(
            f"✅ Successfully added `1x card reroll` to **{added_count}** users.", ephemeral=True
        )

    @nextcord.slash_command(name="test", description="Test!", guild_ids=GUILD_ID)
    async def test(self, interaction: Interaction):
        if interaction.user.id != TARGET_USER_ID:
            # make it display the output.png image
            return await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        # put in card details
        embed = Templates.card_details("LIMITED Combined Card", "R", "Jinu holds rumi", "Character", "https://cdn.discordapp.com/attachments/1398838656315162715/1402770694525423807/output.png?ex=68951f83&is=6893ce03&hm=ffb25c05d8f892ee0ee5ceb9aea4ae5ea1ea10730528891f41177ca1013f63bc&")
        embed.color = nextcord.Color(0xFF6F91)
        await interaction.response.send_message(embed=embed)
        

def setup(bot):
    bot.add_cog(Ping(bot))
