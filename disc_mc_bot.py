import discord
from discord.ext import commands
from discord.utils import get
import requests
import json
import os
import argparse
import uuid

# Import config class for tokens
from config import Config
from operations import Operator

# Create new config object that stores all Tokens
conf = Config()

# ==================== BOT RELATED FUNCTIONS ========================================

# Setting command character for issuing commands
client = commands.Bot(command_prefix = "$")
client.remove_command('help')

#Checks if the bot is ready and if it is it prints Bot is ready
@client.event
async def on_ready():
    # Change bot's status to include the command prefix and call to the help command
    await client.change_presence(status=discord.Status.online, activity=discord.Game('$help'))
    print("Bot is ready")

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
@client.command(aliases = ["save", "sv"])
async def save_coords(ctx, name, x, y, z=0, desc="N/A"):
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
    if not op.verify_location_data(name, x, y, z, desc):
        print("WARN - Entered location data not valid, informing user")
        await ctx.channel.send("The entered location data is invalid, please ensure you are entering in the proper types.")
        return

    # Save instance of the user who sent the message
    user = ctx.message.author

    op.add_location(name, user, x, y, z, desc)

    print("OK - Successfully entered in location data.")
    await ctx.channel.send("New location saved under name '**{}**' located at (**{}**, **{}**)!".format(name, x, y))
    return

# Command to add new location
@client.command(aliases = ["get", "g"])
async def get_coords(ctx, search_token):
    
    # Search for the location data
    searched = op.get_location_data(search_token)
    
    # If no data was found
    if searched == None:
        await ctx.channel.send("No location data was found under the name '{}', please verify that the name you entered is correct and try again.".format(search_token))
        return
    
    # If multiple data was found...
    if searched == False:
        await ctx.channel.send("Multiple locations found under the name '{}'. Please be specific.".format(search_token))
        return

    # Means search found something, print it to user.
    await ctx.channel.send(embed=op.location_embed(searched))
    return

# Command to remove registered coordinates based on name
@client.command(aliases = ["remove", "r", "rem"])
async def remove_coords(ctx, name):
    
    # Get the location that was desired to be removed
    searched = op.get_location_data(name)
    
    # If no data was found, tell user
    if searched == None:
        await ctx.channel.send("No location data was found under the name '{}', please verify that the name you entered is correct and try again.".format(name))
        return
    
    # If multiple data was found...
    if searched == False:
        await ctx.channel.send("Multiple locations found under the name '{}'. Please be specific.".format(search_token))
        return

    print(searched)

    # Save instance of the user who sent the message
    user = ctx.message.author

    print("Current user id: {} | Location author id: {}".format(user.id, searched["author"]["id"]))

    # Check to make sure that the user calling the remove is the owner of that location
    if str(user.id) != searched["author"]["id"]:
        await ctx.channel.send("You are not the author of this location entry. Only the author of a location can remove it. Nice try bud.")
        return

    # Means entry exists, user is the correct author, therefore remove it based on ID of location
    status = op.remove_location_data(searched['id'])

    if status is True:
        await ctx.channel.send("Successfully removed location. Goodbye '{}'!".format(name))
        return

# Command to list all registered locations
@client.command(aliases = ["list", "l"])
async def list_coords(ctx):
    await ctx.channel.send(embed=op.location_list_embed())
    return

# Command to list locations based on search values
@client.command(aliases = ["search", "sr"])
async def search_coords(ctx, search_token, query="name"):
    # Perform search of locations
    found_locations = op.search_locations(search_token, query=query)

    # Check if search was successful
    if found_locations == False:
        await ctx.channel.send("The query that you provided: {}, is unsupported. Supported queries are {}".format(query, ",".join(op.query_types)))
        return

    # Send back list of locations that were found via embeds
    await ctx.channel.send(embed=op.location_list_embed(found_locations, search_token=search_token, query=query))
    return

# Command to compute the distance between two location points and return other intresting data
@client.command(aliases = ["dist", "d"])
async def distance(ctx, nameA, nameB):
    # Calculate the distance
    status, response = op.distance(nameA, nameB)

    # Ensure calculation went smooth
    if status == False:
        await ctx.channel.send("Unable to calculate distance between the two locations.\nDue to: {}".format(response))

    distance_embed = op.create_distance_embed(nameA, nameB, response)

    # Send back the embed representation for distance
    await ctx.channel.send(embed=distance_embed)

# Help command
@client.command(aliases = ["h"])
async def help(ctx):
    """Function for help command

    Creates an embed Discord object to present all available commands to the user

    """
    # Create new embed to add in help information
    embed = discord.Embed(
        title = "Help Menu",
        description = "List of commands for Minecraft-Bot\n\nNote: *For any entries that are text (i.e. words with spaces), you must enclose them with double quotes in order for them to be recognized.*\n\nCommand prefix: **$**",
        color = discord.Color.green()
    )

    # Save command
    embed.add_field(name="$save  <name>  <x>  <y>  [z]  [description]", value="> *Save a set of coordinates under the given name.*\n> *Shorthand: '$sv'*\n> *Note: The 'z' and 'description' fields are optional*\n", inline=False)
    
    # Get command
    embed.add_field(name="$get  <name>", value="> *Get the coordinates of a location with the given name.*\n> *Shorthand: '$g'*", inline=False)

    # Search command
    embed.add_field(name="$search  <query>  [search_mode]", 
                    value="> *Search for locations based on given query.*\n> *Shorthand: '$sr'*\n> *Note: 'search_mode' can be set to either by location name or by author name. Default is search by location name*", 
                    inline=False)

    # List command
    embed.add_field(name="$list", value="> *List all saved locations, server-wide.*\n> *Shorthand: '$l'*", inline=False)

    # Remove command
    embed.add_field(name="$remove  <name>", value="> *Remove the location with the given name.*\n> *Shorthand: '$r', '$rem'*\n> *Note: Only the original author of the location can remove it.*", inline=False)

    # Remove command
    embed.add_field(name="$distance  <nameA>  <nameB>", value="> *Calculate the distance between locations A and B*\n> *Shorthand: '$d', '$dist'*", inline=False)

    # Setting the footer
    embed.set_footer(text="Bot created by Warsna#4581")

    # Send back the embed representation for distance
    await ctx.channel.send(embed=embed)

# ==================== SCRIPT RELATED ========================================

# Function to set up the argparser
def setup_argparse():
    parser = argparse.ArgumentParser(description="Minecraft Discord Bot... by: Nabeel Warsalee")

    parser.add_argument('--dev', action="store_true", help="Activate dev mode")

    return parser.parse_args()

# Check if running in dev mode
args = setup_argparse()

if args.dev:
    print("Running in developer mode...")
    use_local =True
else:
    use_local =False

# Create Operator instance to provide functions
op = Operator(use_local , conf)

# Run the bot instance
client.run(conf.DISCORD_TOKEN)