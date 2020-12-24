# minecraft-discord-bot

## Description
Discord bot that allows user to register location points in Minecraft to a database using coordinates (x, y, z). 
Users can then retrieve the location data that was saved by them or any other user, search for locations based on name or author.

Users can also calculate the distance between two registered points and calculate the directions from one location point to another.

The bot makes use of a PostgreSQL database provided by Heroku, where the instance of the bot is hosted, to store and retrieve all relevant location data. 

## Author

* Nabeel Warsalee (github:nwarsalee)

## Tools Used

[Discord Developer Portal for creating Discord Bots](https://discord.com/developers/docs/intro)

[Heroku PostgreSQL](https://www.heroku.com/postgres)

[Python 3.8](https://www.python.org)