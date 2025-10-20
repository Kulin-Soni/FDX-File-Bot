from bot import client
from pathlib import Path
from handlers.commands import loadCommands
import logging
logging.basicConfig(format='[%(levelname) %(asctime)s] %(name)s: %(message)s', level=logging.WARNING)
async def main():
    loadCommands(Path(__file__).parent) # Loads commands (or say plugins)
    if bot:= await client.get_me():
        name = bot.first_name if bot.first_name else "BOT" if bot.bot else "USER" # type: ignore
        print(f"🤖 LOGGED IN AS {name}!")
    

if __name__ == "__main__":
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
