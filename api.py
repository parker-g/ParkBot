import replicate
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
    img_destination = 'images/image.png'
    with open(img_destination, 'wb') as file:
        file.write(response.content)
    return img_destination
