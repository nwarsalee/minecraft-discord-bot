import os

class Config:
    """Class to store configuration of all environment variables

    Stores...
        Discord Bot Token
        Postgres SQLite Token
        Discord ID of admin account (i.e. account that can issue all types of commands)

    Extracts all tokens from the OS' environment variables

    """
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DISCORD_USER_ID = os.environ.get('DISCORD_USER_ID')