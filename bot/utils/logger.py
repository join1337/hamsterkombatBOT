import sys
from loguru import logger


logger.remove()
logger.add(sink=sys.stdout, format="<level>{time: HH:mm:ss}</level>"
                                   " <white>| <b>{message}</b></white>")
logger = logger.opt(colors=True)


