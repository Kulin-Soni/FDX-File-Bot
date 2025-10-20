from telethon import TelegramClient
from constants import API_ID, API_HASH, BOT_TOKEN
client = TelegramClient("fdx", api_id=API_ID, api_hash=API_HASH).start(bot_token=BOT_TOKEN)