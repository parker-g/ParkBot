from tkinter import ttk
import tkinter as tk
from configparser import ConfigParser
import sys

# provide a GUI for users to enter the required information needed to setup the bot's configuration

# config['DEFAULT'] = {
#             "TOKEN" : "",
#             "WORKING_DIRECTORY" : str(here),
#             "DATA_DIRECTORY" : str(Path(here) / "data"),
#             "BANK_PATH" : str(Path(here) / "data" / "bank.csv"),
#             "THREADS_PATH" : str(Path(here) / "data" / "threads.csv"),
#             "NAUGHTY_WORDS" : "", # provide them as comma separated and parse the csv when needed
#         }
#         config["MUSIC"] = {
#             "FFMPEG_PATH" : str(ffmpeg_path),
#             "GOOGLE_API_KEY" : "",
#         }
#         config["FOR-AUTOPLAY"] = {
#             "SPOTIFY_CLIENT_ID" : "",
#             "SPOTIFY_CLIENT_SECRET" : "",
#         }
#         config["CANVAS"] = {
#             "CANVAS_API_KEY": "",
#             "CANVAS_BASE_URL": "",
#             "CANVAS_COURSE_NUM": "",
#             "DATETIME_FILE": str(Path(os.getcwd())  / "data" / "last_time.txt")
#         }

class ConfigWizard:
    
    DEFAULT = {
        "TOKEN" : "",
        "WORKING_DIRECTORY" : "",
        "DATA_DIRECTORY" : "",
        "BANK_PATH" : "",
        "THREADS_PATH" : "",
        "NAUGHTY_WORDS" : "", # provide them as comma separated and parse the csv when needed
    }

    MUSIC_FIELDS = {
        "FFMPEG_PATH" : "",
        "GOOGLE_API_KEY" : "",
    }

    AUTOPLAY_FIELDS = {
        "SPOTIFY_CLIENT_ID" : "",
        "SPOTIFY_CLIENT_SECRET" : "",
    }

    CANVAS_FIELDS = {
        "CANVAS_API_KEY": "",
        "CANVAS_BASE_URL": "",
        "CANVAS_COURSE_NUM": "",
        "DATETIME_FILE": "",
    }   
        
    def __init__(self):
        pass

    def createConfigGUI(self):
        root = tk.Tk()
        self.frame = ttk.Frame(root, padding=10)
        self.frame.grid()
        ttk.Label(self.frame, text="Discord API Token", name="disc-token").grid(row=0, column=0)
        ttk.Entry(self.frame, name="disc-token", width=100).grid(row=1, column=5, columnspan=30)
        root.mainloop()
        # root = tk.Tk()
        # frm = frame
        # frm = ttk.Frame(root, padding=10)
        # frm.grid()
        # ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
        # ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
        # root.mainloop()

if __name__ == "__main__":
    wiz = ConfigWizard()
    wiz.createConfigGUI()