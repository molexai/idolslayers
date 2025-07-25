import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = [1387525150752378940, 1389313345986756708, 1369853145827770368]

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(
        name="cardmute",
        description="Mute a user from receiving cards.",
        guild_ids=GUILD_ID
    )
    async def cardmute(
        self,
        interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name="user",
            description="The user you want to card mute.",
            required=True
        )
    ):
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if not (member.guild_permissions.administrator or member.guild_permissions.mute_members):
                embed = Templates.drop_error()
                embed.title = "`⋆｡ﾟ☁︎｡𖦹 Permission Denied ｡☁︎ﾟ｡⋆`"
                embed.description = "> You do not have permission to use this command."
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        if self.db.is_card_muted(str(user.id)):
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Uh-oh! Something went wrong...｡☁︎ﾟ｡⋆`"
            embed.description = f"{user.mention} is already card muted."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.db.card_mute(str(user.id))

        embed = Templates.drop_error()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 Card Mute ⋆｡ﾟ☁︎｡`"
        embed.description = f"Successfully card muted {user.mention}."
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="cardunmute",
        description="Unmute a user so they can receive cards again.",
        guild_ids=GUILD_ID,
    )
    async def cardunmute(
        self,
        interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name="user",
            description="The user you want to card unmute.",
            required=True
        )
    ):
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if not (member.guild_permissions.administrator or member.guild_permissions.mute_members):
                embed = Templates.drop_error()
                embed.title = "`⋆｡ﾟ☁︎｡𖦹 Permission Denied ｡☁︎ﾟ｡⋆`"
                embed.description = "> You do not have permission to use this command."
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        if not self.db.is_card_muted(str(user.id)):
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Uh-oh! Something went wrong...｡☁︎ﾟ｡⋆`"
            embed.description = f"{user.mention} is not card muted."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.db.card_unmute(str(user.id))

        embed = Templates.drop_error()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 Card Unmute ⋆｡ﾟ☁︎｡`"
        embed.description = f"Successfully card unmuted {user.mention}."
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="reset",
        description="Reset a user's data. (Admin only)",
        guild_ids=GUILD_ID,
    )
    async def reset(
        self,
        interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name="user",
            description="The user you want to reset.",
            required=True
        )
    ):
        if not interaction.guild or not interaction.guild.get_member(interaction.user.id).guild_permissions.administrator:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Permission Denied ｡☁︎ﾟ｡⋆`"
            embed.description = "> You do not have permission to use this command."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if user.id == self.bot.user.id:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Uh-oh! Something went wrong...｡☁︎ﾟ｡⋆`"
            embed.description = "You cannot reset the bot's data."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        db = Database()
        self.db.remove_all_characters(str(user.id))
        self.db.update_user(str(user.id), {
            "shards": 0,
            "cards": [],
            "characters": [],
            "card_mute": db.card_mute_status(str(user.id)),
        })

        embed = Templates.drop_error()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 User Reset ⋆｡ﾟ☁︎｡`"
        embed.description = f"{user.mention}'s data has been successfully reset."
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Utils(bot))
