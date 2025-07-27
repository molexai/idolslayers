import json
import os

import nextcord
from nextcord import Embed, Color


def get_emoji(emoji_name: str):
    """
    Fetches an emoji from the emojis.json file.
    """
    with open(Templates.emojis_path, 'r') as f:
        data = json.load(f)

    for emoji in data.get("emojis", []):
        if emoji.get("name") == emoji_name:
            return emoji.get("emoji_id")

    return f":{emoji_name}:"

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

    rarity_emojis = [
        "<:z_musicnotegreen_DNS:1397625897443655891>",
        "<:z_musicnoteblue_DNS:1397625915500134521>",
        "<:z_musicnotepink_DNS:1397625875213717724>",
        "<:z_musicnotepurple_DNS:1397625855672455281>",
        "<:z_musicnotegold_DNS:1397669618566430872>",
    ]
    rarity_fire_emojis = [
        "<a:z_sajaboysfiregreen_DNS:1397628059200524398>",
        "<a:z_sajaboysfireblue_DNS:1396906311450361947>",
        "<a:z_sajaboysfirepink_DNS:1397628076086657194>",
        "<a:z_sajaboysfirepurple_DNS:1397628093258272838>"
    ]

    emojis_path = os.path.join(os.path.dirname(__file__), "data/emojis.json")

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
            url="https://cdn.discordapp.com/attachments/1382048543061315674/1395253225619324959/tumblr_3d4d8e88060f1f0bd5fb426f80663ba7_9dd63a95_540-ezgif.com-crop.gif?ex=6883a993&is=68825813&hm=5626e1cbf6c69f4a3a920578031896603ec6c1e4daaa71f0d4af90866f5f10af&"
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
    def drop_success():
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Drop Successful! ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[0]} Your SAJAX drop was a success! Check your cards with `/mycards`.",
            color=Color.from_rgb(173, 216, 230)
        )
        embed.set_footer(text="Thanks for playing with SAJAX! ♡")
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
            f"**{i + 1}.** ✦ `{c['name']}` — {convert_huntrix_ur(group=c.get('group', 'Unknown'), rarity=c.get('rarity', 'Unknown'))} "
            for i, c in enumerate(matching)
        )

        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Choose a Character to Sell! ｡☁︎ﾟ｡⋆`",
            description=desc.replace('â€™', ''),
            color=Color.from_rgb(173, 216, 230)  # Light pastel blue
        )
        embed.set_footer(text="💸 Sell wisely to maximize your gains!")
        return embed

    @staticmethod
    def sell_confirm(char: dict):
        embed = Embed(
            title=f"`⋆｡ﾟ☁︎｡𖦹 Sell Confirmation ｡☁︎ﾟ｡⋆`",
            description=(
                f"**Name:** **{char['name']}**\n"
                f"**Rarity:** {convert_huntrix_ur(group=char.get('group'), rarity=char.get('rarity'))}\n"
                f"**Group:** {char.get('group', 'Unknown')}\n\n"
                "Click ✅ to confirm or ❌ to cancel."
            ),
            color=Color.from_rgb(255, 228, 225)
        )
        if thumb := char.get("thumbnail_url"):
            embed.set_image(url=thumb)
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
        embed.set_footer(text="Try again anytime! ♡")
        return embed

    @staticmethod
    def sell_all_success(amount: int):
        embed = Embed(
            title="`⋆｡ﾟ💎｡ Characters Sold! ｡💎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[0]} You've sold all your characters for **{amount} shards**!",
            color=Color.from_rgb(173, 216, 230)
        )
        embed.set_footer(text="Thanks for playing with SAJAX! ♡")
        return embed

    @staticmethod
    def sell_all_confirm():
        confirm_embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Sell ALL Characters? ｡☁︎ﾟ｡⋆`",
            description=f"> {Templates.pastel_emojis[2]} Are you sure you want to sell **all** your characters?\nThis action **cannot** be undone.",
            color=Color.from_rgb(255, 182, 193)
        )
        confirm_embed.set_footer(text="You’re about to clear your entire inventory.")
        return confirm_embed

    @staticmethod
    def card_details(character_name, rarity, desc, group, thumbnail_url=None):
        embed = Embed(
            title=f"`⋆｡ﾟ☁︎｡𖦹 {character_name} Details ｡☁︎ﾟ｡⋆`",
            description=f"> {desc.replace('â€™', '')}",
            color=Color.from_rgb(255, 228, 225)
        )
        embed.add_field(name=f"{convert_huntrix_ur(group=group, rarity=rarity)} Rarity: {rarity}", value="", inline=True)
        if thumbnail_url:
            embed.set_image(url=thumbnail_url)
        embed.set_footer(text=f"Explore the world of SAJAX!  🍥")
        return embed

    @staticmethod
    def card_muted():
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Card Muted ｡☁︎ﾟ｡⋆`",
            description="> 🍥 **Card Muted!** You won't be able to use, gift, or pay with cards.\n",
            color=Color.from_rgb(255, 153, 102)
        )
        embed.set_footer(text="If you have any questions, please contact the SAJAX team! ♡")
        return embed

    @staticmethod
    def shop_display():
        embed = Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 SAJAX Shop ｡☁︎ﾟ｡⋆`",
            description=(
                f"> {Templates.pastel_emojis[5]} Welcome to the SAJAX Shop! "
                "Browse our powerful items designed to help you become the ultimate K-pop demon hunter.\n"
                "Select an item below and press `Buy` to add it to your arsenal.\n\n"
            ),
            color=Color.from_rgb(255, 255, 224)
        )
        shard = get_emoji('shard_non_pink')

        embed.add_field(
            name="Items for Sale",
            value=(
                f"{get_emoji('giftbox')} **Drop Booster**           —  (7550 shards) {shard}\n\n"
                f"{get_emoji('chest')} **Card Reroll**             — (5200 shards) {shard}\n\n"
                f"{get_emoji('clock')} **Drop Cooldown Reducer**   — (2300 shards) {shard}\n\n"
                f"{shard} **Shard Multiplier**             — (3400 shards) {shard}\n\n"
                f"{get_emoji('spinning_heart')} **Double Drop Chance**    — (7800 shards) {shard}\n\n"
                f"{get_emoji('up')} **Drop Queue Priority**      — (6500 shards) {shard}\n\n"
                f"{get_emoji('verified')} **Auto Drop (Soon)**              — (15000 shards) {shard}"
            ),
            inline=False
        )

        embed.set_footer(text="Happy hunting! ♡")
        return embed

    @staticmethod
    def shop_item_details(item_name, price, description):
        embed = Embed(
            title=f"`⋆｡ﾟ☁︎｡𖦹 {item_name} Details ｡☁︎ﾟ｡⋆`",
            description=f"> {description}",
            color=Color.from_rgb(255, 228, 225)
        )
        embed.add_field(name="Price", value=f"{price} shards {get_emoji('shard_non_pink')}", inline=True)
        embed.set_footer(text="Thanks for shopping with SAJAX! ♡")
        return embed

    @staticmethod
    def item_details(item_name, worth, description):
        embed = Embed(
            title=f"`⋆｡ﾟ☁︎｡𖦹 {item_name} ｡☁︎ﾟ｡⋆`",
            description=f"> {description}",
            color=Color.from_rgb(255, 228, 225)
        )
        embed.add_field(name="Worth", value=f"{worth}{get_emoji('shard_non_pink')}", inline=True)
        embed.set_footer(text="Thanks for shopping with SAJAX! ♡")
        return embed

    @staticmethod
    def item_used(item_name: str):
        return Embed(
            title="`⋆｡ﾟ☁︎｡𖦹 Item Used ｡☁︎ﾟ｡⋆`",
            description=f"> You successfully used `{item_name.replace('_', ' ').title()}`.",
            color=Color.from_rgb(173, 216, 230)
        )


def convert_rarity(rarity):
    convert_rarity = {"B": Templates.rarity_emojis[0],
                      "A": Templates.rarity_emojis[1],
                      "R": Templates.rarity_emojis[2],
                      "UR": Templates.rarity_emojis[3]}
    if rarity == "UR+":
        return Templates.rarity_emojis[4]
    return convert_rarity.get(rarity)

def convert_fire(rarity):
    convert_rarity_fire = {"B": Templates.rarity_fire_emojis[0],
                           "A": Templates.rarity_fire_emojis[1],
                           "R": Templates.rarity_fire_emojis[2],
                           "UR": Templates.rarity_fire_emojis[3]}
    return convert_rarity_fire.get(rarity)

def convert_huntrix_ur(group, rarity):
    if group == "Huntrix" and rarity == "UR":
        return convert_rarity("UR+")
    return convert_rarity(rarity)

