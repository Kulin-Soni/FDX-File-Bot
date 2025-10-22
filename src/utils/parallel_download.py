# Special thanks to https://github.com/mautrix/telegram/blob/master/mautrix_telegram/util/parallel_file_transfer.py
#
import asyncio, aiofiles
from pathvalidate import sanitize_filename
from pathlib import Path
from telethon import TelegramClient
from telethon.network import MTProtoSender
from telethon.tl.custom.message import Message
from telethon.tl.types import InputDocumentFileLocation
from telethon.tl.functions.upload import GetFileRequest
from telethon.utils import get_appropriated_part_size, get_input_location
from telethon.tl.functions.auth import (
    ExportAuthorizationRequest,
    ImportAuthorizationRequest,
)
from telethon.tl.functions import InvokeWithLayerRequest
from telethon.tl.alltlobjects import LAYER
from os import replace
from .crypto_str import crypt
from math import ceil
from typing import Callable, Any, Awaitable

class ConnectionManager:
    def __init__(self, client: TelegramClient, message: Message) -> None:
        self.client = client
        self.dc_id, _ = get_input_location(message.document)
        self.senders: list[MTProtoSender] = []

    async def init(self):
        self.auth_key = self.client.session.auth_key if self.client.session.dc_id == self.dc_id else None  # type: ignore
        self.dc = await self.client._get_dc(self.dc_id)


    async def _create_connection(self) -> MTProtoSender:
        sender = MTProtoSender(auth_key=self.auth_key, loggers=self.client._log)
        dc = self.dc
        client = self.client
        await sender.connect(
            client._connection(
                ip=dc.ip_address,
                port=dc.port,
                dc_id=dc.id,
                loggers=client._log,
                proxy=client._proxy,
            )
        )
        if not self.auth_key:
            auth = await client(ExportAuthorizationRequest(self.dc_id))
            self.client._init_request.query = ImportAuthorizationRequest(id=auth.id, bytes=auth.bytes) # type: ignore
            await sender.send(InvokeWithLayerRequest(LAYER, client._init_request))  # type: ignore
            self.auth_key = sender.auth_key
        self.senders.append(sender)
        return sender

    async def create_connections(self, connections: int) -> None:
        if not getattr(self, "dc", None): await self.init()
        await self._create_connection() # The first cross-DC sender will export+import the authorization.
        await asyncio.gather(
            *(self._create_connection() for _ in range(connections - 1))
        )

    async def disconnect_connections(self) -> None:
        if len(self.senders)==0: return
        [await sender.disconnect() for sender in self.senders]


class DownloadManager:
    def __init__(self, message: Message, client: TelegramClient, progress_callback: Callable[[int, int], Awaitable[Any]] | None = None) -> None:

        if not (message.document and message.file):
            raise RuntimeError("No file in the message. Please check before creating an instance.")

        self.client = client
        self.message = message
        self.connection_manager = ConnectionManager(client=client, message=message)
        self.file = message.file
        doc = message.document
        self.size = doc.size
        self.name = sanitize_filename(str(self.file.name) if self.file else "unnamed_File")
        self.loc = InputDocumentFileLocation(
            id=doc.id,
            access_hash=doc.access_hash,
            file_reference=doc.file_reference,
            thumb_size="",
        )
        self.chunk_size = get_appropriated_part_size(self.size)*1024
        self.parts = ceil(self.size / self.chunk_size)
        self.progress_callback = progress_callback 
        self.progress = 0

    async def _download_chunk(
        self,
        sender: MTProtoSender,
        loc: InputDocumentFileLocation,
        offset: int,
        limit: int,
    ) -> bytes:
        result = await sender.send(request=GetFileRequest(location=loc, offset=offset, limit=limit)) # type: ignore
        return result.bytes

    async def _write_to_file(
        self,
        file: Path,
        offset: int,
        data: bytes
    ):
        async with aiofiles.open(file.resolve(), "r+b") as f:
            await f.seek(offset)
            await f.write(data)
            await f.flush()

    def _resolve_temp_file(self, temp_file: Path):
        perm_file = Path(temp_file.parent / self.name).resolve()
        try: replace(temp_file, perm_file)
        except: pass

    async def _progress_callback(self):
        callback = self.progress_callback
        if callback is None: return
        while self.progress < self.size-(self.chunk_size+1):
            await callback(self.progress, self.size)
            await asyncio.sleep(5)

        await callback(self.size, self.size)
    def _get_connection_count(
        self, file_size: int, full_size: int = 100 * 1024 * 1024
    ) -> int:
        max_connections = 15
        if file_size > full_size:
            return max_connections
        return ceil((file_size / full_size) * max_connections)

    async def download_file(self, destination_folder: str):
        temp_file = Path(destination_folder, f"{Path(self.name).stem}_{crypt(15)}.bin").resolve()
        print("\n📁 FILE:", self.name, f"({self.size/(1024*1024):.2f}MB)")
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.touch(exist_ok=True)

        total_connections = self._get_connection_count(self.size)
        print("📡 TOTAL CONNECTIONS:", total_connections)
        await self.connection_manager.create_connections(total_connections)

        sem = asyncio.Semaphore(total_connections)
        failed_chunks: list[int] = []
        async def download_and_write(offset: int, multiplier: int = 0):
            async with sem:
                try:
                    self.progress = self.progress if offset<self.progress else offset
                    data = await self._download_chunk(
                        sender=self.connection_manager.senders[multiplier % total_connections],
                        loc=self.loc,
                        offset=offset,
                        limit=self.chunk_size,
                    )
                    await self._write_to_file(file=temp_file, offset=offset, data=data)
                    print(f"📝 CHUNK {multiplier+1}/{self.parts} WRITTEN!")
                except: failed_chunks.append(offset)

        await asyncio.gather(*(*(download_and_write(offset=i*self.chunk_size, multiplier=i) for i in range(self.parts)), self._progress_callback()))
        
        if len(failed_chunks)>0:
            for index, item in enumerate(failed_chunks):
                await download_and_write(offset=item, multiplier=index)

        await self.connection_manager.disconnect_connections()
        self._resolve_temp_file(temp_file)

        print("✅ COMPLETED!")