from config.config import WORKING_DIRECTORY, THREADS_PATH, DATA_DIRECTORY
import pandas as pd
import replicate
import requests
import random
import time
import os
import csv

# copied from geeks for geeks website
# modified to take Card objects
def bubbleSortCards(cards_list:list) -> None:
    """
    Function sorts a list of Card objects, in place."""
    n = len(cards_list)
    # optimize code, so if the array is already sorted, it doesn't need
    # to go through the entire process
    swapped = False
    # Traverse through all array elements
    for i in range(n-1):
        # range(n) also work but outer loop will
        # repeat one time more than needed.
        # Last i elements are already in place
        for j in range(0, n-i-1):
 
            # traverse the array from 0 to n-i-1
            # Swap if the element found is greater
            # than the next element
            if cards_list[j].pip_value > cards_list[j + 1].pip_value:
                swapped = True
                cards_list[j], cards_list[j + 1] = cards_list[j + 1], cards_list[j]
         
        if not swapped:
            # if we haven't needed to make a single swap, we
            # can just exit the main loop.
            return


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

def cleanAudioFile(song_name):
    os.chdir(DATA_DIRECTORY)
    # in data directory 

    files = os.listdir(os.getcwd())
    for file in files:
        # if the file minus the .mp3 extension equals input song name
        if str(file[:-4]) == song_name:
            try:
                os.remove(file)
            except Exception as e:
                print(e)
    # change back to top level directory
    os.chdir(WORKING_DIRECTORY)

def clearAllAudio():
    os.chdir(DATA_DIRECTORY)
    files = os.listdir(os.getcwd())
    for file in files:
        # delete any songs that are webm or ytdl extensions
        if (file[-5:] == ".webm") or (file[-5:] == ".ytdl") or (file[-4:] == ".mp3"):
            way = os.getcwd()
            way += f"\\{file}"
            try:
                os.remove(way)
            except Exception as e:
                print(e)

    os.chdir(WORKING_DIRECTORY)

def fileExists(file_path:str) -> bool:
    """Checks whether the file path exists in the data directory."""
    os.chdir(DATA_DIRECTORY)
    files = os.listdir(os.getcwd())
    for file in files:
        if file_path == str(file):
            return True
    return False

def deleteSongsBesidesThese(slugified_song_titles:list) -> None:
    """Deletes all .webm, .ytdl, and .mp3 files which are not included in the song_paths parameter.\nIn other words, song paths provided in song_paths are safe from being deleted."""
    os.chdir(DATA_DIRECTORY)
    files = os.listdir(os.getcwd())
    for file in files:
        # delete any songs that are webm or ytdl extensions
        if ((file[-5:] == ".webm") or (file[-5:] == ".ytdl") or (file[-4:] == ".mp3") or (file[-5:] == ".part")) and (str(file) not in slugified_song_titles):
            way = os.getcwd()
            way += f"\\{file}"
            try:
                os.remove(way)
            except Exception as e:
                print(e)

    os.chdir(WORKING_DIRECTORY)

def write_iterable(file_path:str, iterable:list | dict) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        for item in iterable:
            file.write(str(item) + ",")
    return None

def get_image(args:str):
    model = replicate.models.get('borisdayma/dalle-mini')
    output:list[dict] = model.predict(prompt=args, n_predictions=1)
    # print(type(output)) # output type is list
    # print(type(output[0])) #each index of list is a dictionary
    # print(output[0]) # each dictionary contains {'image': url} pairs.
    dic = output[0]
    image_url = dic['image']
    response = requests.get(image_url)
    img_destination = f'{WORKING_DIRECTORY}/images/image.png'
    with open(img_destination, 'wb') as file:
        file.write(response.content)
    return img_destination


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

def readThreads() -> dict[str, int]:
    """
    Reads threads.csv file into a dictionary format."""
    with open(THREADS_PATH, "r") as file:
        threads_dict = {}
        reader = csv.reader(file) 
        #skip first row of csv
        next(reader)
        for row in reader:
            threads_dict[row[0]] = int(row[1])
    return threads_dict

def writePlayerAndThread(player, thread_id) -> None:
    with open(THREADS_PATH, "a") as file:
        file.write(f"\n{player.name},{thread_id}")
    return
