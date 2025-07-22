import json
from datetime import datetime

import nextcord
from nextcord import Embed, Color

from SAJAX.database import Database


class Templates:
    pastel_emojis = [
        "<:z_dashgreen:1396906153316978838>",
        "<:z_dashpink:1396906180151873556>",
        "<:z_dashwhite:1396906201782026364>",
        "<:z_dashyellow:1396906220572639413>",
        "<:z_musicnotepink_DNS:1397061978651885740>",
        "<a:001_sajaboyspixel_DNS:1397275022133039157>",
    ]
    pastel_emojis_text = " ".join(pastel_emojis[:4])

    @staticmethod
    def drop_summon():
        emoji_wave = f"{Templates.pastel_emojis_text} " * 2 + "➤"
        embed = Embed(
            title=f"`⋆｡ﾟ☁︎｡⋆｡ 𖦹 ₊˚⊹♡` "
                  f" **Summoning your SAJAX Drop...** {Templates.pastel_emojis[4]}",
            description=emoji_wave.strip(),
            color=nextcord.Color.from_rgb(221, 160, 221)  # Light lavender tone
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1389302090303803433/1397020148719812728/Pc_Wallpaper_Gif_Anime_Aesthetic.gif"
        )
        embed.set_footer(text="Hang tight, your drop is materializing ✧")
        return embed

    @staticmethod
    def drop_error():
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Uh-oh! Something went wrong...｡☁︎ﾟ｡⋆`",
            description="> 🍓 **Oopsie!** Your SAJAX drop got a little tangled in the wind.\n"
                        "> Try again in a bit — we'll fix it up real nice! ♡",
            color=nextcord.Color.from_rgb(255, 102, 102)  # Soft red-pink
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1389302090303803433/1397022708831342732/aesthetic_crying_cat.gif"
        )
        embed.set_footer(text="Let’s give it another go, okay? 🍥")
        return embed

    @staticmethod
    def display_cards(user_id):
        db = Database()
        characters = db.get_characters(str(user_id)) or []

        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Your SAJAX Cards! ｡☁︎ﾟ｡⋆`",
            description=f"> Here are the cards you received from your drop! {Templates.pastel_emojis[5]}",
            color=nextcord.Color.from_rgb(173, 216, 230)
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1389302090303803433/1397022708831342732/aesthetic_crying_cat.gif"
        )

        for char in characters:
            name = char.get('name', 'Unknown')
            rarity = char.get('rarity', char.get('top_rarity', 'Unknown'))


            rarity_styles = {
                "B": ("Balanced ⚖️", "<:z_dashwhite:1396906201782026364>"),
                "A": ("Amazing ✨", "<:z_dashpink:1396906180151873556>"),
                "R": ("Rare 💎", "<:z_dashyellow:1396906220572639413>"),
                "UR": ("Ultra Rare 🌟", "<:z_dashgreen:1396906153316978838>"),
                "Unknown": ("Unknown ❓", "❔")
            }

            rarity_name, rarity_emoji = rarity_styles.get(rarity, ("Unknown ❓", "❔"))

            # Add some style to the field value
            field_value = (
                f"{rarity_emoji} **Rarity:** {rarity_name}\n"
                f"> *Unlock your destiny with {name}!*"
            )

            embed.add_field(name=f"🃏 {name}", value=field_value, inline=False)

        embed.set_footer(text=f"Requested at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ✨")
        return embed

    @staticmethod
    def sell_cooldown():
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Uh-oh! Cooldown! ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[0]} You're on cooldown! Please wait a bit before selling again.",
            color=Color.from_rgb(255, 153, 102)  # soft orange
        )
        embed.set_footer(text="Patience is key ♡")
        return embed

    @staticmethod
    def sell_no_character(character_name: str):
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Not Found! ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[1]} You don't own any character named **{character_name}**.",
            color=Color.from_rgb(255, 102, 102)  # soft red-pink
        )
        embed.set_footer(text="Try checking your cards again ♡")
        return embed

    @staticmethod
    def sell_prompt(matching: list):
        desc = "\n".join(
            f"{i + 1}. {c['name']} — {c.get('rarity', c.get('top_rarity', '?'))}"
            for i, c in enumerate(matching)
        )
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Select a character to sell! ｡☁︎ﾟ｡⋆`",
            description=desc,
            color=Color.gold()
        )
        embed.set_footer(text="Choose wisely ✨")
        return embed

    @staticmethod
    def sell_confirm(char: dict):
        embed = Embed(
            title=f"`⋆｡ﾟ☁︎｡𖦹 Sell Confirmation ｡☁︎ﾟ｡⋆`",
            description=(
                f"**Name:** {char['name']}\n"
                f"**Rarity:** {char.get('rarity', char.get('top_rarity', '?'))}\n"
                f"**Group:** {char.get('group', 'Unknown')}\n\n"
                "Click ✅ to confirm or ❌ to cancel."
            ),
            color=Color.orange()
        )
        if thumb := char.get("thumbnail_url"):
            embed.set_thumbnail(url=thumb)
        embed.set_footer(text="Think twice, then choose ✧")
        return embed

    @staticmethod
    def sell_success(shards):
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Sold Successfully! ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[0]} Your character was sold! {shards} shards have been added.",
            color=Color.green()
        )
        embed.set_footer(text="Thanks for playing with SAJAX! ♡")
        return embed

    @staticmethod
    def sell_cancelled():
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Sale Cancelled ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[1]} No worries — your character is safe!",
            color=Color.red()
        )
        embed.set_footer(text="Try again anytime ✨")
        return embed

