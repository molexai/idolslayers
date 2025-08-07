import time
import nextcord
from nextcord import SlashOption, Interaction, ButtonStyle, SelectOption
from nextcord.ext import commands
from nextcord.ui import View, button, Button, Select

from SAJAX.database import Database
from SAJAX.templates import Templates, get_emoji

GUILD_ID = 1369853145827770368

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cooldowns = {}
        self.PAY_COOLDOWN = 10
        self.GIFT_COOLDOWN = 15

    @nextcord.slash_command(
        name="pay",
        description="Pay shards to another user.",
        guild_ids=[GUILD_ID]
    )
    async def pay(self, interaction: Interaction,
                  target: nextcord.Member = SlashOption(description="User to pay"),
                  amount: int = SlashOption(description="Amount of shards to pay", min_value=1)):
        payer = interaction.user
        payer_id = str(payer.id)
        target_id = str(target.id)

        if self.db.is_card_muted(str(payer.id)):
            embed = Templates.card_muted()
            embed.description = f"> You are card muted and cannot view your cards."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if payer.id == target.id:
            embed = Templates.drop_error()
            embed.description = "> You cannot pay shards to yourself."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if target_id == self.bot.user.id:
            embed = Templates.drop_error()
            embed.description = "> You cannot pay shards to the bot."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        now = time.time()
        last_used = self.cooldowns.get(payer.id, 0)
        if interaction.guild and interaction.guild.get_member(payer.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.PAY_COOLDOWN:
            remaining = round(self.PAY_COOLDOWN - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.cooldowns[payer.id] = now

        payer_data = self.db.get_user(payer_id)
        payer_shards = payer_data.get("shards", 0)

        if payer_shards < amount:
            embed = Templates.drop_error()
            embed.description = f"> You don't have enough shards to pay {amount}."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        class PayConfirmView(View):
            def __init__(self, db, payer_id, target_id, amount):
                super().__init__(timeout=60)
                self.db = db
                self.payer_id = payer_id
                self.target_id = target_id
                self.amount = amount
                self.bot = interaction.client

            @button(label="✅ Confirm", style=ButtonStyle.success)
            async def confirm(self, button: Button, i: Interaction):
                payer_latest = self.db.get_user(self.payer_id)
                if payer_latest.get("shards", 0) < self.amount:
                    embed = Templates.drop_error()
                    embed.description = "> You no longer have enough shards to complete this payment."
                    await i.response.edit_message(embed=embed, view=None)
                    self.stop()
                    return

                self.db.add_shards(self.payer_id, -self.amount)
                self.db.add_shards(self.target_id, self.amount)

                embed = Templates.drop_success()
                embed.title = "`⋆｡ﾟ☁︎｡𖦹 Shard Payment Successful ｡☁︎ﾟ｡⋆`"
                embed.description = f"> Successfully paid **{self.amount} shards** to **{target.display_name}**."
                embed.set_footer(text=f"Payment made by {payer.display_name}.")
                await i.response.edit_message(embed=embed, view=None)

                public_embed = Templates.drop_success()
                public_embed.title = "`⋆｡ﾟ☁︎｡ 𖦹 Shard Payment ｡☁︎ﾟ｡⋆`"
                public_embed.set_thumbnail(url=payer.display_avatar.url)
                public_embed.description = f"> {get_emoji('money')} <@{self.target_id}> received **{self.amount} shards** from **{payer.display_name}**!"
                await i.channel.send(embed=public_embed)

                self.stop()

            @button(label="❌ Cancel", style=ButtonStyle.danger)
            async def cancel(self, button: Button, i: Interaction):
                embed = Templates.drop_error()
                embed.description = "> Payment cancelled."
                await i.response.edit_message(embed=embed, view=None)
                self.stop()

        embed = Templates.drop_summon()
        embed.title = "`⋆｡ﾟ☁︎｡𖦹 Payment Confirmation ｡☁︎ﾟ｡⋆`"
        embed.description = f"Do you want to pay **{amount}**{get_emoji('shard_non_pink')} to **{target.display_name}**?"
        await interaction.response.send_message(embed=embed, view=PayConfirmView(self.db, payer_id, target_id, amount), ephemeral=True)

    @nextcord.slash_command(
        name="gift",
        description="Gift a card to another user.",
        guild_ids=[GUILD_ID]
    )
    async def gift(self, interaction: Interaction,
                   target: nextcord.Member = SlashOption(description="User to gift"),
                   character: str = SlashOption(description="Name of the character to gift")):
        sender = interaction.user
        sender_id = str(sender.id)
        target_id = str(target.id)

        if self.db.is_card_muted(str(sender.id)):
            embed = Templates.card_muted()
            embed.description = f"> You are card muted and cannot view your cards."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if sender.id == target.id:
            embed = Templates.drop_error()
            embed.description = "> You cannot gift cards to yourself."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if target_id == self.bot.user.id:
            embed = Templates.drop_error()
            embed.description = "> You cannot gift cards to the bot."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        now = time.time()
        last_used = self.cooldowns.get(sender.id, 0)
        if interaction.guild and interaction.guild.get_member(sender.id).guild_permissions.administrator:
            last_used = 0

        if now - last_used < self.GIFT_COOLDOWN:
            remaining = round(self.GIFT_COOLDOWN - (now - last_used), 1)
            embed = Templates.drop_error()
            embed.description = f"> You're on cooldown! Try again in {remaining}s."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.cooldowns[sender.id] = now

        sender_data = self.db.get_user(sender_id)
        characters = sender_data.get("characters", [])

        character_name = character.strip().lower()
        matching = [c for c in characters if c.get("name", "").strip().lower() == character_name]

        if not matching:
            embed = Templates.drop_error()
            embed.description = f"> You don't have any cards named **{character}**."
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        PAGE_SIZE = 25
        total_pages = (len(matching) + PAGE_SIZE - 1) // PAGE_SIZE

        class CharacterSelectWithPagination(View):
            def __init__(self, db, sender_id, target_id, matching, page=0):
                super().__init__(timeout=60)
                self.db = db
                self.sender_id = sender_id
                self.target_id = target_id
                self.matching = matching
                self.page = page
                self.total_pages = (len(matching) + PAGE_SIZE - 1) // PAGE_SIZE
                self.update_select()

                if self.total_pages > 1:
                    if self.page > 0:
                        self.add_item(PrevButton())
                    if self.page < self.total_pages - 1:
                        self.add_item(NextButton())

            def update_select(self):
                start = self.page * PAGE_SIZE
                end = start + PAGE_SIZE
                options = [
                    SelectOption(
                        label=f"{i + 1 + start}. {c['name']}",
                        description=f"Rarity: {c.get('rarity', c.get('top_rarity', '?'))}",
                        value=str(i + start)
                    ) for i, c in enumerate(self.matching[start:end])
                ]
                self.add_item(CharacterSelect(options, self.db, self.sender_id, self.target_id, self.matching))

        class CharacterSelect(Select):
            def __init__(self, options, db, sender_id, target_id, matching):
                super().__init__(
                    placeholder="Select which character to gift…",
                    min_values=1,
                    max_values=1,
                    options=options
                )
                self.db = db
                self.sender_id = sender_id
                self.target_id = target_id
                self.matching = matching

            async def callback(self, ctx: Interaction):
                idx = int(self.values[0])
                selected_card = self.matching[idx]
                current_chars = self.db.get_characters(self.sender_id)
                if selected_card not in current_chars:
                    embed = Templates.drop_error()
                    embed.description = "> You no longer own that card."
                    return await ctx.response.edit_message(embed=embed, view=None)

                class GiftConfirmView(View):
                    def __init__(self, db, target_id, sender_id):
                        super().__init__()
                        self.db = db
                        self.target_id = target_id
                        self.sender_id = sender_id

                    @button(label="✅ Yes, gift this card", style=ButtonStyle.success)
                    async def confirm(self, button: Button, i: Interaction):
                        current_chars = self.db.get_characters(self.sender_id)
                        if selected_card not in current_chars:
                            embed = Templates.drop_error()
                            embed.description = "> You no longer own that card."
                            return await i.response.edit_message(embed=embed, view=None)

                        # make sure they cant gift if the rarity is S
                        if selected_card.get("rarity", selected_card.get("top_rarity", "")) == "S":
                            embed = Templates.drop_error()
                            embed.description = "> You cannot gift **S tier** cards."
                            return await i.response.edit_message(embed=embed, view=None)

                        self.db.remove_character_and_card(self.sender_id, selected_card)
                        self.db.add_character(self.target_id, selected_card)
                        self.db.add_card(self.target_id, selected_card.get("character_id"))

                        embed = Templates.drop_success()
                        embed.description = f"> Successfully gifted **{selected_card.get('name')}** to {target.display_name}!"
                        embed.set_image(url=selected_card.get("thumbnail_url", None))
                        await i.response.edit_message(embed=embed, view=None)

                        public_embed = Templates.drop_success()
                        public_embed.title = "`⋆｡ﾟ☁︎｡ 𖦹 Card Gifted ｡☁︎ﾟ｡⋆`"
                        public_embed.set_image(url=selected_card.get("thumbnail_url", None))
                        public_embed.description = f"> {get_emoji('giftbox')} <@{self.target_id}> received **{selected_card.get('name')}** from **{sender.display_name}**!"
                        await i.channel.send(embed=public_embed)

                    @button(label="❌ Cancel", style=ButtonStyle.danger)
                    async def cancel(self, button: Button, i: Interaction):
                        embed = Templates.drop_error()
                        embed.description = "> Gift cancelled."
                        await i.response.edit_message(embed=embed, view=None)

                embed = Templates.card_details(
                    selected_card.get("name", "Unknown"),
                    selected_card.get("rarity", selected_card.get("top_rarity", "Unknown")),
                    selected_card.get("description", "No description."),
                    selected_card.get("group", "Unknown"),
                    selected_card.get("thumbnail_url", None)
                )
                embed.set_footer(text=f"Do you want to gift this card to {target.display_name}?")
                await ctx.response.edit_message(embed=embed,
                                                view=GiftConfirmView(self.db, self.target_id, self.sender_id))

        class PrevButton(Button):
            def __init__(self):
                super().__init__(label="◀️ Previous", style=ButtonStyle.secondary)

            async def callback(self, i: Interaction):
                new_view = CharacterSelectWithPagination(self.view.db, self.view.sender_id, self.view.target_id,
                                                         self.view.matching, page=self.view.page - 1)
                embed = Templates.drop_summon()
                embed.title = f"Select which '{character}' to gift to {target.display_name} (Page {self.view.page})"
                await i.response.edit_message(embed=embed, view=new_view)

        class NextButton(Button):
            def __init__(self):
                super().__init__(label="▶️ Next", style=ButtonStyle.secondary)

            async def callback(self, i: Interaction):
                new_view = CharacterSelectWithPagination(self.view.db, self.view.sender_id, self.view.target_id,
                                                         self.view.matching, page=self.view.page + 1)
                embed = Templates.drop_summon()
                embed.title = f"Select which '{character}' to gift to {target.display_name} (Page {self.view.page + 2})"
                await i.response.edit_message(embed=embed, view=new_view)

        initial_view = CharacterSelectWithPagination(self.db, sender_id, target_id, matching, page=0)

        embed = Templates.drop_summon()
        embed.title = f"Select which '{character}' to gift to {target.display_name} (Page 1)"
        await interaction.response.send_message(embed=embed, view=initial_view, ephemeral=True)


def setup(bot):
    bot.add_cog(EconomyCog(bot))
