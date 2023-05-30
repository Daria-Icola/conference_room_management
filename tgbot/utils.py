from typing import Optional
import pytz
import datetime
import logging

time_zone = pytz.timezone('Europe/Moscow')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')


def local_datetime() -> Optional[datetime.datetime]:
    local_date = datetime.datetime.now(time_zone)
    logger.debug(local_date)
    return local_date
