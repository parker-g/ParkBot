import requests

# im realizing i create two bytes objects here - i instantiate one in creation of img variable,
# and then try to save that object to another bytes object. so definitely could be an issue there. 

def img_test0():
    image_url = 'https://res.cloudinary.com/sagacity/image/upload/c_crop,h_480,w_1084,x_0,y_0/c_limit,dpr_auto,f_auto,fl_lossy,q_80,w_1080/Pixabay_1_swmxbf.jpg'
    response = requests.get(image_url) # collect image data from url
    destination_url = 'images/image.png'
    with open(destination_url, 'wb') as file:
        file.write(response.content)
    return destination_url





    # this function returns all the bytes in an image. long asf. discord
    # File() object requires a BytesBase object (such as BytesIO), so I dont need to 
    # send the pure bytes to discord. 
