from datetime import datetime

import pytz

from app.core.config import settings

APP_TZ = pytz.timezone(settings.timezone)



def now_local() -> datetime:
    return datetime.now(APP_TZ)
