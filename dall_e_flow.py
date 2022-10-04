from docarray import Document

server_url = 'grpcs://dalle-flow.dev.jina.ai'
def get_image(args:str):
    doc = Document(text=args).post(server_url, parameters={'num_images': 2})
    return doc
doc = get_image('blue sharks snack on giant hot dogs')
da = doc.matches()

    