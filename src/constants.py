from dotenv import load_dotenv
from os import getenv
load_dotenv()

API_ID = int(getenv("API_ID", 0))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
DEVS = [1314824862, 8135644624]