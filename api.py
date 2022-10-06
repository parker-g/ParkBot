from io import BytesIO
import replicate
from PIL import Image
import requests

def get_image(args:str):
    model = replicate.models.get('borisdayma/dalle-mini')
    output = model.predict(prompt=args, n_predictions=1)
    # print(type(output)) # output type is list
    # print(type(output[0])) #each index of list is a dictionary
    # print(output[0]) # each dictionary contains {'image': url} pairs.
    output = output[0]
    image_url = output['image']
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    bytesbuffer = BytesIO()
    image.save(bytesbuffer, format='PNG')
    return bytesbuffer
