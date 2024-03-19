import os
import csv
import time
import random
import requests
from pathlib import Path

import replicate
import pandas as pd

from config.configuration import WORKING_DIRECTORY, THREADS_PATH, DATA_DIRECTORY

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

def write_iterable(file_path:str, iterable:list | dict) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        for item in iterable:
            file.write(str(item) + ",")
    return None

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

def setUserAmount(df:pd.DataFrame, username, new_money_value):
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