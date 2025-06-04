from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


async def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Добавить документ"))
    return keyboard


async def company_keyboard(companies):
    keyboard = InlineKeyboardMarkup()
    for company in companies:
        keyboard.add(InlineKeyboardButton(text=company["name"], callback_data=f"set_company_{company['company_id']}"))
    keyboard.add(InlineKeyboardButton(text="Отменить отправку", callback_data="cancel"))
    return keyboard


async def facility_keyboard(facilities):
    keyboard = InlineKeyboardMarkup()
    for facility in facilities:
        keyboard.add(InlineKeyboardButton(text=facility["name"], callback_data=f"set_facility_{facility['name']}"))
    keyboard.add(InlineKeyboardButton(text="Без объекта", callback_data="set_facility_no_facility"))
    keyboard.add(InlineKeyboardButton(text="Отменить отправку", callback_data="cancel"))
    return keyboard


async def people_keyboard(confirms):
    keyboard = InlineKeyboardMarkup()
    for priority in confirms:
        if confirms[priority]["choose"]:
            keyboard.add(InlineKeyboardButton(text="✅ " + confirms[priority]["name"], callback_data=f"set_person_{confirms[priority]['tg_id']}"))
        else:
            keyboard.add(InlineKeyboardButton(text="❌ " + confirms[priority]["name"], callback_data=f"set_person_{confirms[priority]['tg_id']}"))
    keyboard.add(InlineKeyboardButton(text="Продолжить", callback_data="set_person_continue"))
    keyboard.add(InlineKeyboardButton(text="Отменить отправку", callback_data="cancel"))
    return keyboard


async def send_without_text_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Отправить без комментария", callback_data="send_without_text"))
    keyboard.add(InlineKeyboardButton(text="Отменить отправку", callback_data="cancel"))
    return keyboard


async def confirm_keyboard(doc_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="✅", callback_data=f"yes_{doc_id}"))
    keyboard.add(InlineKeyboardButton(text="❌", callback_data=f"no_{doc_id}"))
    keyboard.add(InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment_{doc_id}"))
    keyboard.add(InlineKeyboardButton(text="Прикрепить новый документ", callback_data=f"add_new_doc_{doc_id}"))
    return keyboard


async def confirm_creator_keyboard(doc_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Пропустить", callback_data=f"skip_{doc_id}"))
    keyboard.add(InlineKeyboardButton(text="Добавить комментарий", callback_data=f"add_comment_{doc_id}"))
    return keyboard


async def cancel_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return keyboard
