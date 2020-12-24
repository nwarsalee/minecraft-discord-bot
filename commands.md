# List of supported commands for the Minecraft Discord Bot

#### Commands for registering and retrieving locations
```$save  <name>  <x>  <y>  <z>  [description]```
Save a set of coordinates under the given name.
Shorthand: *$sv*
Note: The 'description' field is optional

```$get  <name>```
Get the coordinates of a location with the given name.
Shorthand: $g

```$search  <query>  [search_mode]```
Search for locations based on given query.
Shorthand: *$sr*
Note: 'search_mode' can be set to either by location name or by author name. Default is search by location name

```$list```
List all saved locations, server-wide.
Shorthand: *$l*

```$edit  <name>  <entry_to_edit>  <new_value>```
Edit a specific entry on the location with the given name.
Shorthand: *\$e*, *$ed*
**Names of fields to edit:** name, x, y, z, desc
Note: Only the original author of the location can edit it.

```$remove  <name>```
Remove the location with the given name.
Shorthand: *\$r*, *$rem*
Note: Only the original author of the location can remove it.

#### Commands to operate on locations

```$distance  <nameA>  <nameB>```
Calculate the distance between locations A and B.
Sends back an embedded message with the distance information as well as the time it would take to travel between the two points by walking, running and by horse.
Shorthand: *\$d*, *$dist*

```$navigate  <nameA>  <nameB>```
Calculate directions between locations A and B.
Sends back an embedded message with the direction information to get from location A to location B.
Shorthand: *\$nav*, *$n*

```$navigatec  <x>  <z>  <nameB>```
Calculate directions between given coordinates and a known location.
Sends back an embedded message with the direction information to get from the given set of coordinates to location B.
Shorthand: *\$navc*, *$nc*