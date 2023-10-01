# DEPRECATED --------------------

# save a filled out version of this file as config.py, in this directory.

# this config file uses windows-style back slashes in directory naming - you may need to change all '\\' to '/' to run on a linux machine


# pound sign legend: 

# == this variable is necessary for the discord Bot to run
## == this variable is necessary for the Music feature 
### == this variable is necessary for the Canvas feature
#### == this variable is optional

TOKEN = '' # this is your Discord API token, the soul of your Discord Bot

WORKING_DIRECTORY = "" # this should be the path to your local instance of the ParkBot repository, ie "C:/Users/Parker/Documents/GitHub-Repos/ParkBot/"

GOOGLE_API_KEY = '' ## a google API key is necessary to host the Music feature, since searching for songs on youtube (within google's TOS) requires a key.

SPOTIFY_CLIENT_ID = "" #### Client ID provided by spotify, used to access the Spotify API. use this for access to the music 'autoplay' feature.

SPOTIFY_CLIENT_SECRET = "" #### The api-key corresponding to your spotify client ID. Make sure to provide this value in conjunction with your client ID to allow the music 'autoplay' feature to work.

FFMPEG_PATH = "C:/Program Files/FFmpeg/bin/ffmpeg.exe" ## (the current value of FFMPEG_PATH is an example) this is the path to your FFMPEG executable. this exe will be used to process audio (music) before it can be played.

CANVAS_API_KEY = "" ### if you want to set up the canvas feature, you will store your canvas API key here

CANVAS_BASE_URL = "https://learn.vccs.edu" ###  current value is an example. the base URL of the canvas instance you would like to access using the canvas API. URLs can vary widely due to the way canvas is distributed

CANVAS_COURSE_NUM = 517689 ### current value is an example. an integer that indicates which of your courses you would like to poll for new assignments

###################################### the variable below is optional to change. leave it blank if you want ###############################################

NAUGHTY_WORDS = [] #### a list of strings (make the words you put in here lowercase) which the text to speech feature will not be allowed to say

########################################### the below variables do not need to change, don't change them ######################################################

DATETIME_FILE = WORKING_DIRECTORY + "data\\last_time.txt" # this file stores the date and time every time you request data from canvas, to display it to users whenever they use the canvas command

BANK_PATH = WORKING_DIRECTORY + "data\\bank.csv" # csv file where users' GleepCoin balances are stored + modified

THREADS_PATH:str = WORKING_DIRECTORY + "data\\threads.csv" # csv file where users and their private threads are stored (for use in poker game, to privately send a user their hand)

DATA_DIRECTORY = WORKING_DIRECTORY + "data\\" # no need to change this, this represents the path where any data created by the bot will be stored, ie: songs (temporarily), the 'bank' (a text file where member's money amounts are stored), etc.
