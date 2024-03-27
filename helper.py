import os
import time
import random

import pandas as pd

from config.configuration import WORKING_DIRECTORY

# copied from geeks for geeks website
# modified to take Card objects

def slugify(string):
    new_string = ""
    no_nos = [
        "\\",
        "/",
        "\'",
        "\"",
        "|",
        ":",
        "*",
    ]
    for letter in string:
        if letter not in no_nos:
            new_string += letter
    return new_string

def get_furry_image():
    time.sleep(3)
    os.chdir(f"{WORKING_DIRECTORY}/images/furries") # set cwd to images/furries folder
    images_directory_iteratable = os.scandir()
    furry_names = []
    base_path = os.getcwd()
    for image in images_directory_iteratable:
        furry_names.append(f'{image.name}')
    index = random.randint(0, len(furry_names) - 1)
    os.chdir(WORKING_DIRECTORY)
    return f"{base_path}\\{furry_names[index]}"

def createUserIfNone(df:pd.DataFrame, username:str):
    """Creates a user in the DataFrame if they don't already exist."""
    users = list(df.Usernames)
    # if member isn't in dataframe already, put them in and give them 100 GleepCoins
    if username not in users:
        df.loc[len(df.index)] = [username, 1000]

def setUserAmount(df:pd.DataFrame, username, new_money_value):
    createUserIfNone(df, username)
    user_index = df.index[df['Usernames'] == username].tolist()
    user_index = user_index[0]
    df.at[user_index, "GleepCoins"] = int(new_money_value)

def getUserAmount(df, username) -> int:
    user_index = df.index[df['Usernames'] == username].tolist()
    user_index = user_index[0]
    current_amount = df.at[user_index, "GleepCoins"]
    return int(current_amount)

def getAllAmounts(df) -> str:
    return df.to_string()