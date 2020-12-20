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
# Remove default help command and replace by custom one..
client.remove_command('help')

#Checks if the bot is ready and if it is it prints Bot is ready
@client.event
async def on_ready():
    """Function to start the bot

    Sets bot status to the help command and prints to stdout when the bot is ready.

    """
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
async def save_coords(ctx, name, x, z, y, desc="N/A"):
    """Bot Command to add a new location and its set of data

    Args:
        name (str): Name of the new location
        x    (int): X coordinate of the new location
        z    (int): Z coordinate of the new location
        y    (int): Y coordinate of the new location
        desc (str): (Optional) Description of the location

    Returns:
        Nothing, but does send back a message to the text channel the command was sent to.
    """
    # Verify main data is valid
    if not op.verify_location_data(name, x, y, z, desc):
        print("WARN - Entered location data not valid, informing user")
        await ctx.channel.send("The entered location data is invalid, please ensure you are entering in the proper types.")
        return

    # Verify that another location was not already registered under same name
    searched = op.get_location_data(name)

    # If no data was found
    if searched != None:
        await ctx.channel.send("A location already exists under the name '{}'. Please choose a different name...".format(name))
        return

    # Save instance of the user who sent the message
    user = ctx.message.author

    op.add_location(name, user, x, y, z, desc)

    print("OK - Successfully entered in location data.")
    await ctx.channel.send("New location saved under name '**{}**' located at (**{}**, **{}**)!".format(name, x, y))
    return

# Command to add new location
@client.command(aliases = ["get", "g"])
async def get_coords(ctx, name):
    """Bot command to get a location based on the given name

    Args:
        name (str): Name of the location to get

    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
    # Search for the location data
    searched = op.get_location_data(name)
    
    # If no data was found
    if searched == None:
        await ctx.channel.send("No location data was found under the name '{}', please verify that the name you entered is correct and try again.".format(name))
        return
    
    # If multiple data was found...
    if searched == False:
        await ctx.channel.send("Multiple locations found under the name '{}'. Please be specific.".format(name))
        return

    # Means search found something, print it to user.
    await ctx.channel.send(embed=op.location_embed(searched))
    return

# Command to remove registered location based on name
@client.command(aliases = ["remove", "r", "rem"])
async def remove_coords(ctx, name):
    """Bot command to remove a location based on its name

    Args:
        name (str): Name of the location to remove
    
    Returns:
        Nothing, but does send back a message to the text channel the command was sent to.
    """
    # Get the location that was desired to be removed
    searched = op.get_location_data(name)
    
    # If no data was found, tell user
    if searched == None:
        await ctx.channel.send("No location data was found under the name '{}', please verify that the name you entered is correct and try again.".format(name))
        return
    
    # If multiple data was found...
    if searched == False:
        await ctx.channel.send("Multiple locations found under the name '{}'. Please be specific.".format(name))
        return

    print(searched)

    # Save instance of the user who sent the message
    user = ctx.message.author

    print("Current user id: {} | Location author id: {}".format(user.id, searched["author"]["id"]))

    # Check to make sure that the user calling the remove is the owner of that location
    if str(user.id) != searched["author"]["id"] and str(user.id) != conf.DISCORD_USER_ID:
        await ctx.channel.send("You are not the author of this location entry. Only the author of a location can remove it. Nice try bud.")
        return

    # Means entry exists, user is the correct author, therefore remove it based on ID of location
    status = op.remove_location_data(searched['id'])

    if status is True:
        await ctx.channel.send("Successfully removed location. Goodbye '{}'!".format(name))
        return

# Command to edit registered location based on name
@client.command(aliases = ["edit", "e", "ed"])
async def edit_coords(ctx, name, field_to_edit, edit):
    """Bot command to edit a specific field of a location based on its name

    Args:
        name          (str): Name of the location to remove
        field_to_edit (str): Name of the field to edit, can only be one of the following 'name', 'x', 'y', 'z', 'desc'
        edit          (str): The new value to edit the field with
    
    Returns:
        Nothing, but does send back a message to the text channel the command was sent to.
    """
    # Get the location that was desired to be removed
    searched = op.get_location_data(name)
    
    # If no data was found, tell user
    if searched == None:
        await ctx.channel.send("No location data was found under the name '{}', please verify that the name you entered is correct and try again.".format(name))
        return
    
    # If multiple data was found...
    if searched == False:
        await ctx.channel.send("Multiple locations found under the name '{}'. Please be specific.".format(name))
        return

    if field_to_edit not in ['name', 'x', 'y', 'z', 'desc']:
        await ctx.channel.send("'{}' is not a valid field to edit, please choose one of these fields: name, x, y, z, desc".format(field_to_edit))
        return

    # Save instance of the user who sent the message
    user = ctx.message.author

    print("Current user id: {} | Location author id: {}".format(user.id, searched["author"]["id"]))

    # Check to make sure that the user calling the remove is the owner of that location
    if str(user.id) != searched["author"]["id"] and str(user.id) != conf.DISCORD_USER_ID:
        await ctx.channel.send("You are not the author of this location entry. Only the author of a location can edit it. Nice try bud.")
        return

    # Means entry exists, user is the correct author, therefore remove it based on ID of location
    status = op.edit_location_data(searched['id'], field_to_edit, edit)

    if status is True:
        await ctx.channel.send("Successfully edited location '{}'!".format(name))
        return

# Command to list all registered locations
@client.command(aliases = ["list", "l"])
async def list_coords(ctx):
    """Bot command to list all current registered locations
    
    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
    await ctx.channel.send(embed=op.location_list_embed())
    return

# Command to list locations based on search values
@client.command(aliases = ["search", "sr"])
async def search_coords(ctx, search_token, query="name"):
    """Bot command to get a location based on the given name

    Args:
        search_token (str): What is being searched
        query        (str): (Optional) How it is searching, i.e. by name or author (Default: 'name')

    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
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
    """Bot command to get a location based on the given name

    Args:
        nameA (str): Name of locationA, the first location to use in the distance calculation
        nameB (str): Name of locationB, the second location to use in the distance calculation

    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
    # Calculate the distance
    status, response = op.distance(nameA, nameB)

    # Ensure calculation went smooth
    if status == False:
        await ctx.channel.send("Unable to calculate distance between the two locations.\nDue to: {}".format(response))

    distance_embed = op.create_distance_embed(nameA, nameB, response)

    # Send back the embed representation for distance
    await ctx.channel.send(embed=distance_embed)

# Command to compute the distance between two location points and return other intresting data
@client.command(aliases = ["nav", "n"])
async def navigate(ctx, fromLocation, toLocation):
    """Bot command to navigate from the from location to the to location

    Args:
        fromLocation (str): Name of locationA, the first location to use in the navigation calculation
        toLocation   (str): Name of locationB, the second location to use in the navigation calculation

    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
    # Calculate the distance
    status, direction, angle = op.navigation_locations(fromLocation, toLocation)

    # Ensure calculation went smooth
    if status == False:
        await ctx.channel.send("Unable to calculate directions between the two locations.\nDue to: {}".format(response))

    # Grab both location points data (i.e. name, and other metadata)
    pointA = op.get_location_data(fromLocation)
    pointB = op.get_location_data(toLocation)

    # Create embed to display navigation data
    nav_embed = op.create_navigation_embed(pointA, pointB, direction, angle)

    # Send back the embed representation for navigation
    await ctx.channel.send(embed=nav_embed)

# Command to compute the distance between two location points and return other intresting data
@client.command(aliases = ["navigatec", "navc", "nc"])
async def navigate_coords(ctx, x, y, toLocation):
    """Bot command to navigate from the from location to the to location

    Args:
        x            (int): Int of the x coordinate to compute directions from
        y            (int): Int of the y coordinate to compute directions from (NOTE: This is actually the z coordinate in minecraft, but internally in my head its y :P)
        toLocation   (str): Name of locationB, the second location to use in the navigation calculation

    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
    # Check entered coords
    valid = op.verify_location_data("null", x, y, 0, "N/A")
    
    if valid == False:
        await ctx.channel.send("The provided coordinates are not valid, please enter valid coordinates...")
        return

    # Create new dict object for from location based on given coordinates
    pointA =    {
                        "name" : "(x={}, z={})".format(x, y),
                        "coords" : { "x" : int(x), "y" : int(y) }
                }

    # Calculate the distance
    status, direction, angle = op.navigation_locations_coords(pointA, toLocation)

    # Ensure calculation went smooth
    if status == False:
        await ctx.channel.send("Unable to calculate directions between the two locations.\nDue to: {}".format(response))

    # Grab to location point data (i.e. name, and other metadata)
    pointB = op.get_location_data(toLocation)

    # Create embed to display navigation data
    nav_embed = op.create_navigation_embed(pointA, pointB, direction, angle)

    # Send back the embed representation for navigation
    await ctx.channel.send(embed=nav_embed)

# Help command
@client.command(aliases = ["h"])
async def help(ctx):
    """Function for help command

    Creates an embed Discord object to present all available commands to the user

    Returns:
        Nothing, but does send an embedded object as a message to the text channel the command was sent to.
    """
    # Create new embed to add in help information
    embed = discord.Embed(
        title = "Help Menu",
        description = "List of commands for Minecraft-Bot\n\nNote: *For any entries that are text (i.e. words with spaces), you must enclose them with double quotes in order for them to be recognized.*\n\nCommand prefix: **$**",
        color = discord.Color.green()
    )

    # Save command
    embed.add_field(name="$save  <name>  <x>  <y>  <z>  [description]", value="> *Save a set of coordinates under the given name.*\n> *Shorthand: '$sv'*\n> *Note: The 'description' field is optional*\n", inline=False)
    
    # Get command
    embed.add_field(name="$get  <name>", value="> *Get the coordinates of a location with the given name.*\n> *Shorthand: '$g'*", inline=False)

    # Search command
    embed.add_field(name="$search  <query>  [search_mode]", 
                    value="> *Search for locations based on given query.*\n> *Shorthand: '$sr'*\n> *Note: 'search_mode' can be set to either by location name or by author name. Default is search by location name*", 
                    inline=False)

    # List command
    embed.add_field(name="$list", value="> *List all saved locations, server-wide.*\n> *Shorthand: '$l'*", inline=False)

    # Edit command
    embed.add_field(name="$edit  <name>  <entry_to_edit>  <new_value>", 
                    value="> *Edit a specific entry on the location with the given name.*\n> *Shorthand: '$e', '$ed'*\n> *Names of fields to edit: name, x, y, z, desc*\n> *Note: Only the original author of the location can edit it.*", 
                    inline=False)

    # Remove command
    embed.add_field(name="$remove  <name>", value="> *Remove the location with the given name.*\n> *Shorthand: '$r', '$rem'*\n> *Note: Only the original author of the location can remove it.*", inline=False)

    # Distance command
    embed.add_field(name="$distance  <nameA>  <nameB>", value="> *Calculate the distance between locations A and B*\n> *Shorthand: '$d', '$dist'*", inline=False)

    # Navigation/Directions command
    embed.add_field(name="$navigate  <nameA>  <nameB>", value="> *Calculate directions between locations A and B*\n> *Shorthand: '$nav', '$n'*", inline=False)

    # Navigation/Directions for coordinates command
    embed.add_field(name="$navigatec  <x>  <z>  <nameB>", value="> *Calculate directions between given coordinates and a known location*\n> *Shorthand: '$navc', '$nc'*", inline=False)

    # Setting the footer
    embed.set_footer(text="Bot created by Warsna#4581")

    # Send back the embed representation for distance
    await ctx.channel.send(embed=embed)

# ==================== SCRIPT RELATED ========================================

# Function to set up the argparser
def setup_argparse():
    """Function to set up the argparser for the command line arguments

    Supported arguments: 
        --dev: To turn on developper mode and store locations in memory instead of a database

    Returns:
        Returns arguments parser object that contains the parsed args
    """
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

# Create Operator instance to provide database operations and embed creation functions
op = Operator(use_local , conf)

# Run the bot instance
client.run(conf.DISCORD_TOKEN)