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

# save log files
logger.add(
    Path.home() / ".qcore/logs/session.log",
    format=log_record_format,
    rotation="24 hours",  # current log file closed and new one started every 24 hours
    retention="1 week",  # log files created more than a week ago will be removed
    level="DEBUG",
    backtrace=True,
    diagnose=True,
)

# send logged messages to users
logger.add(
    sys.stdout, format=log_record_format, level="INFO", backtrace=False, diagnose=False
)

logger.info("Logger activated!")
