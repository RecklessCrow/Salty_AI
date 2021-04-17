# Salty_AI

This is a project in which I use a neural network to guess the outcomes of SaltyBet matches.

Later on, it will be converted into a RL algorithm to determine betting behaviour.

## Getting started
1) You need to get some character and match data. How you get that is up to you, my .csv's are too big for git. 
You will also need to edit `database_handler.py` to format correctly to your data.
2) Run `database_handler.py` to construct the database. 
3) Run `train_model.py` to make a new model.
4) Create a file simply called ".env". This will be where you put your salty bet account information.
5) You also need a web driver for chrome, if you want to use another browser change the driver 
information in `web_scraper.py`

Place this into your .env:
>\# .env\
>email={your_email}\
>password={your_password}

After making the .env and getting the driver you can run `main.py`. This will start a browser window and the bot will automatically 
begin betting for you. Currently a premium account (one with salty gold) is required to scrape live information. Later 
I will make a version wich pulls info from the local database and updates it as the model observes matches. This however
will prevent it from betting in exhibitions where 2 characters are present in a team. Teams do not display character names
on the site.

