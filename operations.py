import discord
import uuid
import argparse
import math
import psycopg2

class Operator:
    def __init__(self, local, config):
        self.local  = local
        self.config = config
        self.locations = []

        # List of valid query vars for getting a location
        self.query_types = ["name", "author", "all"]

        # Dictionary to store metrics for things
        self.metrics =  {   "speed" : 
                                        # Speed of different entities in different modes in blocks/sec
                                        {
                                            "player" :  {
                                                            "walk"  : 4.317,
                                                            "run"   : 5.612
                                                        },
                                            "horse" :   {
                                                            "walk"  : 9.0
                                                        }
                                        }
                        }

    # Function to add location data to a list or to a database
    def add_location(self, name, user, x, y, z=0, desc="N/A"):
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
            con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')

            # Create cursor to perform commands
            cur = con.cursor()

            cur.execute("INSERT INTO LOCATIONZ (ID,NAME,AUTHOR,DISCORD_NAME,DISCORD_ID,X_COORD,Y_COORD,Z_COORD,DESCRIPTION) VALUES ('{}', '{}', '{}', '{}', '{}', {}, {}, {}, '{}')".format(uuid.uuid4(), self.quote_escape(name), self.quote_escape(user.name.split("#")[0]), self.quote_escape(user.name), user.id, int(x), int(y), int(z), self.quote_escape(desc)))

            con.commit()
            con.close()

# cur.execute('''CREATE TABLE LOCATIONZ(
#     ID INT PRIMARY KEY NOT NULL,
#     NAME TEXT NOT NULL,
#     AUTHOR TEXT NOT NULL,
#     DISCORD_NAME TEXT,
#     DISCORD_ID INT,
#     X_COORD INT NOT NULL,
#     Y_COORD INT NOT NULL,
#     Z_COORD INT,
#     DESCRIPTION TEXT
#     );''')
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
            int(x)
            int(y)
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

        # Using local dict storage
        if self.local:
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
        
        # Using SQL DB
        else:
            # Connect to the database
            con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
            # Create cursor to perform commands
            cur = con.cursor()

            # Search for location with given name
            cur.execute("SELECT name, author, discord_id, x_coord, y_coord, z_coord, description, id FROM LOCATIONZ WHERE name='{}'".format(self.quote_escape(search_token)))

            # Fetch all results
            results = cur.fetchall()
            
            # Check if results are empty, if so then no location was found
            if len(results) == 0:
                searched_location_data = None
            elif len(results) > 1:
                searched_location_data = False
            else:
                # Grab first item
                first_res = results[0]

                # Create new dict for the retrieved location
                searched_location_data =  {
                                    "name" : self.quote_escape(first_res[0], escape=False),
                                    "author" : {"name" : self.quote_escape(first_res[1], escape=False), "id" : first_res[2]},
                                    "coords" : { "x" : first_res[3], "y" : first_res[4], "z" : first_res[5] },
                                    "desc" : self.quote_escape(first_res[6], escape=False),
                                    "id" : first_res[7]
                                }

            # Close DB connection
            con.close()

        return searched_location_data

    # Function to remove a location entry based on the ID that it was given...
    def remove_location_data(self, id):
        # Local testing case
        if self.local:
            pass
        
        # Using PostgreSQL
        else:
            # Connect to the database
            con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
            # Create cursor to perform commands
            cur = con.cursor()

            # Delete location entry based on the ID
            print("DELETE from LOCATIONZ where ID='{}'".format(id))
            cur.execute("DELETE from LOCATIONZ where ID='{}'".format(id))

            # Commit DB changes
            con.commit()

            # Close DB connection
            con.close()
        
        return True
    
    # Function to search for locations based on search token and query type
    def search_locations(self, search_token, query="name"):
        # Handle case of unsupported query data
        if query not in self.query_types:
            print("Unsupported query type {}, supported query types are {}".format(query, ",".join(self.query_types)))
            return False

        # List to hold all found results
        found_locations = []

        # Local dictionary, dev mode
        if self.local:
            # Traverse all location entries to search for the proper location
            for entry in self.locations:
                # Case for serach by location name
                if query == "name":
                    # Soft search, check if search key appears in location name 
                    if search_token in entry["name"]:
                        found_locations.append(entry)

                # Case for search by users name
                elif query == "author":
                    # Strict search, search key must be identical to current author name
                    if search_token == entry["author"]["name"]:
                        found_locations.append(entry)
        
        # SQL DATABASE METHOD
        else:
            # Connect to the database
            con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
            # Create cursor to perform commands
            cur = con.cursor()

            if query == "name":
                # Search for location with given name
                cur.execute("SELECT name, author, x_coord, y_coord, z_coord, description FROM LOCATIONZ WHERE UPPER(name) LIKE UPPER('%{}%')".format(search_token))
            elif query == "author":
                # Search for location with given name
                cur.execute("SELECT name, author, x_coord, y_coord, z_coord, description FROM LOCATIONZ WHERE UPPER(author) LIKE UPPER('%{}%')".format(search_token))
            elif query == "all":
                print("retrieve all records")
                # Retrieve all locations
                cur.execute("SELECT name, author, x_coord, y_coord, z_coord, description FROM LOCATIONZ")

            # Fetch all results
            rows = cur.fetchall()

            # Iterate over each search result, create dict and add to list
            for row in rows:
                # Create new dict for the retrieved location
                searched_location_data =  {
                                    "name" : self.quote_escape(row[0], escape=False),
                                    "author" : {"name" : self.quote_escape(row[1], escape=False)},
                                    "coords" : { "x" : row[2], "y" : row[3], "z" : row[4] },
                                    "desc" : self.quote_escape(row[5], escape=False)
                                }
                # Append to list
                found_locations.append(searched_location_data)

            # Close DB connection
            con.close()

        
        return found_locations

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
    def location_list_embed(self, collection=None, search_token=None, query=None):
        # If no location list was provided, use the entire location list
        if collection is None:
            if self.local:
                collection = self.locations
            else:
                collection = self.search_locations('', query="all")

            desc = "List of all registered locations..."
        else:
            desc = "Search results for {}: '{}'".format(query, search_token)
        
        embed = discord.Embed(
            title = "Locations",
            description = desc,
            color = discord.Color.green()
        )

        # Traverse each location entry and create new embed field to add into list
        for entry in collection:
            embed.add_field(name=entry["name"], value="{}, {}".format(entry["coords"]["x"], entry["coords"]["y"]), inline=False)

        if len(collection) == 0:
            embed.add_field(name="No locations found...", value="...", inline=False)

        return embed

    # Function to calculate the distance between two given location points
    def distance(self, name1, name2):
        # Retrieve both locations
        loc1 = self.get_location_data(name1)
        loc2 = self.get_location_data(name2)

        # Ensure location 1 was found properly
        if loc1 is None:
            return False, "First location could not be found"
        # Ensure location 2 was found properly
        if loc2 is None:
            return False, "Second location could not be found"

        # Grabbing the x and y of both locations and putting them in tuples for ease of use
        p1 = (loc1["coords"]["x"], loc1["coords"]["y"])
        p2 = (loc2["coords"]["x"], loc2["coords"]["y"])

        print("p1 - {}".format(p1))
        print("p2 - {}".format(p2))

        # Calculate the distance between the two points
        distance = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )

        print("Calculated distance: {}".format(distance))

        return True, distance
    
    # Function to create a distance embed tile
    def create_distance_embed(self, name1, name2, distance):
        embed = discord.Embed(
            title = "Distance Summary",
            description = "Distance between locations '{}' and '{}'.".format(name1, name2),
            color = discord.Color.green()
        )

        # Distance
        embed.add_field(name="Distance", value="{:.0f} blocks".format(distance), inline=False)

        # Time to reach by walking
        embed.add_field(name="Walk time", value="~{:.1f} seconds".format(distance/self.metrics["speed"]["player"]["walk"]), inline=False)

        # Time to reach by running
        embed.add_field(name="Running time", value="~{:.1f} seconds".format(distance/self.metrics["speed"]["player"]["run"]), inline=False)

        # Time to reach by horse
        embed.add_field(name="Average time by horse", value="~{:.1f} seconds".format(distance/self.metrics["speed"]["horse"]["walk"]), inline=False)

        return embed
    
    # Function to convert single or double quotes in a string to it's escaped variant
    def quote_escape(self, string, escape=True):
        if escape:
            # Replace all single quotes with a fake doubled quote (i.e.)
            new_string = string.replace("\'", "''")
        else:
            new_string = string.replace("''", "\'")
        
        return new_string

