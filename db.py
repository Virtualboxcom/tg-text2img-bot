# db.py
import os
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "tg_data.db")


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                chat_id INTEGER,
                text TEXT,
                date TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                chat_id INTEGER,
                file_path TEXT,
                caption TEXT,
                date TEXT
            )
            """
        )
        await db.commit()


async def insert_message(message_id, chat_id, text, date):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (message_id, chat_id, text, date) VALUES (?, ?, ?, ?)",
            (message_id, chat_id, text, date),
        )
        await db.commit()


async def insert_image(message_id, chat_id, file_path, caption, date):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO images (message_id, chat_id, file_path, caption, date) VALUES (?, ?, ?, ?, ?)",
            (message_id, chat_id, file_path, caption, date),
        )
        await db.commit()
