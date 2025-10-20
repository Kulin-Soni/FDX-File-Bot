from handlers.commands import Command
from telethon import TelegramClient
from telethon.tl.custom.message import Message

@Command(name="start")
async def download(event: Message, client: TelegramClient):
    await event.respond("Hey, am alive.") 
    