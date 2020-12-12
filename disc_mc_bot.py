import discord
from discord.ext import commands
from discord.utils import get
import requests
import json
import pymongo # TODO: Convert into Postgres SQLite
import os
import argparse
import uuid

# Import config class for tokens
from config import Config
from operations import Operator

# Create new config object for the tokens
conf = Config()

"""
Dictionary to store location information
NOTE: Locations will be stored in this manner
{
  "id"          : "en1oi231o3123-0",
  "name"        : "My House",
  "author"      : {"name" : "Warsna", "discord_name" : "Warsna#4581", "discord_id" : "4214214635"}
  "coords"      : { "x" : 1414, "y" : 3123213, "z" : 1230 },
  "description" : "Location of my house"
}
"""
locations = []

# Setting command character for issuing commands
client = commands.Bot(command_prefix = "$")
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
async def purge(ctx, num=1):
    """Bot Command

    Used to delete the last 'num' number of messages from the text channel

    :param num: Number of last messages to delete (Default: 1)
    :type num: Int
    """
    await ctx.channel.purge(limit = num+1)
    print(f"{num} messages have been deleted from {ctx.channel}")


# Command to add new location
@client.command(aliases = ["save", "s"])
async def save_coords(ctx, name, x, y, z=None, desc=None):
    """Bot Command

    Used to add the given location data to the collection of locations
    Will inform user of successful addition or not.

    :param name: Name of the location
    :param x: X coordinate of location
    :param y: Y coordinate of location
    :param z: (Optional) Z coordinate of location
    :param desc: (Optional) Description of the location that was saved
    :type name: String
    :type x: Int
    :type y: Int
    :type z: Int
    :type desc: String
    """
    # Verify main data is valid
    if not op.verify_location_data(name, x, y):
        print("WARN - Entered location data not valid, informing user")
        await ctx.channel.send("The entered location data is invalid, please ensure you are entering in the proper types.")
        return

    # Save instance of the user who sent the message
    user = ctx.message.author

    op.add_location(name, user, x, y, z, desc)

    print(op.locations)

    print("OK - Successfully entered in location data.")
    await ctx.channel.send("New location saved under name '**{}**' located at (**{}**, **{}**)!".format(name, x, y))
    return

# Command to add new location
@client.command(aliases = ["get", "g"])
async def get_coords(ctx, search_token, query="name"):
    
    # Search for the location data
    searched = op.get_location_data(search_token, query)

    # Check if search was successful
    if searched == False:
        await ctx.channel.send("The query that you provided: {}, is unsupported. Supported queries are {}".format(query, ",".join(op.query_types)))
        return
    
    # If no data was found
    if searched == None:
        await ctx.channel.send("No location data was found under {}: {}, please verify that the name you entered is correct and try again.".format(query, search_token))
        return

    # Means search found something, print it to user.
    await ctx.channel.send(embed=op.location_embed(searched))
    return

# Command to list all registered locations
@client.command(aliases = ["list", "l"])
async def list_coords(ctx):
    await ctx.channel.send(embed=op.location_list_embed())
    return

# Command to test embed tile
@client.command()
async def embed(ctx):
    embed = discord.Embed(
        title = "My Embed",
        description = "Testing the embed features in discord.py",
        colour = discord.Color.green()
    )

    embed.set_footer(text="My footer")

    # Fields
    embed.add_field(name="field1", value="field value", inline=False)
    embed.add_field(name="field2", value="field value2", inline=True)

    await ctx.channel.send(embed=embed)

# Function to set up the argparser
def setup_argparse():
    parser = argparse.ArgumentParser(description="Minecraft Discord Bot... by: Nabeel Warsalee")

    parser.add_argument('--dev', action="store_true", help="Activate dev mode")

    return parser.parse_args()

# Check if running in dev mode
args = setup_argparse()

if args.dev:
    print("Running in developer mode...")
    USE_LOCAL=True
else:
    USE_LOCAL=False

# Create Operator instance to provide functions
op = Operator(USE_LOCAL, conf)

# Run the bot instance
client.run(conf.DISCORD_TOKEN)