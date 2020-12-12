import os

class Config:
    """Class to store configuration of all environment variables

    Stores...
    Discord Bot Token
    Postgres SQLite Token

    """
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    SQL_TOKEN = os.environ.get('SQL_DB_TOKEN')