import asyncio
import sys
from ShardBot import Shard
import logging
import logging.handlers as handlers
import json

def main(bot: Shard):
    # read config file
    token_raw = json.load(open("config.json"))
    token = token_raw["token"]

    # setup logger
    handler = handlers.RotatingFileHandler("botlogs.log", encoding="utf-8",
                                           mode='a', maxBytes=50000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    handler.setLevel(logging.DEBUG)
    # set up the configuration if there is not already a handler running
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.DEBUG, handlers=[handler])
    # define the logger
    logger = logging.getLogger("bot")
    # ensure the logger is initialized
    logger.debug("Logging initialized successfully")

    # handle any uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        # catch the class of the rror, the value of the exception, and the traceback object
        # if it is a normal interrupt, leave alone
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        # log the error
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    # for all future uncaught exceptions, use this function
    sys.excepthook = handle_exception

    # handle any async exceptions
    # get the event loop
    loop = asyncio.get_running_loop()
    def handle_async_exception(loop, context):
        # from the context, get the exception
        msg = context.get("exception") or context.get("message", "No message provided")
        # log the error
        logger.critical(f"Unhandled asyncio exception: {msg}", exc_info=context.get("exception"))
    # for all future uncaught async exceptions, use this function
    loop.set_exception_handler(handle_async_exception)

    # catch any unhandled crashing errors during the run phase
    try:
        bot.run(token, log_handler=handler)
    except Exception:
        logger.exception("Exception occurred during run()")

main(Shard())