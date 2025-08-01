import uuid
import nextcord
import time
from nextcord.ext import commands
from nextcord import SlashOption, Interaction

from SAJAX.database import Database
from SAJAX.templates import Templates, get_emoji

GUILD_ID = 1369853145827770368

def color_randomize():
    import random
    colors = {
        "pink": 0xFFB6C1,
        "blue": 0xADD8E6,
        "green": 0x90EE90,
        "yellow": 0xFFFFE0,
        "purple": 0xE6E6FA,
        "orange": 0xFFA07A,
        "teal": 0xAFEEEE,
        "lavender": 0xE6E6FA,
        "peach": 0xFFDAB9
    }
    return random.choice(list(colors.values()))

class Ads(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.createad_cooldowns = {}
        self.removead_cooldowns = {}
        self.listads_cooldowns = {}
        self.COOLDOWN_CREATEAD = 300  # 5 minutes
        self.COOLDOWN_REMOVEAD = 30   # 30 seconds
        self.COOLDOWN_LISTADS = 5    # 5 seconds

    @nextcord.slash_command(guild_ids=[GUILD_ID], description="Create a new advertisement.")
    async def createad(self, interaction: Interaction,
                       name: str = SlashOption(description="Name of the ad"),
                       price: str = SlashOption(description="Price of the ad"),
                       description: str = SlashOption(description="Description of the ad"),
                       image: str = SlashOption(description="Optional image URL", required=False)):
        now = time.time()

        # admins can bypass cooldowns
        if interaction.guild and interaction.guild.get_member(interaction.user.id).guild_permissions.administrator:
            last_used = 0
        else:
            last_used = self.createad_cooldowns.get(interaction.user.id, 0)
        if now - last_used < self.COOLDOWN_CREATEAD:
            remaining = int(self.COOLDOWN_CREATEAD - (now - last_used))
            mins, secs = divmod(remaining, 60)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {mins}m {secs}s."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.createad_cooldowns[interaction.user.id] = now
        await interaction.response.defer(ephemeral=True)

        if self.db.is_card_muted(str(interaction.user.id)):
            embed = Templates.card_muted()
            embed.description = "> You are card muted and cannot create advertisements."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        user_id = str(interaction.user.id)
        user_data = self.db.get_user(user_id)
        ad_maximum = user_data.get("ad_maximum", 5)
        global_maximum_ads_allowed = 20
        amount_of_ads = len(user_data.get("ad_data", []))

        # Apply increase first if possible
        if "advertisement_max_increase" in user_data.get("enabled_items", []) and amount_of_ads >= 3:
            if ad_maximum >= global_maximum_ads_allowed:
                embed = Templates.drop_error()
                embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Limit Reached ｡☁︎ﾟ｡⋆`"
                embed.description = (
                    f"> {Templates.pastel_emojis[1]} You have reached the maximum advertisement limit of **{global_maximum_ads_allowed}**.\n"
                    f"> You will not be able to increase your maximum advertise limit anymore. ♡"
                )
                user_data["enabled_items"].remove("advertisement_max_increase")
                self.db.update_user(user_id, user_data)
                await interaction.send(embed=embed, ephemeral=True)

            else:
                ad_maximum += 3
                user_data["ad_maximum"] = ad_maximum
                user_data["enabled_items"].remove("advertisement_max_increase")
                self.db.update_user(user_id, user_data)
                embed = Templates.drop_success()
                embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Limit Increased ｡☁︎ﾟ｡⋆`"
                embed.description = (
                    f"> {Templates.pastel_emojis[5]} <@{user_id}>, Your advertisement limit has been increased to **{ad_maximum}** ads.\n"
                    f"> You can now create more ads! ♡"
                )
                embed.color = color_randomize()
                embed.set_footer(text="Thank you for using SAJAX Ads!")
                await interaction.send(embed=embed, ephemeral=False)

        if "ad_data" not in user_data:
            user_data["ad_data"] = []

        if len(user_data["ad_data"]) >= ad_maximum or amount_of_ads >= global_maximum_ads_allowed:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Limit Reached ｡☁︎ﾟ｡⋆`"
            embed.description = (
                f"> {Templates.pastel_emojis[1]} You can only have up to **{ad_maximum}** ads at a time.\n"
                f"> Please **remove** an existing ad before creating a new one. ♡"
            )
            return await interaction.send(embed=embed, ephemeral=True)

        if isinstance(price, str):
            try:
                price = float(price)
            except ValueError:
                embed = Templates.drop_error()
                embed.title = "`⋆｡ﾟ☁︎｡𖦹 Invalid Price ｡☁︎ﾟ｡⋆`"
                embed.description = "> Please enter a valid number for the price."
                return await interaction.send(embed=embed, ephemeral=True)
        if price <= 0:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Invalid Price ｡☁︎ﾟ｡⋆`"
            embed.description = "> The price must be a positive number."
            return await interaction.send(embed=embed, ephemeral=True)

        if not name or len(name) > 50:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Invalid Advertisement Name ｡☁︎ﾟ｡⋆`"
            embed.description = "> Please provide a valid ad name (max 50 characters)."
            return await interaction.send(embed=embed, ephemeral=True)

        if description and len(description) > 800:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Description Too Long ｡☁︎ﾟ｡⋆`"
            embed.description = "> The description must be 800 characters or less."
            return await interaction.send(embed=embed, ephemeral=True)

        if image and not image.startswith(("http://", "https://")):
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Invalid Image URL ｡☁︎ﾟ｡⋆`"
            embed.description = "> Please provide a valid image URL starting with `http://` or `https://`."
            return await interaction.send(embed=embed, ephemeral=True)

        ad_id = str(uuid.uuid4())

        ad_embed = nextcord.Embed(
            title=f"`⋆｡ﾟ☁︎｡𖦹 {name} ｡☁︎ﾟ｡⋆`",
            description=f"> **{description}**" or "> **No description provided**.",
            color=color_randomize()
        )
        ad_embed.add_field(name="Price", value=f"**{str(price).replace('.0', '')}**{get_emoji('shard_non_pink')}", inline=True)
        ad_embed.add_field(name="Posted by", value=interaction.user.mention, inline=True)
        ad_embed.timestamp = nextcord.utils.utcnow()
        ad_embed.set_author(
            name=f"{interaction.user.name}'s Advertisement",
            icon_url=interaction.user.display_avatar.url
        )
        ad_embed.set_footer(
            text=f"",
            icon_url=interaction.user.display_avatar.url
        )
        ad_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        if image:
            ad_embed.set_image(url=image)

        ad_message = await interaction.channel.send(embed=ad_embed)

        user_data["ad_data"].append({
            "ad_name": name,
            "price": price,
            "ad_id": ad_id,
            "message_link": ad_message.jump_url,
            "channel_id": str(ad_message.channel.id),
            "message_id": str(ad_message.id)
        })

        self.db.update_user(str(interaction.user.id), user_data)

        success_embed = Templates.drop_success()
        success_embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Created ｡☁︎ﾟ｡⋆`"
        success_embed.description = f"> Your ad has been **created and posted** successfully!\n\n"
        success_embed.add_field(
            name="\n\nAd Details",
            value=f"> **Ad ID:** `{ad_id}`\n"
                  f"> **Message Link:** [Click Here]({ad_message.jump_url})",
            inline=False
        )

        success_embed.color = nextcord.Color.green()
        return await interaction.send(embed=success_embed, ephemeral=True)

    @nextcord.slash_command(guild_ids=[GUILD_ID], description="List all your advertisements.")
    async def listads(self, interaction: Interaction):
        now = time.time()
        # admins can bypass cooldowns
        if interaction.guild and interaction.guild.get_member(interaction.user.id).guild_permissions.administrator:
            last_used = 0
        else:
            last_used = self.listads_cooldowns.get(interaction.user.id, 0)
        if now - last_used < self.COOLDOWN_LISTADS:
            remaining = round(self.COOLDOWN_LISTADS - (now - last_used))
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.send(embed=embed, ephemeral=True)
        self.listads_cooldowns[interaction.user.id] = now

        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        if self.db.is_card_muted(str(user_id)):
            embed = Templates.card_muted()
            embed.description = "> You are card muted and cannot view your advertisements."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        user_data = self.db.get_user(str(interaction.user.id))
        ad_data = user_data.get("ad_data", [])

        if not ad_data:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 No Advertisements Found ｡☁︎ﾟ｡⋆`"
            embed.description = "> You haven't created any ads yet. Use `/createad` to get started!"
            return await interaction.send(embed=embed, ephemeral=True)

        list_embed = nextcord.Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Your Advertisements ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[5]} Here are your **current advertisements**:",
            color=color_randomize()
        )

        for ad in ad_data:
            list_embed.add_field(
                name=f"{get_emoji('shard_non_pink')} {ad['ad_name']}",
                value=f"> **Ad ID:** `{ad['ad_id']}`\n> **Message Link:** [Click Here]({ad['message_link']})",
                inline=False
            )

        return await interaction.send(embed=list_embed, ephemeral=True)

    @nextcord.slash_command(guild_ids=[GUILD_ID], description="Remove one of your advertisements.")
    async def removead(self, interaction: Interaction,
                       ad_id: str = SlashOption(description="UUID of the ad you want to remove")):

        now = time.time()
        # admins can bypass cooldowns
        if interaction.guild and interaction.guild.get_member(interaction.user.id).guild_permissions.administrator:
            last_used = 0
        else:
            last_used = self.removead_cooldowns.get(interaction.user.id, 0)
        if now - last_used < self.COOLDOWN_REMOVEAD:
            remaining = round(self.COOLDOWN_REMOVEAD - (now - last_used))
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.send(embed=embed, ephemeral=True)
        self.removead_cooldowns[interaction.user.id] = now

        await interaction.response.defer(ephemeral=True)

        if self.db.is_card_muted(str(interaction.user.id)):
            embed = Templates.card_muted()
            embed.description = "> You are card muted and cannot remove advertisements."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        user_data = self.db.get_user(str(interaction.user.id))
        if not user_data or "ad_data" not in user_data:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 No Advertisements Found ｡☁︎ﾟ｡⋆`"
            embed.description = "> You haven't created any ads yet. Use `/createad` to get started!"
            return await interaction.send(embed=embed, ephemeral=True)

        ad_entry = next((ad for ad in user_data["ad_data"] if ad["ad_id"] == ad_id), None)

        if not ad_entry:
            embed = Templates.drop_error()
            embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Not Found ｡☁︎ﾟ｡⋆`"
            embed.description = f"> No advertisement found with ID `{ad_id}`.\n"
            return await interaction.send(embed=embed, ephemeral=True)

        try:
            msg_link = ad_entry["message_link"]
            parts = msg_link.split("/")
            guild = self.bot.get_guild(int(parts[-3]))
            channel = guild.get_channel(int(parts[-2]))
            msg = await channel.fetch_message(int(parts[-1]))
            await msg.delete()
        except Exception:
            pass

        user_data["ad_data"] = [ad for ad in user_data["ad_data"] if ad["ad_id"] != ad_id]
        self.db.update_user(str(interaction.user.id), user_data)

        success_embed = Templates.drop_success()
        success_embed.title = "`⋆｡ﾟ☁︎｡𖦹 Advertisement Removed ｡☁︎ﾟ｡⋆`"
        success_embed.description = f"> Your ad with ID `{ad_id}` has been successfully removed."
        success_embed.color = nextcord.Color.green()
        success_embed.set_footer(text="Thank you for using SAJAX Ads!")
        return await interaction.send(embed=success_embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Ads(bot))
