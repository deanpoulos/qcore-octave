""" """

from pathlib import Path
import sys

from loguru import logger

logger.remove()  # remove default handlers

# customise logging levels
logger.level("INFO", color="<white>")
logger.level("SUCCESS", color="<green>")
logger.level("WARNING", color="<magenta>")
logger.level("ERROR", color="<red>")

# customise log record format
log_record_format = (
    "<lvl>{level} [{time:YY-MM-DD HH:mm:ss}] [{module}-{function}] {message}</>"
)

# send logged messages to users
logger.add(
    sys.stdout, format=log_record_format, level="DEBUG", backtrace=False, diagnose=False
)

logger.info("Logger activated!")
