import asyncio
import sys
import json
import atexit
import logging
import logging.handlers as handlers
from ShardBot import Shard


# --- GLOBAL LOGGER SETUP ---
handler = handlers.RotatingFileHandler(
    "botlogs.log", encoding="utf-8", mode='a', maxBytes=50000, backupCount=3
)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
handler.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler, stream],
    force=True
)
logger = logging.getLogger("bot")
logger.debug("Global logging initialized successfully.")


# --- FAILSAFE HOOKS ---

def on_shutdown():
    logger.critical("Bot process exiting unexpectedly (atexit triggered).")

atexit.register(on_shutdown)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception


def handle_async_exception(loop, context):
    msg = context.get("exception") or context.get("message", "No message provided")
    logger.critical(f"Unhandled asyncio exception: {msg}", exc_info=context.get("exception"))

asyncio.get_event_loop().set_exception_handler(handle_async_exception)


# --- MAIN BOT EXECUTION ---

def main(bot: Shard):
    try:
        token_raw = json.load(open("config.json"))
        token = token_raw["token"]
    except Exception:
        logger.exception("Failed to load token from config.json.")
        sys.exit(1)

    try:
        bot.run(token, log_handler=handler)
    except Exception:
        logger.exception("Exception occurred during bot.run().")


if __name__ == "__main__":
    main(Shard())
