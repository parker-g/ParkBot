from config.config import DATA_DIRECTORY, FFMPEG_PATH
import yt_dlp

def slugify(string):
    new_string = ""
    no_nos = [
        "\\",
        "/",
        "\'",
        "\"",
        "|",
        ":",
        "*",
    ]
    for letter in string:
        if letter not in no_nos:
            new_string += letter
    return new_string

def getSong(youtube_id:str, song_name:str) -> None:
        """Downloads the youtube video corresponding to the ID passed as an argument, to the DATA_DIRECTORY as an .mp3."""
        base_address = "https://www.youtube.com/watch?v="
        ytdl_format_options = {
            "no_playlist": True,
            # "max_downloads": 1,
            'format': 'mp3/bestaudio/best',
            "outtmpl": DATA_DIRECTORY + slugify(song_name) + ".%(ext)s",  
            "ffmpeg_location": FFMPEG_PATH,
                # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
        }

        youtube_url = [base_address + youtube_id]
        
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            ydl.download(youtube_url)
        return