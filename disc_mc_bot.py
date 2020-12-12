import discord
from discord.ext import commands
from discord.utils import get
import requests
import json
import pymongo # TODO: Convert into Postgres SQLite
import os

# Import config class for tokens
from config import Config

# Create new config object for the tokens
conf = Config()

# Setting command character for issuing commands
client = commands.Bot(command_prefix = "~")
#client.remove_command('help')

#Checks if the bot is ready and if it is it prints Bot is ready
@client.event
async def on_ready():
   print("Bot is ready")

# Command to say hi when user sends command
@client.command()
async def hi(ctx):
    """Bot Command

    Used to say hello back to the user who issued the command.
    
    """
    user = ctx.message.author
    await ctx.channel.send("Hello {}".format(user.mention))

# Command to delete a specified amount of messages
@client.command()
async def purge(ctx, num = 1):
    """Bot Command

    Used to delete the last 'x' number of messages that were sent in the text chat.

    :param num: Number of messages to delete (Default: 1)
    """
    await ctx.channel.purge(limit = num+1)
    print(f"{num} messages have been deleted from {ctx.channel}")

# Run the bot instance
client.run(conf.DISCORD_TOKEN)