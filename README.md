# discord-daddies
project


**Creating a virtual environment**
* Open a cmd terminal in VSCode
* Make sure you're pathed into 'discord-daddies'
```cd Documents/GitHub/discord-daddies```
* create a virtual environment using python venv library - the first 'venv' is telling windows that's the module we want to call, while the '.venv' is the what we are naming our virtual environment
```python3 -m venv .venv```
* activate virtual environment (it may do this automatically. you will know it's activated because your command prompt will have the name of your virtual environment, .venv, in the beginning of every line now)
```.venv\Scripts\activate.bat```
* your virtual environment is ready to work with :) now to install the dependencies required to run the bot. we'll use a command to install all dependencies listed in 'requirements.txt'
```python3 -m pip install -r requirements.txt```
