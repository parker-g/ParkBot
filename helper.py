import replicate
import requests
import os 
import random
import time
from pathlib import Path

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


def get_furry():
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

print(get_furry())