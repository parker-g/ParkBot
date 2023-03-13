import requests
import get_assignments
# created this file to test requesting an image from url, opening it,
# saving it, and returning image url

# def img_test0():
#     image_url = ''
#     response = requests.get(image_url) # collect image data from url
#     destination_url = 'images/image.png'
#     with open(destination_url, 'wb') as file:
#         file.write(response.content)
#     return destination_url

# url = img_test0()

differences, time_diff = get_assignments.get_differences("data/last_time.txt")
print(differences, time_diff)