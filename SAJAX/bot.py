import nextcord
from nextcord.ext import commands
import os

intents = nextcord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "json_db.py":
        extension = f"cogs.{filename[:-3]}"
        try:
            bot.load_extension(extension)
            print(f"✅ Loaded extension: {extension}")
        except Exception as e:
            print(f"❌ Failed to load {extension}: {e}")

bot.run("MTM4NzUwOTI1MTg5MDYxNDQyMg.GRCvtO.FzrhOIog7Ds9QHNDFLlX2TWdreRnYzK5Gqn5-c")
