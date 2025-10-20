import asyncio, aiofiles
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.types import InputDocumentFileLocation
from telethon.tl.functions.upload import GetFileRequest as GetFile
from telethon.utils import get_appropriated_part_size
# from telethon.tl.functions.auth import ExportAuthorizationRequest, ImportAuthorizationRequest
# from telethon.tl.functions import InvokeWithLayerRequest
# from telethon.tl.alltlobjects import LAYER
from os import rename, listdir, makedirs
from typing import Callable, Any
from .crypto_str import crypt
from math import ceil

PARALLELS = 2
KB = 1024

async def download_file(client: TelegramClient, message: Message, output_file, dest_folder, progress_callback: Callable[[int, int], Any] | None=None, completed_callback: Callable[[], Any] | None=None):

    # Folder handling
    dest = dest_folder
    makedirs(dest, exist_ok=True)
    if output_file in listdir(dest):
        if completed_callback: await completed_callback()
        return

    # Getting necessary information of file
    doc = message.document
    if doc is None: return
    size = doc.size
    loc = InputDocumentFileLocation(
        id=doc.id,
        access_hash=doc.access_hash,
        file_reference=doc.file_reference,
        thumb_size=""
    )
    chunk_size =  get_appropriated_part_size(size)*1024  
    parts = ceil(size/chunk_size)

    # Temporary file
    temp_file = f"{dest}/{output_file}_{crypt(15)}.bin"

    # Creating and filling a null file for avoiding fragmentation.
    async with aiofiles.open(temp_file, "wb") as f:
        await f.seek(size-1)
        await f.write(b"\0")

    # Basic utilities
    sem = asyncio.Semaphore(PARALLELS)
    lock = asyncio.Lock()

    # Function to download file in parts.
    async def download_part(multiplier: int):

        offset = multiplier * chunk_size

        async with sem:

            downloaded_part = await client(GetFile(location=loc, offset=offset, limit=chunk_size))
            async with lock:
                async with aiofiles.open(temp_file, "r+b") as f:
                    await f.seek(offset)
                    await f.write(downloaded_part.bytes) # type: ignore # cuz telethon has shitty types
                    await f.flush()
            if progress_callback: await progress_callback(multiplier+1, parts)

    await asyncio.gather(*[download_part(i) for i in range(parts)])

    # Renaming as actual file.
    rename(temp_file, f"{dest}/{output_file}")

    if completed_callback: await completed_callback()