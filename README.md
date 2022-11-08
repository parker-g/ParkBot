# dall-e-discord-bot !

**Ever wanted to access Dall-E mini from your own discord server? Look no further! Using the power of replicate API hosting, anyone with a github account can use AI to generate images in discord. Side note: every request to replicate's API uses a token, of which new users have only 15 - 20. Because of that, this bot is limited to sending only 15-20 dall-E-mini generations from each github account it is associated with.**

**Creating a virtual environment**
* Open a cmd terminal in VSCode
* Make sure you're pathed into 'discord-daddies'

```cd Documents/GitHub/dall-e-discord-bot```
* create a virtual environment using python venv library - the first 'venv' is telling windows that's the module we want to call, while the '.venv' is the what we are naming our virtual environment

```python3 -m venv .venv```
* activate virtual environment (it may do this automatically. you will know it's activated because your command prompt will have the name of your virtual environment, .venv, in the beginning of every line now)

```.venv\Scripts\activate.bat```
* your virtual environment is ready to work with :) now to install the dependencies required to run the bot. we'll use a command to install all dependencies listed in 'requirements.txt'  

```pip install -r requirements.txt```  
Now, if you check .venv/Lib/site-packages, you should see a bunch of libraries which we just installed - including discord and discord.py.


* use help command to view commands
