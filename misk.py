import asyncio
import email
import imaplib
import os
import logging
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from config import *
from keyboards import *
from postgres import *


class Status(StatesGroup):
    new_add_document = State()
    new_add_company = State()
    new_add_facility = State()
    new_add_change_people = State()
    new_add_comment = State()

    old_add_comment = State()
    old_add_new_doc = State()


class CheckBotStatusMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        await bot.delete_message(message.from_user.id, message.message_id)
        await self.before_any_process(message.from_user.id, message.message_id, message.text)
        logging.info(f"\n   Пользователь: {message.from_user.id} прислал сообщение\n"
                     f"   Id сообщения: {message.message_id}\n"
                     f"   Текст сообщения: {message.text}\n"
                     f"   Тип сообщения: {message.content_type}")

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        await callback_query.answer()
        logging.info(f"\n   Пользователь: {callback_query.from_user.id} нажал кнопку\n"
                     f"   Id сообщения: {callback_query.message.message_id}\n"
                     f"   Текст сообщения: {callback_query.message.text}\n"
                     f"   Callback: {callback_query.data}")
        await self.before_any_process(callback_query.from_user.id, callback_query.message.message_id,
                                      call_data=callback_query.data)

    @staticmethod
    async def before_any_process(user_id, mes_id, mes_text=None, call_data=None):
        if user_id == 641825727 and is_testing is False:
            text = "Работаю!"
            await send_message(user_id, text)
        admin = await get_admin(user_id)
        if admin is None:
            raise CancelHandler()


middleware = CheckBotStatusMiddleware()
dp.middleware.setup(middleware)


async def change_buttons():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def send_message(chat_id, text, keyboard=None, document=None, reply=None):
    if document:
        try:
            document_file = open(str(document), "rb")
            mes = await bot.send_document(chat_id, document_file, caption=text, reply_markup=keyboard,reply_to_message_id=reply)
            logging.info(f"\n   Бот ответил пользователю {mes.chat.id}\n"
                         f"   Id сообщения: {mes.message_id}\n"
                         f"   Текст сообщения: {mes.text}\n")
            return mes
        except Exception as e:
            logging.error(f"send_message {chat_id}", exc_info=True)

    try:
        mes = await bot.send_message(chat_id, text=text, reply_markup=keyboard, reply_to_message_id=reply)
        logging.info(f"\n   Бот ответил пользователю: {mes.chat.id}\n"
                     f"   Id сообщения: {mes.message_id}\n"
                     f"   Текст сообщения: {mes.text}\n")
        return mes
    except Exception as e:
        logging.error(f"send_message {chat_id}", exc_info=True)


async def send_last_message(chat_id, text, keyboard=None):
    await delete_last_message(chat_id)
    mes = await send_message(chat_id, text, keyboard)
    last_message[chat_id] = mes.message_id
    return mes


async def delete_last_message(chat_id):
    if chat_id in last_message:
        try:
            await bot.delete_message(chat_id, last_message[chat_id])
            del (last_message[chat_id])
        except Exception as e:
            logging.error(f"delete_last_message {chat_id} {last_message[chat_id]}", exc_info=True)


async def change_message(chat_id, mes_id, text, keyboard=None, caption=False):
    try:
        if caption:
            mes = await bot.edit_message_caption(chat_id, mes_id, caption=text, reply_markup=keyboard)
            logging.info(f"\n   Бот меняет сообщение пользователя {mes.chat.id}\n"
                         f"   Id сообщения: {mes.message_id}\n"
                         f"   Текст сообщения: {mes.text}\n")

        else:
            mes = await bot.edit_message_text(text, chat_id, mes_id, reply_markup=keyboard)
            logging.info(f"\n   Бот меняет сообщение пользователя {mes.chat.id}\n"
                         f"   Id сообщения: {mes.message_id}\n"
                         f"   Текст сообщения: {mes.text}\n")
    except Exception as e:
        if e.args[0] == ("Message is not modified: specified new message content and reply "
                         "markup are exactly the same as a current content and reply markup of the message"):
            return
        else:
            logging.error(f"change_message", exc_info=True)


async def delete_document(data):
    if "document_name" in data and data["document_name"] is not None:
        try:
            os.remove(data["document_name"])
        except Exception as e:
            pass


async def create_document_text_creator(document):
    text = ""
    keyboard = await confirm_creator_keyboard(document["document_id"])
    confirm_text = ""

    for priority in document["confirms"]:
        if "confirm" not in document["confirms"][priority]:
            confirm_text += document["confirms"][priority]["name"] + ": \n"
        elif document["confirms"][priority]["confirm"] is False:
            confirm_text += document["confirms"][priority]["name"] + ": ❌\n"
            keyboard = None
        else:
            confirm_text += document["confirms"][priority]["name"] + ": ✅\n"

    if document["status"]:
        text += document["status"] + "\n\n"
        keyboard = None
    text += document["company"] + "\n\n"
    if document["facility"]:
        text += document["facility"] + "\n\n"
    if document["text"]:
        text += document["text"] + "\n\n"
    for comment in document["comments"]:
        text += comment + "\n"
    if document["comments"]:
        text += "\n"
    text += confirm_text
    return text, keyboard


async def create_document_text_next(document):
    text = ""
    keyboard = await confirm_keyboard(document["document_id"])

    text += "Создатель: " + document["creator"]["name"] + "\n\n"
    text += document["company"] + "\n\n"
    if document["facility"]:
        text += document["facility"] + "\n\n"
    if document["text"]:
        text += document["text"] + "\n\n"
    for comment in document["comments"]:
        text += comment + "\n"
    return text, keyboard


async def create_document_text_other(document):
    text = ""
    keyboard = None

    if document["status"]:
        text += document["status"] + "\n\n"
    text += "Создатель: " + document["creator"]["name"] + "\n\n"
    text += document["company"] + "\n\n"
    if document["facility"]:
        text += document["facility"] + "\n\n"
    if document["text"]:
        text += document["text"] + "\n\n"
    for comment in document["comments"]:
        text += comment + "\n"
    return text, keyboard


async def send_document(doc_id):
    document = await get_document(doc_id)
    next_id = None
    next_priority = None
    for priority in document["confirms"]:
        if "confirm" not in document["confirms"][priority]:
            next_id = document["confirms"][priority]["tg_id"]
            next_priority = priority
            break

    if next_id is not None:
        creator_text, creator_keyboard = await create_document_text_creator(document)
        next_text, next_keyboard = await create_document_text_next(document)
    else:
        document["status"] = "🟡 Отправлено 🟡"
        await update_document_status(doc_id, document["status"])

        creator_text, creator_keyboard = await create_document_text_creator(document)

    # отправка создателю
    try:
        if document["document_name"]:
            mes = await send_message(document["creator"]["tg_id"], creator_text, creator_keyboard, document['document_name'])
            document["file_id"] = mes.document.file_id
            await update_document_file_id(doc_id, mes.document.file_id)
        else:
            mes = await send_message(document["creator"]["tg_id"], creator_text, creator_keyboard)
        document["message_id"]["creator"] = {"tg_id": document["creator"]["tg_id"], "mes_id": mes.message_id}
    except Exception as e:
        logging.error(f"send_document {document['creator']['tg_id']}", exc_info=True)
        await delete_document(document)
        return

    # отправка следующим
    if next_id is not None:
        try:
            if document["document_name"]:
                mes = await send_message(next_id, next_text, next_keyboard, document['document_name'])
            else:
                mes = await send_message(next_id, next_text, next_keyboard)
            document["message_id"][next_priority] = {"tg_id": next_id, "mes_id": mes.message_id}
        except Exception as e:
            logging.error(f"send_document {next_id}", exc_info=True)
    # отправка заключающему
    else:
        try:
            await send_message_email(document)
        except Exception as e:
            logging.error(f"send_message_email", exc_info=True)

    await delete_document(document)
    await update_document_message_id(doc_id, document["message_id"])


async def change_document_message(doc_id):
    document = await get_document(doc_id)
    next_id = None
    next_priority = None
    if document["status"] is None:
        for priority in document["confirms"]:
            if "confirm" not in document["confirms"][priority]:
                next_id = document["confirms"][priority]["tg_id"]
                next_priority = priority
                break

    if next_id is not None:
        creator_text, creator_keyboard = await create_document_text_creator(document)
        next_text, next_keyboard = await create_document_text_next(document)
    else:
        if document["status"] is None:
            document["status"] = "🟡 Отправлено 🟡"
            await update_document_status(doc_id, document["status"])

        creator_text, creator_keyboard = await create_document_text_creator(document)
    other_text, other_keyboard = await create_document_text_other(document)

    # отправка создателю
    try:
        if document["document_name"]:
            await change_message(document["creator"]["tg_id"], document["message_id"]["creator"]["mes_id"], creator_text, creator_keyboard, True)
        else:
            await change_message(document["creator"]["tg_id"], document["message_id"]["creator"]["mes_id"], creator_text, creator_keyboard)
    except Exception as e:
        logging.error(f"change_document_message {document['creator']['tg_id']}", exc_info=True)

    # отправка следующим
    if next_id is not None:
        if next_priority in document["message_id"]:
            try:
                if document["document_name"]:
                    await change_message(document["message_id"][next_priority]["tg_id"], document["message_id"][next_priority]["mes_id"], next_text, next_keyboard, True)
                else:
                    await change_message(document["message_id"][next_priority]["tg_id"], document["message_id"][next_priority]["mes_id"], next_text, next_keyboard)
            except Exception as e:
                logging.error(f"change_document_message {next_id}", exc_info=True)
        else:
            try:
                if document["document_name"]:
                    await bot.download_file_by_id(document["file_id"], document["document_name"])
                    mes = await send_message(next_id, next_text, next_keyboard, document['document_name'])
                else:
                    mes = await send_message(next_id, next_text, next_keyboard)
                document["message_id"][next_priority] = {"tg_id": next_id, "mes_id": mes.message_id}
            except Exception as e:
                logging.error(f"change_document_message {next_id}", exc_info=True)

    # отправка заключающему
    elif document["status"] == "🟡 Отправлено 🟡":
        try:
            await send_message_email(document)
        except Exception as e:
            logging.error(f"send_message_email", exc_info=True)

    # отправка предыдущим
    for priority in document["confirms"]:
        if "confirm" in document["confirms"][priority]:
            try:
                if document["document_name"]:
                    await change_message(document["message_id"][priority]["tg_id"], document["message_id"][priority]["mes_id"], other_text, other_keyboard, True)
                else:
                    await change_message(document["message_id"][priority]["tg_id"], document["message_id"][priority]["mes_id"], other_text, other_keyboard)
            except Exception as e:
                logging.error(f"change_document_message {document['document_id']} {priority}", exc_info=True)

    await delete_document(document)
    await update_document_message_id(doc_id, document["message_id"])


async def send_message_email(document):
    try:
        if document["document_name"]:
            await bot.download_file_by_id(file_id=document["file_id"],
                                          destination=document["document_name"])
    except Exception as e:
        logging.error(f"send_message_email download_file_by_id {document['file_id']} {document['document_name']}",
                      exc_info=True)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = dest_email
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    text = "doc_num:" + str(document["document_id"]) + "\n"
    text += "Компания: " + str(document["company"]) + "\n"
    if document["facility"]:
        text += "Объект: " + str(document["facility"]) + "\n"
    text += "Автор: " + str(document["creator"]["name"]) + "\n\n"
    if document["text"]:
        text += document["text"] + "\n\n"
    for comment in document["comments"]:
        text += comment + "\n"
    text += "\n"
    for confirm in document["confirms"]:
        text += document["confirms"][confirm]["name"]
        if document["confirms"][confirm]["confirm"] is True:
            text += " +" + "\n"
        else:
            text += " пропуск" + "\n"
    text += "\n"

    if document["document_name"]:
        msg.attach(MIMEText(text))
        with open(f"{document['document_name']}", "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=document["document_name"]
            )
        part["Content-Disposition"] = 'attachment; filename="%s"' % document["document_name"]
        msg.attach(part)
    else:
        msg.attach(MIMEText(text))

    server = smtplib.SMTP_SSL("smtp.yandex.ru", 465)
    server.login(from_email, from_email_password)
    server.sendmail(from_email, dest_email, msg.as_string())
    server.quit()

    try:
        os.remove(document["document_name"])
    except Exception as e:
        logging.error(f"send_message_email remove {document['document_name']}",
                      exc_info=True)


async def read_messages():
    try:
        connection = imaplib.IMAP4_SSL(host="imap.yandex.ru", port=993)
        connection.login(user=from_email, password=from_email_password)
        status, msgs = connection.select("INBOX")
        assert status == "OK"
    except Exception as e:
        logging.error(f"read_messages", exc_info=True)
        return

    typ, mail_data = connection.search(None, f'HEADER FROM "{dest_email}"')
    for num in mail_data[0].split():
        typ, message_data = connection.fetch(num, "(RFC822)")
        doc_id = re.search("doc_num:(\d+)", str(message_data[0][1])).group(1)
        mail = email.message_from_bytes(message_data[0][1])
        connection.store(num, "+FLAGS", "\\Deleted")
        if mail.is_multipart():
            for part in mail.walk():
                filename = part.get_filename()
                if filename:
                    with open(f"{doc_id}.pdf", "wb") as new_file:
                        new_file.write(part.get_payload(decode=True))
                    await send_paid_document(int(doc_id))
    connection.expunge()
    connection.close()
    connection.logout()


async def send_paid_document(doc_id):
    document = await get_document(doc_id)
    if document is not None:
        await update_document_status(doc_id, "🟢 Принято 🟢")
        await change_document_message(doc_id)

        document = await get_document(doc_id)

        await send_message(document["creator"]["tg_id"], None, None, f"{doc_id}.pdf", document["message_id"]["creator"]["mes_id"])
    try:
        os.remove(f"{doc_id}.pdf")
    except Exception as e:
        logging.error(f"send_paid_document remove {doc_id}.pdf",
                      exc_info=True)

