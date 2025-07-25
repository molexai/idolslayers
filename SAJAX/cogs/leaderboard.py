import json
import os
import time

import nextcord
from nextcord import SlashOption, Interaction, Embed, Color
from nextcord.ext import commands
from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = 1369853145827770368

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.leaderboard_cooldowns = {}
        self.LEADERBOARD_COOLDOWN = 10

        rarities_path = os.path.join(os.path.dirname(__file__), 'rarities.json')
        with open(rarities_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.rarity_worth = {item['tier']: item['worth'] for item in data.get('rarities', [])}

    @nextcord.slash_command(
        name="leaderboard",
        description="View the SAJAX leaderboard.",
        guild_ids=[GUILD_ID]
    )
    async def leaderboard(
        self,
        interaction: Interaction,
        type: str = SlashOption(
            name="type",
            description="Which leaderboard to view",
            choices={"shards": "shards", "characters": "characters"},
            required=True
        )
    ):
        user = interaction.user
        now = time.time()
        last_used = self.leaderboard_cooldowns.get(user.id, 0)
        if interaction.guild and interaction.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.LEADERBOARD_COOLDOWN:
            remaining = round(self.LEADERBOARD_COOLDOWN - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in `{remaining}s`."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.leaderboard_cooldowns[user.id] = now

        all_users = list(self.db.users.find({}))
        guild = interaction.guild

        if type == 'shards':
            sorted_by_shards = sorted(
                all_users,
                key=lambda doc: doc.get('shards', 0),
                reverse=True
            )[:5]

            fire_emoji = Templates.rarity_fire_emojis[2]

            embed = Embed(
                title="`⋆｡ﾟ☁︎｡ 𖦹 Top Shards Leaderboard ｡☁︎ﾟ｡⋆`",
                description=f"{fire_emoji} **Top 5 players with the most shards**",
                color=Color.from_rgb(102, 204, 255)
            )
            for idx, doc in enumerate(sorted_by_shards, 1):
                uid = int(doc.get('user_id'))
                member = guild.get_member(uid)
                username = member.display_name if member else f"User {uid}"
                shards = doc.get('shards', 0)
                embed.add_field(
                    name=f"{idx}. {username}",
                    value=f"💎 **{shards}** shards",
                    inline=False
                )
        else:
            user_stats = []
            for doc in all_users:
                uid = doc.get('user_id')
                chars = doc.get('characters', [])
                count = len(chars)
                net_worth = sum(
                    self.rarity_worth.get(
                        c.get('rarity', c.get('top_rarity', '')), 0
                    ) for c in chars
                )
                user_stats.append({'uid': uid, 'count': count, 'net': net_worth})
            top_chars = sorted(
                user_stats,
                key=lambda d: d['count'],
                reverse=True
            )[:5]

            fire_emoji = Templates.rarity_fire_emojis[3]

            embed = Embed(
                title="`⋆｡ﾟ☁︎｡ 𖦹 Top Characters Leaderboard ｡☁︎ﾟ｡⋆`",
                description=f"{fire_emoji} **Top 5 players by character count (net worth in shards)**",
                color=Color.purple()
            )
            for idx, stat in enumerate(top_chars, 1):
                uid = int(stat['uid'])
                member = guild.get_member(uid)
                username = member.display_name if member else f"User {uid}"
                embed.add_field(
                    name=f"{idx}. {username}",
                    value=f"🗡️ **{stat['count']}** characters — 💰 **{stat['net']}** shards net worth",
                    inline=False
                )

        embed.set_footer(text="Thanks for playing with SAJAX! ♡")
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(LeaderboardCog(bot))
