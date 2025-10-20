from handlers.commands import Command
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from utils import download_file
import asyncio
from handlers.temp_event import TemporaryEvent

@Command(name="save")
async def save(event: Message, client: TelegramClient):
    resp = await event.respond("📂 Send me a file:")

    temporary_handler = TemporaryEvent(client=client)
    done = asyncio.Event()


    async def save_task(temp_event):

        if done.is_set(): return
        done.set()
        temporary_handler.remove()


        if temp_event.file and temp_event.document:
            msg= await temp_event.reply("🌐 Downloading ...")
            async def progress(numerator, denominator):
                try: await msg.edit(f"🌐 Downloading ({int(numerator/denominator*100)}%)")  # type: ignore
                except: pass

            name = temp_event.file.name or "unnamed.tmp"
            async def completed():
                completed_msg = f"✅ Downloaded successfully!\n📁 `{name}`"
                try: await msg.edit(completed_msg)  # type: ignore
                except:
                    # This will be used when, by any chance Telegram rate-limits us.
                    await asyncio.sleep(5)
                    await msg.edit(completed_msg)  # type: ignore

            await download_file(client=client, message=temp_event, output_file=name, dest_folder="downloads",progress_callback=progress, completed_callback=completed)

        else:
            await temp_event.reply("❌ Message contains no file or document. If you think this is a mistake, please mention it on our support channel.")


    temporary_handler.create(callback=save_task, event=events.NewMessage(chats=event.chat, from_users=[event.sender_id]))
    try: await asyncio.wait_for(done.wait(), timeout=60)
    except:
        temporary_handler.remove()
        await resp.edit("⌛ Timeout!\n📁 No file received! Re-run the /save command again.") # type: ignore
        

