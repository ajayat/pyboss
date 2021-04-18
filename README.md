# PyBoss - A Discord bot
**Creator**: Adrien Jayat

[![DeepSource][Issues]][Badge-Issues]

## Setup & Install :
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
python3.9 -m pip install pipenv
```
Run the script `bot/__main__.py` or `python3.9 -m bot`

- ### Using Docker
```sh
docker-compose up --build
```

[Issues]: https://deepsource.io/gh/Adridri24/PyBoss.svg/?label=active+issues&show_trend=true
[Badge-Issues]: https://deepsource.io/gh/Adridri24/PyBoss/?ref=repository-badge