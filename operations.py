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

        # The table name that is used for locations
        self.location_table_name = "LOCATIONZ"

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

        # Dictionary to map the field_to_edit parameter to the actual name of the column in the sql table
        self.field_map = { 'name' : 'name', 'x' : 'x_coord', 'y' : 'z_coord', 'z' : 'y_coord', 'desc' : 'description'}

    # Function to add location data to a list or to a database
    def add_location(self, name, user, x, y, z=0, desc="N/A"):
        """Function to add a set of location data to the database or list of locations (depending on run mode)

        Args:
            name (str): Name of the potential new location entry
            x    (int): X coordinate of the potential location
            y    (int): Y coordinate of the potential location
            z    (int): Z coordinate of the potential location (default=0)
            desc (str): Description text of the new location (default="N/A")

        Returns:
            bool: Returns whether the addition of the new location data was successful
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
            try:
                # Connect to the PostgreSQL DB via the database URL stored in config
                con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
                # Create cursor to perform commands
                cur = con.cursor()
                # Execute PostgreSQL command to add new location data
                cur.execute("INSERT INTO {} (ID,NAME,AUTHOR,DISCORD_NAME,DISCORD_ID,X_COORD,Y_COORD,Z_COORD,DESCRIPTION) VALUES ('{}', '{}', '{}', '{}', '{}', {}, {}, {}, '{}')".format(self.location_table_name, uuid.uuid4(), self.quote_escape(name), self.quote_escape(user.name.split("#")[0]), self.quote_escape(user.name), user.id, int(x), int(y), int(z), self.quote_escape(desc)))
                # Commit changes to the database and close connection to database
                con.commit()
                con.close()
            except Exception as e:
                print("Error adding new entry due to: {}".format(e))
                return False
        
        return True

    # Function to verify required arguments of location data
    def verify_location_data(self, name, x, y, z, desc):
        """Function to verify a set of location data from the database

        Args:
            name (str): Name of the potential new location entry
            x    (int): X coordinate of the potential location
            y    (int): Y coordinate of the potential location
            z    (int): Z coordinate of the potential location
            desc (str): Description text of the new location

        Returns:
            bool: Returns whether all provided location data is valid (return true if so)
        """
        if name == None or x == None or y == None or z == None or desc == None:
            print("Name, x, y, z or description is set to None... Returning false.")
            return False

        # Attempts to cast x and y into ints to verify if they are ints
        try:
            int(x)
            int(y)
            int(z)
        except ValueError:
            print("Entered x, y or z value is not an integer... Returning false.")
            return False
        else:
            return True
    
    # Function to get location data
    def get_location_data(self, search_token, query="name"):
        """Function to retrieve a set of location data from the database (or from the dictionary if in local mode)

        Searches based on either location name or by author name.
        By default it searches based on location name unless specified for author name.

        Args:
            search_token (str): Name of what is being searched for
            query        (str): Query method, i.e. search by location name or by author name (Default: location name)
        
        Returns:
            dict or bool or None: Returns the location data in a dictionary/map format, returns False if it's an illegal query and returns None if no location was found 
        """
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
            cur.execute("SELECT name, author, discord_id, x_coord, y_coord, z_coord, description, id FROM {} WHERE name='{}'".format(self.location_table_name, self.quote_escape(search_token)))

            # Fetch all results
            results = cur.fetchall()
            
            # Check if results are empty, if so then no location was found
            if len(results) == 0:
                searched_location_data = None
            # Check if we got more than one result, if so return False, something not right...
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
        """Function to remove a set of location data based on its ID within the database

        Args:
            id (str): ID of the set of location data to remove

        Returns:
            bool: Returns whether the removal was successful or not
        """
        # Local testing case
        if self.local:
            print("Oops, remove for local mode (i.e. --dev mode) is unsupported. Either implement it or deal with it.")
            pass
        
        # Using PostgreSQL
        else:
            try:
                # Connect to the database
                con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
                # Create cursor to perform commands
                cur = con.cursor()
                # Delete location entry based on the ID
                cur.execute("DELETE from {} where ID='{}'".format(self.location_table_name, id))
                # Commit DB changes
                con.commit()
                # Close DB connection
                con.close()
            except Exception as e:
                print("ERROR while attempting to remove location with ID {} due to: {}".format(id, e))
                return False
        
        return True
    
    # Function to remove a location entry based on the ID that it was given...
    def edit_location_data(self, id, field_to_edit, edit):
        """Function to edit a field within the location data based on its ID within the database

        Args:
            id            (str): ID of the set of location data to remove
            field_to_edit (str): Name of the field to edit, can only be one of the following 'name', 'x', 'y', 'z', 'desc'
            edit          (str): The new value to edit the field with

        Returns:
            bool: Returns whether the edit was successful or not
        """

        # Local testing case
        if self.local:
            print("Oops, remove for local mode (i.e. --dev mode) is unsupported. Either implement it or deal with it.")
            pass
        
        # Using PostgreSQL
        else:
            try:
                # Connect to the database
                con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
                # Create cursor to perform commands
                cur = con.cursor()
                # Delete location entry based on the ID
                print("UPDATE {} SET {}='{}' where ID='{}'".format(self.location_table_name, self.field_map[field_to_edit], edit, id))
                cur.execute("UPDATE {} SET {}='{}' where ID='{}'".format(self.location_table_name, self.field_map[field_to_edit], edit, id))
                # Commit DB changes
                con.commit()
                # Close DB connection
                con.close()
            except Exception as e:
                print("ERROR while attempting to edit location with ID {} due to: {}".format(id, e))
                return False
        
        return True
    
    # Function to search for locations based on search token and query type
    def search_locations(self, search_token, query="name"):
        """Function to search for location data from the database based on a given search token (or from the dictionary if in local mode)

        Searches based on either location name or by author name or to just retrieve all location data from the DB
        By default it searches based on location name unless specified for author name or all.

        Args:
            search_token (str): Name of what is being searched for
            query        (str): Query method, i.e. search by location name or by author name (Default: location name)
        
        Returns:
            list or bool: Returns a list of location data in a dictionary/map format and returns False if it's an illegal query
        """
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
            try:
                # Connect to the database
                con = psycopg2.connect(self.config.DATABASE_URL, sslmode='require')
                # Create cursor to perform commands
                cur = con.cursor()

                # Search for location based on location name
                if query == "name":
                    cur.execute("SELECT name, author, x_coord, y_coord, z_coord, description FROM {} WHERE UPPER(name) LIKE UPPER('%{}%')".format(self.location_table_name, search_token))
                
                # Search for location based on author name
                elif query == "author":
                    cur.execute("SELECT name, author, x_coord, y_coord, z_coord, description FROM {} WHERE UPPER(author) LIKE UPPER('%{}%')".format(self.location_table_name, search_token))
                
                # Retrieve all locations
                elif query == "all":
                    cur.execute("SELECT name, author, x_coord, y_coord, z_coord, description FROM {}".format(self.location_table_name))

                # Fetch all results
                rows = cur.fetchall()
                # Close DB connection
                con.close()

            except Exception as e:
                print("ERROR: Unable to search for locations with key '{}' in mode '{}' due to: {}".format(search_token, query, e))
                return False
            
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

        
        return found_locations

    # Function to create string of location data in a nice format
    def location_str(self, location):
        """Function that creates a string representation for the given location data

        Args:
            location (dict): Location data that is to be stringified

        Returns:
            str: Returns the given location in a neat string format
        """
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
        """Function to create a discord embed object for displaying data for a single location

        Args:
            location (dict): Location data in dict format

        Returns:
            embed: Returns a discord embed object of the location's information, nicely formatted to be sent to the text channel 
        """
        embed = discord.Embed(
            title = location["name"],
            color = discord.Color.green()
        )

        embed.add_field(name="Author", value=location["author"]["name"], inline=False)
        embed.add_field(name="Coordinates (x, y, z)", value="{}, {}, {}".format(location["coords"]["x"], location["coords"]["z"], location["coords"]["y"]), inline=False)

        if location["desc"] is not None:
            embed.add_field(name="Description", value=location["desc"], inline=False)

        return embed

    # Function to print out location data in a nice format
    def short_location_str(self, location):
        """Function to create a short version of a string representation for a single location data
        
        Args:
            location (dict): Location data in dict format

        Returns:
            str: Returns the short string to represent the location data
        """
        # Format follows as so
        # <name_of_location> <author> (x, y)

        str = "{:<15} {:<15} ({}, {})".format(location["name"], location["author"]["name"], location["coords"]["x"], location["coords"]["y"])

        return str

    # Function to return a list of location data that is currently being stored
    def location_list(self):
        """Function to print the entire list of locations currently being stored in this object's list of locations

        Meant to be used while in dev mode...

        Returns:
            str: Returns string that represents the list of all locations in the list
        """
        str = "List of Registered Locations...\n\n"

        for entry in self.locations:
            str += self.short_location_str(entry) + "\n"

        return str
    
    # Function to return a list of locations stored within an embed
    def location_list_embed(self, collection=None, search_token=None, query=None):
        """Function to create a discord embed object for displaying a list of location data that is in the database

        Will create a list for all entered location data if no list, search_token and query were not provided.

        If a collection of locations was provided and search token and query were provided, it creates a list of locations based on the search result

        Args:
            collection   (list): List of location data that is pre provided (Default: None)
            search_token  (str): Token to base the search for locations (Default: None)
            query         (str): How to search for the locations, if searching (Default: None)

        Returns:
            embed: Returns a discord embed object of the location's information, nicely formatted to be sent to the text channel 
        """
        # If no location list was provided, use the entire location list
        if collection is None:
            if self.local:
                collection = self.locations
            else:
                collection = self.search_locations('', query="all")
                desc = "List of all registered locations..."

        else:
            desc = "Search results for {}: '{}'".format(query, search_token)
        
        desc += "\n*(x, y, z) - author*"

        embed = discord.Embed(
            title = "Locations",
            description = desc,
            color = discord.Color.green()
        )

        # In case search for locations on DB side failed
        if collection == False:
            embed.add_field(name="Error retrieving locations...", value="...", inline=False)
            return embed

        # Traverse each location entry and create new embed field to add into list
        for entry in collection:
            embed.add_field(name=entry["name"], value="({}, {}, {}) - {}".format(entry["coords"]["x"], entry["coords"]["z"], entry["coords"]["y"], entry["author"]["name"]), inline=False)

        if len(collection) == 0:
            embed.add_field(name="No locations found...", value="...", inline=False)

        return embed

    # Function to calculate the distance between two given location points
    def distance(self, name1, name2):
        """Function to calculate the distance between two locations with given names

        Args:
            name1 (str): Name of the first location to consider in the calculation
            name2 (str): Name of the second location to consider in the calculation

        Returns:
            bool, float or str: Returns whether the calculation was successful and the calculated distance or a message as to why the calculation failed
        """
        # Retrieve both locations from database
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

    def navigation(self, loc1, loc2):
        """Function to calculate the directions between two locations with given names

        Args:
            pointA (dict): First location to consider in the calculation
            pointB (dict): Second location to consider in the calculation

        Returns:
            bool, float or str: Returns whether the calculation was successful and the calculated angle/navigation or a message as to why the calculation failed
        """

        # Grabbing the x and y of both locations and putting them in tuples for ease of use
        p1 = (loc1["coords"]["x"], loc1["coords"]["y"])
        p2 = (loc2["coords"]["x"], loc2["coords"]["y"])

        print("p1 - {}".format(p1))
        print("p2 - {}".format(p2))

        # Calculate deltas between x and y coords
        x_delta = p1[0] - p2[0]
        y_delta = p1[1] - p2[1]

        print("delta x: {} | delta y: {}".format(x_delta, y_delta))

        # Calculate angle
        myAngle = int(math.atan((y_delta)/(x_delta)) * (180/math.pi))
        print("arctan(O/A) = {} deg".format(myAngle))

        # Case of negative angle return from arctan
        if myAngle < 0:
            myAngle = 360 + myAngle

        # Create cardinal locations dict
        cardinalDirs = { 0 : "E", 45 : "NE", 90 : "N", 135 : "NW", 180 : "W", 225 : "SW", 270 : "S", 315 : "SE", 360 : "E" }

        # Calculate the remainder and true bearing
        remainder = myAngle % 45

        print("Angle: {} | remainder: {} | myAngle-rem = {} | myAngle+rem = {}".format(myAngle, remainder, myAngle - remainder, myAngle + remainder))
        
        direction = "NONE"

        if (myAngle + remainder) in cardinalDirs:
            print("subtraction")
            direction = cardinalDirs[(myAngle - remainder)]
        elif (myAngle - remainder) in cardinalDirs:
            print("addition")
            direction = cardinalDirs[(myAngle - remainder)]
        else:
            print("Angle {} deg and remainder {} deg don't sync up to a specific direction...".format(myAngle, remainder))

        return True, direction, myAngle

    def navigation_locations(self, pointA, pointB):
        """Function to calculate the directions between two locations with given names

        Args:
            pointA (str): Name of the first location to consider in the calculation
            pointB (str): Name of the second location to consider in the calculation

        Returns:
            bool, float or str: Returns whether the calculation was successful and the calculated angle/navigation or a message as to why the calculation failed
        """
        # Retrieve both locations from database
        loc1 = self.get_location_data(pointA)
        loc2 = self.get_location_data(pointB)

        # Ensure location 1 was found properly
        if loc1 is None:
            return False, "First location could not be found"
        # Ensure location 2 was found properly
        if loc2 is None:
            return False, "Second location could not be found"

        angles = self.navigation(loc1, loc2)

        return angles
    
    def navigation_locations_coords(self, pointA, pointB):
        """Function to calculate the directions between a set of coordinate and a location

        Args:
            pointA (str): Name of the first location to consider in the calculation
            pointB (str): Name of the second location to consider in the calculation

        Returns:
            bool, float or str: Returns whether the calculation was successful and the calculated angle/navigation or a message as to why the calculation failed
        """
        # Retrieve both locations from database
        loc1 = pointA
        loc2 = self.get_location_data(pointB)

        # Ensure location 1 was found properly
        if loc1 is None:
            return False, "First location could not be found"
        # Ensure location 2 was found properly
        if loc2 is None:
            return False, "Second location could not be found"

        angles = self.navigation(loc1, loc2)

        return angles
    
    # Function to create a distance embed tile
    def create_distance_embed(self, name1, name2, distance):
        """Function to calculate the distance between two locations with given names

        Args:
            name1      (str): Name of the first location to consider in the calculation
            name2      (str): Name of the second location to consider in the calculation
            distance (float): The distance between the two locations

        Returns:
            embed: Returns a discord embed object that contains all the distance related information between the two points
        """
        embed = discord.Embed(
            title = "Distance Summary",
            description = "Distance between locations '{}' and '{}'.".format(name1, name2),
            color = discord.Color.green()
        )

        # Distance
        embed.add_field(name="Distance", value="{:.0f} blocks".format(distance), inline=False)

        # Time to reach by walking
        embed.add_field(name=":person_walking: Walk time", value="~{:.1f} seconds".format(distance/self.metrics["speed"]["player"]["walk"]), inline=False)

        # Time to reach by running
        embed.add_field(name=":woman_running: Running time", value="~{:.1f} seconds".format(distance/self.metrics["speed"]["player"]["run"]), inline=False)

        # Time to reach by horse
        embed.add_field(name=":racehorse: Average time by horse", value="~{:.1f} seconds".format(distance/self.metrics["speed"]["horse"]["walk"]), inline=False)

        return embed

    # Function to create a distance embed tile
    def create_navigation_embed(self, pointA, pointB, direction, angle):
        """Function to display the directions between two locations

        Args:
            name1      (str): Name of the first location to consider in the calculation
            name2      (str): Name of the second location to consider in the calculation
            distance (float): The distance between the two locations

        Returns:
            embed: Returns a discord embed object that contains all the distance related information between the two points
        """
        embed = discord.Embed(
            title = "Navigation Summary",
            description = "Directions to navigate from '{}' to '{}'".format(pointA['name'], pointB['name']),
            color = discord.Color.green()
        )

        # Dictionary to convert shorthand cardinal name to the full one
        expand_card_dir = {"N" : "North", "S" : "South", "E" : "East", "W" : "West", "NW" : "North West", "NE" : "North East", "SW" : "Sout West", "SE" : "Sout East",}

        # Distance
        embed.add_field(name=":compass: Direction", value="{} ({})".format(expand_card_dir[direction], direction), inline=False)

        # Angle
        embed.add_field(name="Exact Angle (East is 0°, North 90°, etc...)", value="{}°".format(angle), inline=False)

        return embed
    
    # Function to convert single or double quotes in a string to it's escaped variant
    def quote_escape(self, string, escape=True):
        """Function to escape all single quotes in a string to make it valid for PostgreSQL use

        It will also de-escape quotes for a string that was just recently extracted from a PostgreSQL table

        Args:
            string  (str): The string that is to have all its single quotes escaped (or de-escaped)
            escape (bool): Flag for whether to escape the single quotes in the string or to de-escape (Default: True, i.e. escape single quotes)
        
        Returns:
            str: Returns the string in its single quote escaped or de-escaped format.
        """
        if escape:
            # Replace all single quotes with a fake doubled quote (i.e.)
            new_string = string.replace("\'", "''")
        else:
            new_string = string.replace("''", "\'")
        
        return new_string

