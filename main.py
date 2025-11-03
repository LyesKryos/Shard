import asyncio
import sys
import json
import atexit
import logging
import logging.handlers as handlers
from ShardBot import Shard
import time


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

async def watchdog_task(bot, interval=60):
    """
    A background watchdog that checks if the bot is still alive and responsive.
    Logs any disconnections or slowdowns.
    """
    last_heartbeat = time.monotonic()

    # Monkey-patch the bot's internal heartbeat event (for more precise tracking)
    async def heartbeat_listener(latency):
        nonlocal last_heartbeat
        last_heartbeat = time.monotonic()

    bot.add_listener(heartbeat_listener, "on_socket_response")

    while True:
        await asyncio.sleep(interval)
        now = time.monotonic()

        # Log if bot has gone silent for too long
        silence = now - last_heartbeat
        if bot.is_closed():
            logger.critical(f"Watchdog: Bot appears disconnected (is_closed=True). Last heartbeat {silence:.0f}s ago.")
        elif not bot.is_ready():
            logger.warning(f"Watchdog: Bot not ready. Last heartbeat {silence:.0f}s ago.")
        elif silence > interval * 3:
            logger.error(f"Watchdog: No Discord heartbeat in {silence:.0f}s — possible freeze or lost connection.")
        else:
            continue

# --- MAIN BOT EXECUTION ---

def main(bot: Shard):
    try:
        with open("config.json") as f:
            token_raw = json.load(f)
        token = token_raw["token"]
        loop = asyncio.get_event_loop()
        watchdog_main_task = loop.create_task(watchdog_task(bot))
        watchdog_main_task.add_done_callback(lambda t: logger.exception("Watchdog task ended unexpectedly", exc_info=t.exception()))
    
    except Exception:
        logger.exception("Failed to load token from config.json.")
        sys.exit(1)

    try:
        bot.run(token, log_handler=handler)
    except Exception:
        logger.exception("Exception occurred during bot.run().")


if __name__ == "__main__":
    main(Shard())
