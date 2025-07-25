import json
import os
import time

import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, Color
from nextcord.ui import View, Select, button, Button

from SAJAX.database import Database
from SAJAX.templates import Templates
from SAJAX.templates import get_emoji

GUILD_ID = [1369853145827770368]


class BuyConfirmView(View):
    cooldowns = {}
    COOLDOWN_SECONDS = 5

    def __init__(self, user_id: str, item_name: str, item_price: int, db: Database):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_name = item_name
        self.item_price = item_price
        self.db = db

    async def check_shards(self):
        user_data = self.db.get_user(self.user_id) or {}
        shards = user_data.get("shards", 0)
        return shards >= self.item_price

    @button(label="✅ Yes", style=nextcord.ButtonStyle.success)
    async def confirm(self, button: Button, interaction: Interaction):
        now = time.time()
        last_used = self.cooldowns.get(self.user_id, 0)

        if interaction.guild and interaction.guild.get_member(interaction.user.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.COOLDOWN_SECONDS:
            remaining = round(self.COOLDOWN_SECONDS - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> ❌ You're on cooldown! Try again in {remaining}s."
            await interaction.response.edit_message(embed=embed, view=None)
            return

        if not await self.check_shards():
            embed = Templates.drop_error()
            embed.description = "> ❌ You do not have enough shards to buy this item."
            await interaction.response.edit_message(embed=embed, view=None)
            return
        user_data = self.db.get_user(self.user_id) or {}
        usables = user_data.get("usables", {})
        if usables.get(self.item_name.lower().replace(" ", "_")):
            embed = Templates.drop_error()
            embed.description = f"> ❌ You already own **{self.item_name}**."
            await interaction.response.edit_message(embed=embed, view=None)
            return
        self.db.add_shards(self.user_id, -self.item_price)
        usables = user_data.get("usables", {})
        usables[self.item_name.lower().replace(" ", "_")] = True
        self.db.update_user(self.user_id, {"usables": usables})

        success_embed = Templates.sell_success(self.item_price)
        success_embed.title = "`⋆｡ﾟ☁｡･ﾟ✧ Purchase Successful! ✧･ﾟ｡☁ﾟ｡⋆`"
        success_embed.description = f"> {get_emoji('up')} You successfully purchased **{self.item_name}** for {self.item_price} shards!"
        await interaction.response.edit_message(embed=success_embed, view=None)

        self.cooldowns[self.user_id] = now
        self.stop()

    @button(label="❌ No", style=nextcord.ButtonStyle.danger)
    async def cancel(self, button: Button, interaction: Interaction):
        cancel_embed = Templates.sell_cancelled()
        cancel_embed.title = "`⋆｡ﾟ☁｡･ﾟ✧ Purchase Cancelled! ✧･ﾟ｡☁ﾟ｡⋆`"
        cancel_embed.description = "> ❌ Your purchase has been cancelled."
        await interaction.response.edit_message(embed=cancel_embed, view=None)
        self.stop()


class ShopDropdown(Select):
    def __init__(self, user_id: str, db: Database):
        self.db = db
        self.user_id = str(user_id)

        options = [
            nextcord.SelectOption(label="Drop Booster", value="Drop Booster"),
            nextcord.SelectOption(label="Card Reroll", value="Card Reroll"),
            nextcord.SelectOption(label="Drop Cooldown Reducer", value="Drop Cooldown Reducer"),
            nextcord.SelectOption(label="Shard Multiplier", value="Shard Multiplier"),
            nextcord.SelectOption(label="Double Drop Chance", value="Double Drop Chance"),
            nextcord.SelectOption(label="Drop Queue Priority", value="Drop Queue Priority"),
            nextcord.SelectOption(label="Auto Drop (Soon)", value="Auto Drop"),
        ]

        super().__init__(
            placeholder="Pick something to view details...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction):
        choice = self.values[0]

        file_path = os.path.join(os.path.dirname(__file__), "shop_items.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                shop_data = json.load(f)
        except Exception:
            await interaction.response.send_message(
                "❌ Failed to load shop data. Please try again later.", ephemeral=True
            )
            return

        item_info = next((item for item in shop_data.get("shop_items", []) if item["name"] == choice), None)

        if not item_info:
            await interaction.response.send_message("❌ Item not found.", ephemeral=True)
            return

        embed = Templates.shop_item_details(
            item_name=item_info["name"],
            price=item_info["price"],
            description=item_info["description"]
        )

        view = View(timeout=60)
        view.add_item(BuyButton(self.user_id, item_info["name"], item_info["price"], self.db))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class BuyButton(Button):
    def __init__(self, user_id: str, item_name: str, item_price: int, db: Database):
        super().__init__(label="Buy", style=nextcord.ButtonStyle.success)
        self.user_id = user_id
        self.item_name = item_name
        self.item_price = item_price
        self.db = db

    async def callback(self, interaction: Interaction):
        user_data = self.db.get_user(self.user_id) or {}
        shards = user_data.get("shards", 0)

        if shards < self.item_price:
            embed = Templates.drop_error()
            embed.description = "> ❌ You don't have enough shards to buy this item."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        confirm_view = BuyConfirmView(self.user_id, self.item_name, self.item_price, self.db)
        confirm_embed = Embed(
            title="Confirm Purchase",
            description=f"> Are you sure you want to buy **{self.item_name}** for {self.item_price} shards?",
            color=Color.green()
        )
        confirm_embed.set_footer(text="You have 60 seconds to confirm.")
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)


class ShopView(View):
    def __init__(self, user_id: str, db: Database):
        super().__init__(timeout=None)
        self.add_item(ShopDropdown(user_id, db))



class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        self.COOLDOWN_SECONDS = 5

    @nextcord.slash_command(name="shop", description="Open the SajaX item shop.", guild_ids=GUILD_ID)
    async def shop(self, interaction: Interaction):
        user = interaction.user
        user_id = user.id
        now = time.time()
        last_used = self.cooldowns.get(user_id, 0)

        if interaction.guild and interaction.guild.get_member(user.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.COOLDOWN_SECONDS:
            remaining = round(self.COOLDOWN_SECONDS - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.cooldowns[user_id] = now

        if self.db.is_card_muted(str(user_id)):
            embed = Templates.card_muted()
            embed.description = "> You are card muted and cannot view the shop."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = Templates.shop_display()
        embed.set_footer(text="Select an item to view details!")
        view = ShopView(str(user_id), self.db)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(Shop(bot))