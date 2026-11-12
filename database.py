import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ["DATABASE_URL"]


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                solved BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        conn.execute("ALTER TABLE problems ADD COLUMN IF NOT EXISTS difficulty TEXT NOT NULL DEFAULT 'Medium'")
        conn.execute("ALTER TABLE problems ADD COLUMN IF NOT EXISTS link TEXT NOT NULL DEFAULT ''")
        conn.execute("ALTER TABLE problems ADD COLUMN IF NOT EXISTS notes TEXT NOT NULL DEFAULT ''")

        count = conn.execute("SELECT COUNT(*) AS n FROM problems").fetchone()["n"]
        if count == 0:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO problems (title, topic, solved, difficulty) VALUES (%s, %s, %s, %s)",
                    [
                        ("Two Sum", "Arrays", True, "Easy"),
                        ("Valid Parentheses", "Stack", False, "Easy"),
                        ("Maximum Subarray", "Arrays", False, "Medium"),
                        ("Binary Search", "Searching", True, "Easy"),
                    ],
                )