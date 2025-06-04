import psycopg2
import psycopg2.extras

from config import DB_HOST, DB_NAME, DB_USER, DB_PASS


async def postgres_do_query(query, params):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()
    return None


async def postgres_select_one(query, params):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, params)
    result = cursor.fetchone()
    if result:
        result = dict(result)
    conn.commit()
    cursor.close()
    conn.close()

    return result


async def postgres_select_all(query, params):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(query, params)
    results = cursor.fetchall()
    if results:
        res = []
        for r in results:
            res.append(dict(r))
        results = res
    conn.commit()
    cursor.close()
    conn.close()
    return results
