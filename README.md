# dall-e-discord-bot !

**Ever wanted to access Dall-E mini from your own discord server? Look no further! Using the power of replicate API hosting, anyone with a github account can use AI to generate images in discord. Side note: every request to replicate's API uses a token, of which new users have only 15 - 20. Because of that, this bot is limited to sending only 15-20 dall-E-mini generations from each github account it is associated with. NOW, there are benefits of using an API as well. You don't have to use your own local processing power to generate these images, plus replicate is free until you run out of tokens ( as long as you don't enter your card info! ) You will not be able to complete any requests after you are out of tokens. It's not like AWS where you might accidentally get $2 million charged for overdrawing on API tokens. So why not give it a try :D**

**Let's begin with creating a virtual environment**
* Open a cmd terminal in VSCode
* Make sure you're pathed into 'dall-e-discord-bot'

```cd Documents/GitHub/dall-e-discord-bot```

* create a virtual environment using python venv library - the first 'venv' is telling windows that's the module we want to call, while the '.venv' is the what we are naming our virtual environment

```python3 -m venv .venv```
* activate virtual environment (it may do this automatically. you will know it's activated because your command prompt will have the name of your virtual environment, .venv, in the beginning of every line now)

```.venv\Scripts\activate.bat```

* your virtual environment is ready to work with :) now to install the dependencies required to run the bot. we'll use a command to install all dependencies listed in 'requirements.txt'  

```python3 -m pip install -r requirements.txt```  

Now, if you check .venv/Lib/site-packages, you should see a bunch of libraries which we just installed - including discord and discord.py. If you don't, you probably installed your requirements to your global python environment rather than the virtual environment you just created. This isn't an issue now, but if you want to run other python projects in the future, you will want to look into cleaning up your global python environment. 

**Getting your replicate API token**
* Begin by going to [replicate's website](https://www.replicate.com)

* Sign up using your github account

* Navigate to the top right hand corner where your profile picture is located, and select "account" in the dropdown. 

* Here, you should see 'API TOKEN' blaring at you. generate one if this section is blank.

* Now, go to [this link](https://replicate.com/docs/get-started/python) in the replicate documentation. There should be a subheader `authenticate`, in which there is a command beginning with `export`. Copy this command (it contains your unique API key, and assigns it to an environment variable) and run it in your command prompt terminal. 

* Now you're almost ready!

**If you're unfamiliar with the Discord API**

* To create your discord bot, you will have to follow a few steps on the discord API documentation. Don't forget to invite your bot to your server before trying to run the bot. 

* Most importantly, once you have created your bot, ensuring you have the message sending intention active, you want to locate and copy your discord API token. You'll want to keep this token secret.

* Now that you have your discord API token, you need to store it in a config file. Create a 'config' folder within the 'dall-e-discord-bot' folder. 

* within the config folder you just created, create a file called config.py

* in config.py, you need to write just one line - be sure to replace the string I included with the Discord API token you copied a few steps ago. 

```TOKEN = ABC123DEF456GHI789```

* Now you're just about ready to run your dall-e-mini discord bot!

* Open a command prompt terminal, and be sure to path to your dall-e-discord-bot folder

```cd Documents/GitHub/dall-e-discord-bot```

* now, run this command to boot up the bot. upon booting up, you should receive a message in your terminal telling you 'Hi, I'm logged in as (your bots name). from here, your bot is online!

```python3 bot.py```

* use the !help command to see a list of commands. remember to prefix any commands to this bot with the `!` character. now generate some AI art :D. the requests have generally taken around 30-45 seconds to load in my experience. 

* if an image takes longer than 2 minutes to load, close the terminal where your bot.py script is running. then, open a new terminal and run the last two commands again.