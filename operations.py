import discord
import uuid
import argparse

class Operator:
    def __init__(self, local, config):
        self.local  = local
        self.config = config
        self.locations = []
        self.query_types = ["name", "author"] # List of valid query vars for getting a location

    # Function to add location data to a list or to a database
    def add_location(self, name, user, x, y, z=None, desc=None):
        """Function to add a set of location data to the locations list of the database
        """
        # Saving to local memory in a list
        if self.local:
            # Create new location entry to add
            new_location =  {
                                "id"   : uuid.uuid4(),
                                "name" : name,
                                "author" : {"name" : user.name.split("#")[0], "discord_name" : user.name, "discord_id" : user.id},
                                "coords" : { "x" : int(x), "y" : int(y), "z" : z },
                                "desc" : desc
                            }

            # save the new location in the locations list
            self.locations.append(new_location)
        
        # Saving to SQL database
        else:
            pass

    # Function to verify required arguments of location data
    def verify_location_data(self, name, x, y):
        """Function to verify a set of location data

        Only verifies the most important info (i.e. name, and x, y coords)
        """
        if name == None or x == None or y == None:
            print("Name, x or y is set to None... Returning false.")
            return False

        # Attempts to cast x and y into ints to verify if they are ints
        try:
            x_int = int(x)
            y_int = int(y)
        except ValueError:
            print("Entered x or y value is not an integer... Returning false.")
            return False
        else:
            return True
    
    # Function to get location data
    def get_location_data(self, search_token, query="name"):
        # Handle case of unsupported query data
        if query not in self.query_types:
            print("Unsupported query type {}, supported query types are {}".format(query, ",".join(self.query_types)))
            return False

        # Placeholder for location data that we are looking for
        searched_location_data = None

        # Traverse all location entries to search for the proper location
        for entry in self.locations:
            # Case for serach by location name
            if query == "name":
                if search_token == entry["name"]:
                    searched_location_data = entry
                    break

            # Case for search by users name
            elif query == "author":
                if search_token == entry["author"]["name"]:
                    searched_location_data = entry
                    break

        if searched_location_data is None:
            print("WARN - No location data found for search of {}: {}".format(query, search_token))

        return searched_location_data
    
    # Function to create string of location data in a nice format
    def location_str(self, location):
        str = "Name: {}\n".format(location["name"])
        str += "Author: {}\n".format(location["author"]["name"])
        str += "Coordinates: ({}, {})\n".format(location["coords"]["x"], location["coords"]["y"])

        # If z coord is specified, print it out
        if location["coords"]["z"] is not None:
            str += "Altitude: {}\n".format(location["coords"]["z"])

        if location["desc"] is not None:
            str += "Description: {}\n".format(location["desc"])

        return str

    # Function to create embed object for the location's information
    def location_embed(self, location):
        embed = discord.Embed(
            title = location["name"],
            color = discord.Color.green()
        )

        embed.add_field(name="Author", value=location["author"]["name"], inline=False)
        embed.add_field(name="Coordinates", value="{}, {}".format(location["coords"]["x"], location["coords"]["y"]), inline=False)

        # If z coord is specified, print it out
        if location["coords"]["z"] is not None:
            embed.add_field(name="Altitude", value=location["coords"]["z"], inline=False)

        if location["desc"] is not None:
            embed.add_field(name="Description", value=location["desc"], inline=False)

        return embed

    # Function to print out location data in a nice format
    def short_location_str(self, location):
        # Format follows as so
        # <name_of_location> <author> (x, y)

        str = "{:<15} {:<15} ({}, {})".format(location["name"], location["author"]["name"], location["coords"]["x"], location["coords"]["y"])

        return str

    # Function to return a list of location data that is currently being stored
    def location_list(self):
        str = "List of Registered Locations...\n\n"

        for entry in self.locations:
            str += self.short_location_str(entry) + "\n"

        return str

    # Function to return a list of locations stored within an embed
    def location_list_embed(self):
        embed = discord.Embed(
            title = "Locations",
            description = "List of all registered locations...",
            color = discord.Color.green()
        )

        # Traverse each location entry and create new embed field to add into list
        for entry in self.locations:
            embed.add_field(name=entry["name"], value="{}, {}".format(entry["coords"]["x"], entry["coords"]["y"]), inline=False)

        return embed