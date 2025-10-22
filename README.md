# FDX FIle Bot
A simple bot to download files from Telegram to host at very fast speed.

## Setup (with Docker)

### Requirements
- [Docker](https://www.docker.com/)


### Steps
1. Setup environment variables following [Environment Variables](#environment-variables) guide.

3. Run a docker container:
    ```
    docker compose up
    ```


## Manual Setup

### Requirements
- [Python 3.7+](https://python.org/downloads)

### Steps

1. Copy the files and folder manually or using [Git](https://git-scm.com/), and open it.

2. Setup environment variables following [Environment Variables](#environment-variables) guide.

3. Install all the dependencies:
    ```
    pip install -r src/requirements.txt
    ```

5. Run the script:
    ```
    python src/main.py
    ```

## Environment Variables
Create `.env` file and update all the variables as:
- **API_ID**: Get it from [here](https://my.telegram.org).
- **API_HASH**: Get it from [here](https://my.telegram.org).
- **BOT_TOKEN**: You can get it from [BotFather](https://t.me/BotFather)


_**(Optional)**_ You can modify developers list in `src/constants.py` to make (some) commands limited to your use.

```
API_ID=12345678
API_HASH=abcdefghijklmnopqrstuvwxyz
BOT_TOKEN=12345678:abcdefghijklmnopqrstuvwxyz
```