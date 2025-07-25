import nextcord
from nextcord.ext import commands
from pathlib import Path
import sys

intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_USER_ID = 1152734418109206548
COLLAB_ROLE_NAME = "SajaX - Collaborator"
COLLAB_ROLE_COLOR = nextcord.Color.from_rgb(255, 105, 180)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.sync_all_application_commands()

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

cogs_dir = Path(__file__).resolve().parent / "cogs"

if cogs_dir.exists():
    for file in cogs_dir.glob("*.py"):
        if file.name != "json_db.py":
            extension = f"SAJAX.cogs.{file.stem}"
            try:
                bot.load_extension(extension)
                print(f"✅ Loaded extension: {extension}")
            except Exception as e:
                print(f"❌ Failed to load {extension}: {e}")
else:
    print(f"❌ Cogs directory not found at {cogs_dir}")

bot.run("MTM4NzUwOTI1MTg5MDYxNDQyMg.GRCvtO.FzrhOIog7Ds9QHNDFLlX2TWdreRnYzK5Gqn5-c")
