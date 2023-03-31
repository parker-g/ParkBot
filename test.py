import pandas as pd
# created this file to test requesting an image from url, opening it,
# saving it, and returning image url

# def img_test0():
#     image_url = ''
#     response = requests.get(image_url) # collect image data from url
#     destination_url = 'images/image.png'
#     with open(destination_url, 'wb') as file:
#         file.write(response.content)
#     return destination_url


# path = "data/bank.csv"
# # url = img_test0()
# test = {
#     "BagelBrigadier": 100,
#     "Goolie": 101, 
#     "Tom": 50000,
# }
# test = pd.read_csv("data/bank.csv", header='infer')
# test.to_csv(path, index=False)
# usernames = test.Usernames


# for user in usernames:
#     print(user)