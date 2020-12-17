import os

class Config:
    """Class to store configuration of all environment variables

    Stores...
        Discord Bot Token
        Postgres SQLite Token

    Extracts all tokens from the OS' environment variables

    """
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    DATABASE_URL = os.environ.get('DATABASE_URL')