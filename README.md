<h1 align="center">PyBoss</h1>
<h4 align="center">A Discord bot created by Adrien Jayat </h4>

<p align="center">
    <a href="https://github.com/Adridri24/PyBoss#overview">Overview</a> •
    <a href="https://github.com/Adridri24/PyBoss#softwares">Sofwares</a> •
    <a href="https://github.com/Adridri24/PyBoss#installation">Installation</a>
</p>

![GitHub top language: Python](https://img.shields.io/github/languages/top/Adridri24/PyBoss) &nbsp;
![Python3.9](https://img.shields.io/badge/python-3.9-red) &nbsp;
[![discord.py](https://img.shields.io/badge/discord-py-orange.svg)](https://github.com/Rapptz/discord.py) &nbsp;
![GitHub repo size](https://img.shields.io/github/repo-size/Adridri24/PyBoss) &nbsp;
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE) &nbsp;
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/Adridri24/PyBoss) &nbsp;
[![DeepSource](https://deepsource.io/gh/Adridri24/PyBoss.svg/?label=active+issues)](https://deepsource.io/gh/Adridri24/PyBoss/?ref=repository-badge)


## Overview
*PyBoss* is a Discord bot that facilitates distance learning on Discord.
It allows you to manage the agenda, the planning by providing simple commands for anyone to use.

It also provides other features based on a database like a quiz, and can play music in a voice channel.

Once configured, it can automatically manage roles. The users are invited to choose their categories
with interactive reaction system.

## Softwares
**Python** <br>
It's required to have python 3.8 or more  installed on your system.
[Download Python](https://www.python.org/downloads/)

**Docker** <br>
You can also use Docker to deploy the environment in one command.
[Get started with Docker](https://www.docker.com/get-started)


## Installation
First set variables in .env file:
```ini
DISCORD_TOKEN = <discord_bot_token>
# Can be development (More logs)
ENVIRONMENT = production
# Optional, a SQLite database will be created otherwise.
DATABASE_URL = mysql+mysqlconnector://user:password@host:port/database
# For YouTube API (optional).
API_DEVELOPER_KEY = <youtube_api_developer_key>
```

- ### Using Pipenv
Install `pipenv` dependencies:
```sh
python3 -m pip install pipenv
```
Now, you can create an empty `.venv` directory and running `pipenv`
It will install packages in the virtual environment (recommended).
```sh
pipenv install
```
Run the script `pyboss/__main__.py` or run `python3 -m pyboss`

- ### Using Docker
```sh
docker-compose up --build
```

- ### Using Setup
*PyBoss* can be used as a package. It's strongly recommended using a virtual environment,
you can create one using `python3 -m venv .venv`.

Now, install the dependencies:
```sh
python3 -m pip install .
```
Now, you can run the bot from a script:
```py
from pyboss import bot

bot.run()  # or bot.run(token)
```
