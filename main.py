import discord
from discord.ext import commands
import os, sys

from apikeys import *

# Bot setup
intents = discord.Intents.all()

bot = commands.Bot(command_prefix="+", intents=intents)

# Load cogs
@bot.event
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != "chat_manager.py":
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"Loaded Cog: {filename[:-3]}")
            except Exception as e:
                print(f"Failed to load Cog: {filename[:-3]} - {e}")
        else:
            print(f"Skipped loading ({filename})")
    # for filename in os.listdir('./info'):
    #     if filename.endswith('.py'):
    #         try:
    #             await bot.load_extension(f'info.{filename[:-3]}')
    #             print(f"Loaded information: {filename[:-3]}")
    #         except Exception as e:
    #             print(f"Failed to load information: {filename[:-3]} - {e}")
    #     else:
    #         print(f"Skipped loading ({filename})")
    # for filename in os.listdir('./knowledge'):
    #     if filename.endswith('.py'):
    #         try:
    #             await bot.load_extension(f'info.{filename[:-3]}')
    #             print(f"Loaded information: {filename[:-3]}")
    #         except Exception as e:
    #             print(f"Failed to load information: {filename[:-3]} - {e}")
    #     else:
    #         print(f"Skipped loading ({filename})")

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
