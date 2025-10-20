from telethon import TelegramClient
from telethon.events.common import EventBuilder
from telethon.client.updates import Callback

class TemporaryEvent:
    def __init__(self, client: TelegramClient) -> None:
        self.client = client
    
    def create(self, callback: Callback, event: EventBuilder):

        if getattr(self, "callback", None) is not None:
            raise RuntimeError("Event already active. Remove before recreating.")

        self.callback = callback
        self.client.add_event_handler(callback=self.callback, event=event)
    
    def remove(self):
        if not (self.callback is None):
            self.client.remove_event_handler(callback=self.callback)
            self.callback = None