import os
from pathlib import Path
from configparser import ConfigParser

def read(config_filename) -> dict[str, dict[str, str]]:
    """Reads an 'ini' config file, specifically ParkBot's config file, into a Python dictionary."""
    # see if any of all config values already contain a value
    # if so, keep those existing values unless a user submits something besides a blank
    here = Path(os.getcwd())
    
    result = {}
    config = ConfigParser()
    config_path = Path(os.getcwd())  / config_filename
    file = config.read(config_path)

    result["REQUIRED"] = dict(config.items(section="REQUIRED"))
    result["MUSIC"] = dict(config.items(section="MUSIC"))
    result["FOR-AUTOPLAY"] = dict(config.items(section="FOR-AUTOPLAY"))
    result["CANVAS"] = dict(config.items(section="CANVAS"))
    return result

def isInProjectRoot() -> bool:
    """Checks if the terminal is in the ParkBot root directory."""
    here = Path(os.getcwd())
    root_components = {"cogs", "data"}
    sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
    intersection = sub_dirs.intersection(root_components)
    if root_components == intersection:
        return True
    return False

def list_from_csv(csv_string:str) -> list[str]:
    terms = csv_string.split(",")
    terms = list(map(lambda string: string.strip(), terms))
    return terms    

inRoot = isInProjectRoot()
if inRoot is False:
    os.chdir("../")

config = read("bot.config") # i can see an issue arrising here where the path will need a "..." in it

required = config["REQUIRED"]

TOKEN = required["token"]
WORKING_DIRECTORY = required["working_directory"]
DATA_DIRECTORY = required["data_directory"]
BANK_PATH = required["bank_path"]
THREADS_PATH = required["threads_path"]
NAUGHTY_WORDS = list_from_csv(required["naughty_words"])
DB_OPTION = required["db_option"]

music = config["MUSIC"]
LAVALINK_URI = music["lavalink_uri"]
LAVALINK_PASS = music["lavalink_pass"]

autoplay = config["FOR-AUTOPLAY"]
SPOTIFY_CLIENT_ID = autoplay["spotify_client_id"]
SPOTIFY_CLIENT_SECRET = autoplay["spotify_client_secret"]

canvas = config["CANVAS"]
CANVAS_API_KEY = canvas["canvas_api_key"]
CANVAS_BASE_URL = canvas["canvas_base_url"]
CANVAS_COURSE_NUM = canvas["canvas_course_num"]
DATETIME_FILE = canvas["datetime_file"]