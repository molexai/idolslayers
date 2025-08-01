import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = 1369853145827770368

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @nextcord.slash_command(
        name="cardmute",
        description="Mute a user from receiving cards.",
        guild_ids=[GUILD_ID]
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
        guild_ids=[GUILD_ID],
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
        guild_ids=[GUILD_ID],
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

        self.db.remove_all_characters(str(user.id))
        self.db.remove_user(str(user.id))

        embed = Templates.drop_error()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 User Reset ⋆｡ﾟ☁︎｡`"
        embed.description = f"{user.mention}'s data has been successfully reset."
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="removeadvertisement",
        description="Remove a user's advertisement. (Admin only)",
        guild_ids=[GUILD_ID],
    )
    async def remove_advertisement(
        self,
        interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name="user",
            description="The user whose advertisement you want to remove.",
            required=True
        ),
        ad_id: str = SlashOption(
            name="ad_id",
            description="The ID of the advertisement to remove.",
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

        user_data = self.db.get_user(str(user.id))
        if not user_data or "ad_data" not in user_data:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 No Advertisements Found ｡☁︎ﾟ｡⋆`"
            embed.description = f"{user.mention} has no advertisements."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        ad_data = user_data["ad_data"]
        if ad_id is None:
            ad_id = ad_data[0]["ad_id"]
        ad_entry = next((ad for ad in ad_data if ad["ad_id"] == ad_id), None)
        if not ad_entry:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Not Found ｡☁︎ﾟ｡⋆`"
            embed.description = f"> No advertisement found with ID `{ad_id}` for {user.mention}."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            self.db.remove_advertisement(str(user.id), ad_id)

            channel = self.bot.get_channel(int(ad_entry["channel_id"]))
            if channel:
                try:
                    ad_message = await channel.fetch_message(int(ad_entry["message_id"]))
                    await ad_message.delete()
                except nextcord.NotFound:
                    pass
                except Exception as e:
                    print(f"Error deleting ad message: {e}")

            embed = Templates.drop_success()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Removed ｡☁︎ﾟ｡⋆`"
            embed.description = f"> Successfully **removed** advertisement with ID `{ad_id}` for {user.mention}."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Error Removing Advertisement ｡☁︎ﾟ｡⋆`"
            embed.description = f"> An error occurred while removing the advertisement: {str(e)}"
            return await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Utils(bot))
