from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from apscheduler.schedulers.asyncio import AsyncIOScheduler

DB_HOST = "localhost"
DB_NAME = "vks_main"
DB_USER = "postgres"
DB_PASS = "postgres"

telegram_token = ""
is_testing = True
dest_email = ""
from_email = ""
from_email_password = ""

subject = "Согласование документов"

bot = Bot(token=telegram_token)
dp = Dispatcher(bot, storage=MemoryStorage())
scheduler = AsyncIOScheduler()

last_message = {}
