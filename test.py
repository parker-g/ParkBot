import pandas as pd
import pyttsx3
import yt_dlp
# created this file to test requesting an image from url, opening it,
# saving it, and returning image url

# def img_test0():
#     image_url = ''
#     response = requests.get(image_url) # collect image data from url
#     destination_url = 'images/image.png'
#     with open(destination_url, 'wb') as file:
#         file.write(response.content)
#     return destination_url

def getSong(youtube_id):
    base_address = "https://www.youtube.com/watch?v="
    ytdl_format_options = {
        "no_playlist": True,
        "max_downloads": 1,
        'format': 'mp3/bestaudio/best',
        "outtmpl": "data/current_audio.%(ext)s",
        "ffmpeg_location": "C:/Program Files/FFmpeg/bin/ffmpeg.exe",
            # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
    }
    youtube_url = [base_address + youtube_id]
    print(youtube_url)
    with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
        ydl.download(youtube_url)
getSong("usu0XY4QNB0")
