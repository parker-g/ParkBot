import tkinter as tk
from tkinter import ttk
import requests
from pathlib import Path
import os


# provide a GUI for users to enter the required information needed to setup the bot's configuration

class ConfigWizard:
    
    fields = {
        0: "TOKEN",
        1: "CANVAS_API_KEY",
        2: "WORKING_DIRECTORY",
        3: "DATA_DIRECTORY",
        4: "CANVAS_BASE_URL",
        5: "CANVAS_COURSE_NUM",
        6: "DATETIME_FILE",
        7: "BANK_PATH",
        8: "THREADS_PATH",
        9: "NAUGHTY_WORDS",
        10: "SPOTIFY_CLIENT_ID",
        11: "SPOTIFY_CLIENT_SECRET",
        12: "GOOGLE_API_KEY",
        13: "FFMPEG_PATH",
    }

    def downloadFFMPEG(self):
        pass
    
    def getProjectRoot(self):
        dir = os.getcwd()
        # check if we are in the top directory of parkBot project



    def createConfigGUI(self):
        self.frame = ttk.Frame(root, padding=10)
        self.frame.grid()

    def __init__(self, project_root_directory:str):
        pass
        

root = tk.Tk()
# frm = frame
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)

root.mainloop()

