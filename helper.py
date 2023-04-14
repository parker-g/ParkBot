from config.config import CANVAS_API_KEY, CANVAS_BASE_URL, CANVAS_COURSE_NUM
from datetime import datetime, timedelta, date
from canvasapi import Canvas
import pandas as pd
import replicate
import requests
import asyncio
import random
import time
import os

async def cleanAudioLeftovers():
    os.chdir("data")
    files = os.listdir(os.getcwd())
    for file in files:
        if (len(str(file)) > 13) and (file[:13] == "current_audio") and (file[-4:] != ".mp3"):
            way = os.getcwd()
            way += f"\\{file}"
            os.remove(way)
    os.chdir("../")

def write_iterable(file_path:str, iterable:list | dict) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        for item in iterable:
            file.write(str(item) + ",")
    return None

def get_image(args:str):
    model = replicate.models.get('borisdayma/dalle-mini')
    output = model.predict(prompt=args, n_predictions=1)
    # print(type(output)) # output type is list
    # print(type(output[0])) #each index of list is a dictionary
    # print(output[0]) # each dictionary contains {'image': url} pairs.
    output = output[0]
    image_url = output['image']
    response = requests.get(image_url)
    img_destination = 'images/image.png'
    with open(img_destination, 'wb') as file:
        file.write(response.content)
    return img_destination


def get_furry_image():
    time.sleep(3)
    current_path = os.getcwd()
    os.chdir(f"{current_path}/images/furries") # set cwd to images/furries folder
    images_directory_iteratable = os.scandir()
    furry_names = []
    base_path = os.getcwd()
    for image in images_directory_iteratable:
        furry_names.append(f'{image.name}')
    index = random.randint(0, len(furry_names) - 1)
    os.chdir("C:/Users/rober/Documents/GitHub/dall-e-discord-bot")
    return f'{base_path}\{furry_names[index]}'


def setUserAmount(df:pd.DataFrame, username, new_money_value):
    user_index = df.index[df['Usernames'] == username].tolist()
    user_index = user_index[0]
    df.at[user_index, "GleepCoins"] = int(new_money_value)


def getUserAmount(df, username) -> int:
    user_index = df.index[df['Usernames'] == username].tolist()
    user_index = user_index[0]
    current_amount = df.at[user_index, "GleepCoins"]
    return int(current_amount)
