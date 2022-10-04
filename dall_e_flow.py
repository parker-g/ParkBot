from docarray import Document
from jina import Client

import asyncio
server_url = 'grpcs://dalle-flow.dev.jina.ai'

def test(args:str, server):
    client = Client(host = server, asyncio=True)
    doc = Document(text=args)
    response = client.post('/', doc, request_size=1, parameters={'num_images': 2})
    # doc = Document(text=args).post(server_url, parameters={'num_images': 2})
    return response

# # async def run_client(port):
#     client = Client(port=port, asyncio=True)
#     async for resp in client.post('/', async_inputs, request_size=1):
#         print(resp)

async def test2(args:str):
    i = 0
    client = Client(host=server_url, asyncio=True)
    while i <= 2:
        response = client.post(
            '/', 
            Document(text=args),
            request_size=1,
            parameters={'num_images': 2}
            )
        async for res in response:
            print(res)
        i += 1
    await asyncio.sleep(0.5)
        


# this was returning exactly what i needed it to - images in bytes. when i printed the matches, i got a bazillion
# bytes printed in my terminal. problem is that I need to structure this function in an asynchronous way since it 
# is part of an event loop. jina detects the event loop in bot.py and raises an error bc of it - then suggests using
# jina's Client or Flow objects with asyncio = True. so yeah gotta figure out how to do that tomorrow, seems like 
# jina docs actually have some rly good examples. shouldn't be too excruciatingly bad.

def get_image(args:str):
    doc = Document(text=args).post(server_url, parameters={'num_images': 2})
    da = doc.matches
    return da

# da.plot_image_sprites(fig_size=(10,10), show_index=True)
# results.plot_image_sprites(show_index=True)



