import json

from postgres_queries import *


async def get_admin(tg_id):
    admin = await postgres_select_one("SELECT * FROM admins WHERE tg_id = %s AND agreement_bot2 IS NOT NULL;",
                                      (tg_id,))
    return admin


async def get_admins():
    admins = await postgres_select_all("SELECT * FROM admins WHERE agreement_bot2 IS NOT NULL;",
                                       None)
    ret_admins = {}
    for admin in admins:
        ret_admins[admin["tg_id"]] = {"name": admin["name"], "priority": admin["agreement_bot2_priority"]}
    return ret_admins


async def get_companies():
    return await postgres_select_all("SELECT * FROM companies WHERE status = true ORDER BY name;",
                                     None)


async def get_company(company_id):
    return await postgres_select_one("SELECT * FROM companies WHERE company_id = %s;",
                                     (company_id,))


async def get_facilities(company_id):
    return await postgres_select_all("SELECT * FROM facilities WHERE status = true and company_id = %s "
                                     "ORDER BY name;",
                                     (company_id,))


async def insert_document(data):
    doc = await postgres_select_one("INSERT INTO agreement_documents2 (creator, text, document_name, company, facility, "
                                    "confirms, comments, status, message_id) "
                                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING document_id;",
                                    (json.dumps(data["creator"], ensure_ascii=True), data["text"], data["document_name"],
                                     data["company"], data["facility"], json.dumps(data["confirms"], ensure_ascii=True),
                                     data["comments"], data["status"], json.dumps({}, ensure_ascii=True),))
    return doc["document_id"]


async def update_document_file_id(doc_id, file_id):
    await postgres_do_query("UPDATE agreement_documents2 SET file_id = %s WHERE document_id = %s;",
                            (file_id, doc_id))


async def update_document_message_id(doc_id, message_id):
    await postgres_do_query("UPDATE agreement_documents2 SET message_id = %s WHERE document_id = %s;",
                            (json.dumps(message_id, ensure_ascii=True), doc_id))


async def update_document_confirm(doc_id, user_id, confirm):
    document = await get_document(doc_id)
    for priority in document["confirms"]:
        if document["confirms"][priority]["tg_id"] == user_id and "confirm" not in document["confirms"][priority]:
            document["confirms"][priority]["confirm"] = confirm
            await postgres_do_query("UPDATE agreement_documents2 SET confirms = %s WHERE document_id = %s;",
                                    (json.dumps(document["confirms"], ensure_ascii=True), doc_id))
            if confirm is False:
                await update_document_status(doc_id, "🔴 Отменено 🔴")
            return


async def update_document_confirms(doc_id, confirms):
    await postgres_do_query("UPDATE agreement_documents2 SET confirms = %s WHERE document_id = %s;",
                            (json.dumps(confirms, ensure_ascii=True), doc_id))


async def update_document_comments(doc_id, user_name, comment):
    document = await get_document(doc_id)
    comments = document["comments"]
    comments.append(f"{user_name}: {comment}")
    await postgres_do_query("UPDATE agreement_documents2 SET comments = %s WHERE document_id = %s;",
                            (comments, doc_id))


async def update_document_status(doc_id, status):
    await postgres_do_query("UPDATE agreement_documents2 SET status = %s WHERE document_id = %s;",
                            (status, doc_id))


async def update_document_file_name(doc_id, document_name):
    await postgres_do_query("UPDATE agreement_documents2 SET document_name = %s WHERE document_id = %s;",
                            (document_name, doc_id))


async def get_document(doc_id):
    document = await postgres_select_one("SELECT * FROM agreement_documents2 WHERE document_id = %s;",
                                         (doc_id,))
    return document
