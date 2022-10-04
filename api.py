import replicate

def get_image(args:str):
    model = replicate.models.get('borisdayma/dalle-mini')
    output = model.predict(prompt=args, n_predictions=1)
    print(type(output)) # output type is list
    print(type(output[0])) #each index of list is a dictionary
    print(output[0]) # each dictionary contains {'image': url} pairs.
    return output
get_image('a cat sitting on a cloud')