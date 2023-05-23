<p align="center">
  <img width="500" height="500" src="images/ParkBot-logo (1).png">
</p>

# parker's perplexing, powerful discord bot !

**this discord bot has everything a college student needs for their discord server. play music in a voice channel to enhance the vibe. canvas functionality, to keep up with school. gambling feature, to safely engage in impulsive behavior. find your friends' "fursonas", for the meme. dall-e-mini image generation, because it's awesome. and be on the lookout for even more features!**

# music feature
**let's be honest guys. why does anyone really want a discord bot? this music feature is now very reliable! but it isn't banned ;D use `play` to add a song to queue, or `skip` to skip the current song. wondering what's up next? use `showQ` to see the song request queue. where does it source music from? YOU will never know unless you peer into the deep TUBE of source code provided in the music cog. disclaimer: you will have to download FFMPEG in order to use this music feature. once you download FFMPEG, you will need to save the path to ffmpeg.exe in config.py, as FFMPEG_PATH.**

# gambling breakdown
**gamble, without truly gambling! introducing gambling games, playable from the discord chat. you and all your buddies can join the player pool by using the `joinQ` command. check who's joined by using `showPlayers`. once you're in the queue, set a bet by using  `setBet <amount>`. first time players begin with 1000 GleepCoins. players remain in the player pool until they `leaveQ`, or someone clears the entire queue, `clearQ`. if you find yourself scrambling for some extra GleepCoins, don't fret. you're in luck. you can always beg for some extra gleepCoins using the `beg` command! yippee!**

**blackjack - to finally begin a game of blackjack, use the `playJack` command after players have joined and those who want to bet, have set their bets.**

**in development - texas hold em poker!!! keep your eyes peeled**

# canvas functionality breakdown
**have u ever created a discord server to keep in touch with classmates? well, ParkBot's canvas api functionality is here to bring value to you and all your classmates. Using the simple ```$getNewAssignments <days>``` command, you'll be able to see all your upcoming assignments for a class right inside your discord chat! to setup - configure a canvas api token, set up your canvas url and class ID in the config.py file. I'm open to adding more canvas-api functionality to this bot upon request!**

# text to speech functionality
**everyone gets in arguments. but not everyone can settle them like this text to speech functionality. ensure you always get the last word over your frenemies, using the `$say` command. ParkBot will join your voice channel, and repeat the words you typed. if your guild members get too rowdy with this feature, you can set a list of banned 'naughty words' in the `config/config.py` file.**

# coming soon
* texas hold'em poker - almost finished!
* thinking I could use a config json/yaml/toml file instead of using the config.py. seems more accessible to non-coders
* working on creating a bash script/ small bash function for easy bot setup and operations (to work on windows git-bash terminal, or any unix based terminal)
* open to suggestions! I need to challenge myself, dream big!!

# BIG NOTE - the instructions to set up dall-e-mini below need revision! some of the commands may not be appropriate for your operating system. also, I haven't checked the validity of the replicate links in months so those instructions mahy be deprecated as well. I will revise them sooner or later

# dall-e-mini set up below

**Ever wanted to access Dall-E mini from your own discord server? Look no further! Using the power of replicate API hosting, anyone with a github account can use AI to generate images in discord. Side note: every request to replicate's API uses a token, of which new users have only 15 - 20. Because of that, this bot is limited to sending only 15-20 dall-E-mini generations from each github account it is associated with. NOW, there are benefits of using an API as well. You don't have to use your own local processing power to generate these images, plus replicate is free until you run out of tokens ( as long as you don't enter your card info! ) You will not be able to complete any requests after you are out of tokens. It's not like AWS where you might accidentally get $2 million charged for overdrawing on API tokens. So why not give it a try :D This walkthrough assumes you are using a windows machine, and GitHub desktop installed, in the default location.**

**Let's begin with creating a virtual environment**
* Open a cmd terminal in VSCode
* Make sure you're pathed into 'ParkBot'
* 
```cd Documents/GitHub/ParkBot```

* create a virtual environment using python venv library - the first 'venv' is telling windows that's the module we want to call, while the '.venv' is what we are naming our virtual environment

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
* Don't forget to activate your virtual environment again

```.venv\Scripts\activate.bat```

* now, run this command to boot up the bot. upon booting up, you should receive a message in your terminal telling you `Hi, I'm logged in as (your bots name).` from here, your bot is online!

```python3 bot.py```

* use the $help command in discord chat to see a list of commands. remember to prefix any commands to this bot with the `$` character. now generate some AI art :D. the requests have generally taken around 30-45 seconds to load in my experience. 

* if an image takes longer than 2 minutes to load, close the terminal where your bot.py script is running. then, open a new terminal and run the last three commands again to get a fresh bot running
