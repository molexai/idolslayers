import os
import json
import time

import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Embed, Color
from nextcord.ui import View, button, Button

from SAJAX.database import Database
from SAJAX.templates import Templates

GUILD_ID = [1369853145827770368]

class ItemPageView(View):
    def __init__(self, user_items, shop_items, templates, owner_id, timeout=180):
        super().__init__(timeout=timeout)
        self.user_items = user_items  # list of keys like 'drop_booster'
        self.shop_items = shop_items  # list of dicts with full item data
        self.index = 0
        self.templates = templates
        self.owner_id = owner_id
        self.displayed_items = set()
        self.update_buttons()
        self.db = Database()

    def update_buttons(self):
        self.children[0].disabled = self.index == 0
        self.children[1].disabled = self.index == len(self.user_items) - 1

    def generate_embed(self):
        item_key = self.user_items[self.index]
        shop_item = next((i for i in self.shop_items if i['name'].lower().replace(' ', '_') == item_key), None)
        if not shop_item:
            embed = Embed(title="Unknown Item", description="No details available.", color=Color.red())
            embed.set_footer(text=f"Item {self.index + 1} of {len(self.user_items)}")
            return embed
        return self.templates.item_details(
            item_name=shop_item['name'],
            worth=shop_item['price'],
            description=shop_item['description']
        ).set_footer(text=f"Item {self.index + 1} of {len(self.user_items)}")

    @button(label="Previous", style=nextcord.ButtonStyle.blurple)
    async def previous(self, button: Button, interaction: Interaction):
        if self.index > 0:
            self.index -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Next", style=nextcord.ButtonStyle.blurple)
    async def next(self, button: Button, interaction: Interaction):
        if self.index < len(self.user_items) - 1:
            self.index += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @button(label="Use", style=nextcord.ButtonStyle.green, custom_id="use_item")
    async def use(self, button: Button, interaction: Interaction):
        item_key = self.user_items[self.index]
        user_id_str = str(interaction.user.id)

        user_data = self.db.get_user(user_id_str) or {}
        usables = user_data.get("usables", {})
        enabled_items = user_data.get("enabled_items", [])

        if item_key not in usables:
            embed = self.templates.drop_error()
            embed.description = f"> ❌ You no longer own **{item_key.replace('_', ' ').title()}**."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if item_key in enabled_items:
            embed = self.templates.drop_error()
            embed.description = f"> ❌ You already have **{item_key.replace('_', ' ').title()}** enabled."
            return await interaction.response.send_message(embed=embed, ephemeral=True)


        del usables[item_key]
        enabled_items.append(item_key)

        # Update DB with new states
        self.db.update_user(user_id_str, {"usables": usables, "enabled_items": enabled_items})

        # Remove from local list and update view
        self.user_items.remove(item_key)
        self.displayed_items.add(item_key)

        if not self.user_items:
            embed = self.templates.drop_error()
            embed.description = "> You have no more items to use!"
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.index = min(self.index, len(self.user_items) - 1)
        self.update_buttons()
        embed = self.generate_embed()
        if not embed:
            embed = Embed(title="No Item", description="No details available.", color=nextcord.Color.red())
        embed.set_footer(text=f"Item {self.index + 1} of {len(self.user_items)}")
        await interaction.response.edit_message(embed=embed, view=self)

        item_name = item_key.replace('_', ' ').title()
        success_embed = self.templates.item_used(item_name=item_name)
        success_embed.description = f"> You have successfully used **{item_name}**!"
        success_embed.color = nextcord.Color.green()
        await interaction.followup.send(embed=success_embed, ephemeral=True)

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.json_path = os.path.join(os.path.dirname(__file__), "shop_items.json")
        self.myitems_cooldowns = {}
        self.MYITEMS_COOLDOWN = 5

    @nextcord.slash_command(name="myitems", description="View your owned items.", guild_ids=GUILD_ID)
    async def myitems(self, interaction: Interaction):
        user_id = interaction.user.id
        now = time.time()
        last_used = self.myitems_cooldowns.get(user_id, 0)

        if interaction.guild:
            member = interaction.guild.get_member(user_id)
            if member and member.guild_permissions.administrator:
                last_used = 0

        if now - last_used < self.MYITEMS_COOLDOWN:
            remaining = round(self.MYITEMS_COOLDOWN - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.myitems_cooldowns[user_id] = now

        user_data = self.db.get_user(str(user_id)) or {}
        usables = user_data.get("usables", {})
        owned_item_keys = list(usables.keys())
        if not owned_item_keys:
            embed = Templates.drop_error()
            embed.description = "> You don't own any items yet!"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                shop_data = json.load(f)
        except Exception:
            embed = Templates.drop_error()
            embed.description = "> Failed to load item details. Try again later."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        shop_items = shop_data.get("shop_items", [])
        filtered_shop_items = [item for item in shop_items if item['name'].lower().replace(' ', '_') in owned_item_keys]

        view = ItemPageView(owned_item_keys, shop_items, Templates, user_id)
        embed = view.generate_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(Items(bot))