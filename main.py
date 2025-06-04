from handlers import *
from misk import *

import sys
from log_filter import ContextFilter

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="logs.log", filemode="a",
                        format="%(asctime)s %(levelname)s %(message)s", errors='ignore')
    logging.getLogger('apscheduler.executors.default').propagate = False
    filer = ContextFilter()
    logging.getLogger('aiogram.contrib.middlewares.logging').addFilter(filer)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    scheduler.start()
    scheduler.add_job(read_messages, "interval", minutes=1)
    scheduler.add_job(change_buttons)

    executor.start_polling(dp, skip_updates=True)
