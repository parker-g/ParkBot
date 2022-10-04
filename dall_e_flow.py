from docarray import Document

server_url = 'grpcs://dalle-flow.dev.jina.ai'
def get_image(args:str):
    doc = Document(text=args).post(server_url, parameters={'num_images': 2})
    da = doc.matches
    return da
# da.plot_image_sprites(fig_size=(10,10), show_index=True)
results = get_image('swirly clouds with a red sky')
# results.plot_image_sprites(show_index=True)
print(results[0])
    