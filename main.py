import discord, sqlite3
from discord.ext import commands
import os, sys

from apikeys import *

# Bot setup
intents = discord.Intents.all()

bot = commands.Bot(command_prefix="+", intents=intents)

def ensure_directories():
    """Ensure required directories exist."""
    for folder in ["data", "prompts", "chat_histories", "prompts"]:
        os.makedirs(folder, exist_ok=True)

def setup_database():
    """Ensure the required databases and tables exist."""
    # Setup knowledge.db
    knowledge_conn = sqlite3.connect("data/knowledge.db")
    knowledge_cursor = knowledge_conn.cursor()
    
    knowledge_cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyword (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            general TEXT NOT NULL,
            detailed TEXT DEFAULT NULL,
            keyword TEXT NOT NULL
        )
    ''')
    
    knowledge_cursor.execute('''
        CREATE TABLE IF NOT EXISTS kondisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            teks TEXT NOT NULL,
            kondisi TEXT NOT NULL
        )
    ''')
    
    knowledge_conn.commit()
    knowledge_conn.close()

    # Setup user_info.db
    user_conn = sqlite3.connect("data/user_info.db")
    user_cursor = user_conn.cursor()
    
    user_cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            DiscordID TEXT PRIMARY KEY,
            nama TEXT NOT NULL,
            posisi TEXT,
            semester TEXT,
            kelas TEXT,
            tentang TEXT
        )
    ''')
    
    user_conn.commit()
    user_conn.close()

# Load cogs
@bot.event
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename not in ["chat_manager.py", "keyword_management.py"]:
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename[:-3]}")
            except Exception as e:
                print(f"Failed to load Cog: {filename[:-3]} - {e}")
        else:
            print(f"Skipped loading ({filename})")
    ensure_directories()
    setup_database()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


@bot.command(name="restart", help="To restart the bot")
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Restarting...")
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.command(name="sync", help="To syncronize slash commands")
@commands.is_owner()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"Sycned {len(synced)} command(s)")

@bot.command(name="ping", help="Shows the bot's latency in milliseconds")
async def ping(ctx):
    latency = bot.latency * 1000  # Convert to milliseconds
    await ctx.send(f"Pong! {latency:.2f} ms")

# Run the bot
bot.run(botToken)
