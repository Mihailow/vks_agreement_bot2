from datetime import datetime

from misk import *


@dp.message_handler(commands=["start"], state="*")
async def command_start(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_document(await state.get_data())

    text = "Здравствуйте!"
    keyboard = await main_keyboard()
    await send_message(message.from_user.id, text, keyboard)

    await state.finish()


@dp.message_handler(text="Добавить документ", state="*")
async def add_document(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_document(await state.get_data())

    confirms = {}
    admins = await get_admins()
    for user_id in admins:
        if user_id == message.from_user.id:
            await state.update_data(creator={"tg_id": user_id, "name": admins[user_id]["name"]})
        if admins[user_id]["priority"] is None:
            continue
        if user_id != message.from_user.id:
            confirms[admins[user_id]["priority"]] = {"tg_id": user_id,
                                                     "name":  admins[user_id]["name"],
                                                     "choose": True}

    text = "⬇️ Отправьте текст/картинку/документ ⬇️"
    keyboard = await cancel_keyboard()
    await send_last_message(message.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_document)
    await state.update_data(confirms=confirms)
    await state.update_data(status=None)


@dp.message_handler(state=Status.new_add_document, content_types=types.ContentType.ANY)
async def status_new_add_document(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        document_name = f"{datetime.now().strftime('%d-%m-%Y %H.%M.%S')}.png"
        await message.photo[-1].download(destination_file=document_name)
        await state.update_data(text=None)
        await state.update_data(document_name=document_name)
    elif message.content_type == "text":
        await state.update_data(text=message.text)
        await state.update_data(document_name=None)
    elif message.content_type == "document":
        document_name = message.document.file_name
        await message.document.download(destination_file=document_name)
        await state.update_data(text=None)
        await state.update_data(document_name=document_name)
    else:
        text = "Я вас не понял\n⬇️ Отправьте текст/картинку/документ ⬇️"
        keyboard = await cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return
    companies = await get_companies()

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await company_keyboard(companies)
    await send_last_message(message.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_company)


@dp.callback_query_handler(text_startswith="set_company_", state=Status.new_add_company)
async def but_set_company_(callback_query: types.CallbackQuery, state: FSMContext):
    company_id = callback_query.data.replace("set_company_", "")
    company = await get_company(company_id)
    facilities = await get_facilities(company_id)

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await facility_keyboard(facilities)
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_facility)
    await state.update_data(company_id=company_id)
    await state.update_data(company=company["name"])


@dp.message_handler(state=Status.new_add_company, content_types=types.ContentType.ANY)
async def status_new_add_company(message: types.Message, state: FSMContext):
    companies = await get_companies()

    text = "Я вас не понимаю\n⬇️ Выберите пункт меню ⬇️"
    keyboard = await company_keyboard(companies)
    await send_last_message(message.from_user.id, text, keyboard)


@dp.callback_query_handler(text_startswith="set_facility_", state=Status.new_add_facility)
async def bet_set_object_(callback_query: types.CallbackQuery, state: FSMContext):
    facility_name = callback_query.data.replace("set_facility_", "")
    confirms = (await state.get_data())["confirms"]

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await people_keyboard(confirms)
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_change_people)
    if facility_name != "no_facility":
        await state.update_data(facility=facility_name)
    else:
        await state.update_data(facility=None)


@dp.message_handler(state=Status.new_add_facility, content_types=types.ContentType.ANY)
async def status_new_add_object(message: types.Message, state: FSMContext):
    company_id = (await state.get_data())["company_id"]
    facilities = await get_facilities(company_id)

    text = "Я вас не понимаю\n⬇️ Выберите пункт меню ⬇️"
    keyboard = await facility_keyboard(facilities)
    await send_last_message(message.from_user.id, text, keyboard)


@dp.callback_query_handler(text="set_person_continue", state=Status.new_add_change_people)
async def bet_set_person_continue(callback_query: types.CallbackQuery, state: FSMContext):
    confirms = (await state.get_data())["confirms"]
    for i in range(1, len(confirms)+1):
        if i in confirms:
            if not confirms[i]["choose"]:
                del confirms[i]
        if i not in confirms:
            for j in range(i+1, 100):
                if j in confirms:
                    if not confirms[j]["choose"]:
                        del confirms[j]
                    else:
                        confirms[i] = confirms[j]
                        del confirms[j]
                        break
        if i not in confirms:
            break

    text = "Напишите комментарий\n⬇️ Или выберите пункт меню ⬇️"
    keyboard = await send_without_text_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_comment)
    await state.update_data(confirms=confirms)


@dp.callback_query_handler(text_startswith="set_person_", state=Status.new_add_change_people)
async def bet_set_person_(callback_query: types.CallbackQuery, state: FSMContext):
    tg_id = callback_query.data.replace("set_person_", "")
    confirms = (await state.get_data())["confirms"]
    for priority in confirms:
        if str(confirms[priority]["tg_id"]) == tg_id:
            confirms[priority]["choose"] = not confirms[priority]["choose"]

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await people_keyboard(confirms)
    await send_last_message(callback_query.from_user.id, text, keyboard)
    await state.update_data(confirms=confirms)


@dp.message_handler(state=Status.new_add_change_people, content_types=types.ContentType.ANY)
async def status_new_add_change_people(message: types.Message, state: FSMContext):
    confirms = (await state.get_data())["confirms"]

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await people_keyboard(confirms)
    await send_last_message(message.from_user.id, text, keyboard)


@dp.callback_query_handler(text="send_without_text", state=Status.new_add_comment)
async def but_send_without_text(callback_query: types.CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query.from_user.id)
    data = await state.get_data()
    data["comments"] = []

    doc_id = await insert_document(data)
    await send_document(doc_id)

    await state.finish()


@dp.message_handler(state=Status.new_add_comment, content_types=types.ContentType.ANY)
async def status_new_add_comment(message: types.Message, state: FSMContext):
    if message.content_type != "text":
        text = "Я вас не понимаю\nНапишите комментарий\n⬇️ Или выберите пункт меню ⬇️"
        keyboard = await send_without_text_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return

    await delete_last_message(message.from_user.id)
    data = await state.get_data()
    admin = await get_admin(message.from_user.id)
    data["comments"] = [f"{admin['name']}: {message.text}"]

    doc_id = await insert_document(data)
    await send_document(doc_id)

    await state.finish()


@dp.callback_query_handler(text="cancel", state="*")
async def but_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query.from_user.id)
    await delete_document(await state.get_data())
    await state.finish()


@dp.callback_query_handler(text_startswith="yes_", state="*")
async def but_yes_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("yes_", "")
    await update_document_confirm(doc_id, callback_query.from_user.id, True)
    await change_document_message(doc_id)


@dp.callback_query_handler(text_startswith="no_", state="*")
async def but_no_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("no_", "")
    await update_document_confirm(doc_id, callback_query.from_user.id, False)

    await change_document_message(doc_id)


@dp.callback_query_handler(text_startswith="add_comment_")
async def but_add_comment_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("add_comment_", "")

    text = "Введите комментарий"
    keyboard = await cancel_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.old_add_comment)
    await state.update_data(doc_id=doc_id)


@dp.callback_query_handler(text_startswith="add_new_doc_")
async def but_add_new_doc_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("add_new_doc_", "")

    text = "⬇️ Отправьте картинку или документ ⬇️"
    keyboard = await cancel_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.old_add_new_doc)
    await state.update_data(doc_id=doc_id)


@dp.message_handler(state=Status.old_add_new_doc, content_types=types.ContentType.ANY)
async def status_new_add_document(message: types.Message, state: FSMContext):
    doc_id = (await state.get_data())["doc_id"]
    document = await get_document(doc_id)
    if message.content_type == "photo":
        document_name = f"{datetime.now().strftime('%d-%m-%Y %H.%M.%S')}.png"
        await message.photo[-1].download(destination_file=document_name)
        await update_document_file_name(doc_id, document_name)
    elif message.content_type == "document":
        document_name = message.document.file_name
        await message.document.download(destination_file=document_name)
        await update_document_file_name(doc_id, document_name)
    else:
        text = "Я вас не понял\n⬇️ Отправьте картинку или документ ⬇️"
        keyboard = await cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return

    await state.finish()
    await send_document(doc_id)
    await delete_last_message(message.from_user.id)
    try:
        await bot.delete_message(document["message_id"]["creator"]["tg_id"], document["message_id"]["creator"]["mes_id"])
    except:
        pass
    try:
        for priority in document["confirms"]:
            if "confirm" not in document["confirms"][priority]:
                await bot.delete_message(document["message_id"][priority]["tg_id"], document["message_id"][priority]["mes_id"])
                break
    except:
        pass


@dp.callback_query_handler(text_startswith="skip_", state="*")
async def but_yes_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("skip_", "")
    document = await get_document(doc_id)
    for priority in document["confirms"]:
        if "confirm" not in document["confirms"][priority]:
            await update_document_confirm(doc_id, document["confirms"][priority]["tg_id"], None)
            break

    await change_document_message(doc_id)


@dp.message_handler(state=Status.old_add_comment, content_types=types.ContentType.ANY)
async def status_old_add_comment(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    if message.content_type != "text":
        text = "Я вас не понимаю\nВведите комментарий"
        keyboard = await cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return

    doc_id = (await state.get_data())["doc_id"]
    admin = await get_admin(message.from_user.id)
    name = admin["name"]
    await update_document_comments(doc_id, name, message.text)
    await change_document_message(doc_id)

    await state.finish()


@dp.callback_query_handler(state="*")
async def all_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
