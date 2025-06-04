import logging
import re


class ContextFilter(logging.Filter):
    def filter(self, record):
        if record.name == 'aiogram.contrib.middlewares.logging':
            if record.msg.__contains__('Process update'):
                return False
            if record.msg.__contains__('Unhandled callback query'):
                return False
            if record.msg.__contains__('Received callback query'):
                nums = re.findall(r'\d+', record.msg)
                user_id = [int(i) for i in nums][1]
                callback = re.findall('with data: (.*) originally posted', record.msg)[0]
                record.msg = f"User: {user_id}; Callback: {callback} "
        return True
