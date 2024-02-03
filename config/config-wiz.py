import os
from tkinter import *
from tkinter import ttk
from pathlib import Path
from configparser import ConfigParser

CONFIG_FILE = "bot.config"

def read(config_filename) -> dict[str, dict[str, str]] | None:
    """Reads an 'ini' config file, specifically ParkBot's config file, into a Python dictionary."""
    # see if any of all config values already contain a value
    # if so, keep those existing values unless a user submits something besides a blank
    here = Path(os.getcwd())

    result = {}
    config = ConfigParser()
    config_path = Path(os.getcwd())  / config_filename
    success_files = config.read(config_path)
    if len(success_files) == 0:
        return None

    result["REQUIRED"] = dict(config.items(section="REQUIRED"))
    result["MUSIC"] = dict(config.items(section="MUSIC"))
    result["FOR-AUTOPLAY"] = dict(config.items(section="FOR-AUTOPLAY"))
    result["CANVAS"] = dict(config.items(section="CANVAS"))
    return result

class ConfigWizard:
    
    REQUIRED = {
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
        "LAVALINK_URI" : "",
        "LAVALINK_PASS" : "",
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

    def writeEmptyConfig(self) -> None:
        """This method creates a 'bot.config' file if one doesn't exist."""
        # attempt to read a config if one exists
        config_path:Path = Path(os.getcwd()) / CONFIG_FILE

        current_config = read(config_path)

        new_config = ConfigParser()
        here = Path(os.getcwd())
        new_config['REQUIRED'] = {
            "TOKEN" : "",
            "WORKING_DIRECTORY" : str(here),
            "DATA_DIRECTORY" : str(Path(here) / "data"),
            "BANK_PATH" : str(Path(here) / "data" / "bank.csv"),
            "THREADS_PATH" : str(Path(here) / "data" / "threads.csv"),
            "NAUGHTY_WORDS" : "", # provide them as comma separated and parse the csv when needed
        }
        new_config["MUSIC"] = {
            "FFMPEG_PATH" : "",
            "GOOGLE_API_KEY" : "",
            "LAVALINK_URI": "",
            "LAVALINK_PASS" : "",
        }
        new_config["FOR-AUTOPLAY"] = {
            "SPOTIFY_CLIENT_ID" : "",
            "SPOTIFY_CLIENT_SECRET" : "",
        }
        new_config["CANVAS"] = {
            "CANVAS_API_KEY": "",
            "CANVAS_BASE_URL": "",
            "CANVAS_COURSE_NUM": "",
            "DATETIME_FILE": str(here / "data" / "last_time.txt")
        }

        if current_config is not None:
            for section in new_config:
                if section in current_config:
                    for key in new_config[section]:
                        if key in current_config[section]:
                            new_config[section][key] = current_config[section][key]
                            # retain values that already exist, rather than overwriting them

        with open(config_path, "w") as configfile:
            new_config.write(configfile)
        return
    
    def readConfigValues(self) -> dict[str, dict[str, str]]:
        return read(CONFIG_FILE)
    
    def writeConfigValues(self, new_values:dict[str, Entry]):
        old_conf = self.readConfigValues()
        new_config = ConfigParser()
        # we are able to iterate through all keys of the conf here because we already wrote
        # all sections and keys to the conf during the external dependency setup.
        for section_key in old_conf:
            new_config[section_key] = {}
            for key in old_conf[section_key]:
                if old_conf[section_key][key] != "": # if theres already a value there, don't overwrite it
                    new_config[section_key][key] = old_conf[section_key][key]
                else:
                    new_config[section_key][key] = new_values[key].get()
        
        with open(CONFIG_FILE, "w") as file:
            new_config.write(file)

    def overwriteConfigValues(self, new_values:dict[str, Entry]):
        old_conf = self.readConfigValues()
        new_config = ConfigParser()
        print([new_values[key].get() for key in new_values])
        for section_key in old_conf:
            new_config[section_key] = {}
            for key in old_conf[section_key]:
                if (key in new_values) and (new_values[key].get().strip() != ""):
                    new_config[section_key][key] = new_values[key].get()
                else:
                    new_config[section_key][key] = old_conf[section_key][key]

        with open(CONFIG_FILE, "w") as file:
            new_config.write(file)


    def writeConfig(self, overwriteBool:bool, entries:dict):
        match overwriteBool:
            case True:
                write_function = self.overwriteConfigValues
                print("-"*50 + f"\nNon-empty config inputs were written to '{CONFIG_FILE}'.")
            case False:
                write_function = self.writeConfigValues
                print("-"*50 + f"\nConfig values which were empty in '{CONFIG_FILE}' have been populated with your inputs :)")
            case _:
                raise ValueError()
        write_function(entries)
        
    
    def createConfigGUI(self):
        # creating main tkinter window/toplevel
        master = Tk()
        master.geometry("350x300")

        # this will create a label widget
        l1 = Label(master, text = "Discord API Token:")
        l2 = Label(master, text = "Google API Key:")
        separator = Label(master, text = "-- Optional Fields Below --")
        l3 = Label(master, text = "Spotify Client ID:")
        l4 = Label(master, text = "Spotify Client Secret:")
        l5 = Label(master, text = "Naughty Words:")
        l6 = Label(master, text = "Canvas API Key:")
        l7 = Label(master, text = "Canvas Base URL:")
        l8 = Label(master, text = "Canvas Course Num:")
        # grid method to arrange labels in respective
        # rows and columns as specified
        l1.grid(row = 0, column = 0, sticky = W, pady = 2)
        l2.grid(row = 1, column = 0, sticky = W, pady = 2)
        separator.grid(row = 2, column = 1, sticky = W, pady = 2)
        l3.grid(row = 3, column = 0, sticky = W, pady = 2)
        l4.grid(row = 4, column = 0, sticky = W, pady = 2)
        l5.grid(row = 5, column = 0, sticky = W, pady = 2)
        l6.grid(row = 6, column = 0, sticky = W, pady = 2)
        l7.grid(row = 7, column = 0, sticky = W, pady = 2)
        l8.grid(row = 8, column = 0, sticky = W, pady = 2)

        # entry widgets, used to take entry from user
        e1 = Entry(master)
        e2 = Entry(master)
        e3 = Entry(master)
        e4 = Entry(master)
        e5 = Entry(master)
        e6 = Entry(master)
        e7 = Entry(master)
        e8 = Entry(master)

        entries = {
            "token" : e1,
            "google_api_key" : e2,
            "spotify_client_id" : e3,
            "spotify_client_secret" : e4,
            "naughty_words" : e5,
            "canvas_api_key": e6,
            "canvas_base_url": e7,
            "canvas_course_num": e8,
        }

        toOverwrite = BooleanVar(master)
        checkBox = Checkbutton(master, text="Overwrite non-null values?", variable=toOverwrite, onvalue=True, offvalue=False, height=5, width = 20)
        submit = Button(master, command = lambda: [self.writeConfig(toOverwrite.get(), entries), master.destroy()], text="Submit New Values")

        # this will arrange entry widgets
        e1.grid(row = 0, column = 1, pady = 2)
        e2.grid(row = 1, column = 1, pady = 2)
        e3.grid(row = 3, column = 1, pady = 2)
        e4.grid(row = 4, column = 1, pady = 2)
        e5.grid(row = 5, column = 1, pady = 2)
        e6.grid(row = 6, column = 1, pady = 2)
        e7.grid(row = 7, column = 1, pady = 2)
        e8.grid(row = 8, column = 1, pady = 2)
        checkBox.grid(row = 9, column = 0, pady = 2)
        submit.grid(row = 9, column = 1, pady = 2)
        mainloop()

if __name__ == "__main__":
    wiz = ConfigWizard()
    wiz.writeEmptyConfig()
    wiz.createConfigGUI()