from handlers.commands import Command
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
import asyncio
from handlers.temp_event import TemporaryEvent
from utils import DownloadManager
from constants import DEVS

@Command(name="save", allowed=DEVS)
async def save(event: Message, client: TelegramClient):
    resp = await event.respond("📂 Send me a file:")

    temporary_handler = TemporaryEvent(client=client)
    done = asyncio.Event()


    async def save_task(temp_event):

        if done.is_set(): return
        done.set()
        temporary_handler.remove()


        if temp_event.file and temp_event.document:

            name = temp_event.file.name
            msg= await temp_event.reply(f"🌐 Downloading ... `{name}`")

            async def progress(numerator, denominator):
                if (numerator>=denominator):
                    try: await msg.edit(f"✅ Downloaded successfully!\n📁 `{name}`")
                    except: pass
                else:
                    try: await msg.edit(f"🌐 Downloading ({int(numerator/denominator*100)}%)")  # type: ignore
                    except: pass

            manager = DownloadManager(message=temp_event, client=client, progress_callback=progress)
            await manager.download_file("downloads")

        else:
            await temp_event.reply("❌ Message contains no file or document. If you think this is a mistake, please mention it on our support channel.")


    temporary_handler.create(callback=save_task, event=events.NewMessage(chats=event.chat, from_users=[event.sender_id]))
    try: await asyncio.wait_for(done.wait(), timeout=60)
    except:
        temporary_handler.remove()
        await resp.edit("⌛ Timeout!\n📁 No file received! Re-run the /save command again.") # type: ignore
        

