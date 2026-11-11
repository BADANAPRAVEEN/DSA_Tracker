import os
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://dsa-tracker-1-sowf.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        # Migrations: safe to run every time, because of IF NOT EXISTS
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


init_db()


class Problem(BaseModel):
    title: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    solved: bool = False
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    link: str = ""
    notes: str = ""


@app.get("/problems")
def get_problems():
    with get_db() as conn:
        return conn.execute("SELECT * FROM problems ORDER BY id").fetchall()


@app.post("/problems", status_code=201)
def add_problem(problem: Problem):
    with get_db() as conn:
        row = conn.execute(
            """INSERT INTO problems (title, topic, solved, difficulty, link, notes)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
            (problem.title, problem.topic, problem.solved,
             problem.difficulty, problem.link, problem.notes),
        ).fetchone()
    return row


@app.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM problems WHERE id = %s", (problem_id,))
        deleted = cursor.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Problem not found")


@app.patch("/problems/{problem_id}")
def toggle_solved(problem_id: int):
    with get_db() as conn:
        row = conn.execute(
            "UPDATE problems SET solved = NOT solved WHERE id = %s RETURNING *",
            (problem_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return row


@app.get("/stats/topics")
def topic_stats():
    with get_db() as conn:
        return conn.execute("""
            SELECT topic,
                   COUNT(*)::int AS total,
                   SUM(solved::int)::int AS solved,
                   ROUND(100.0 * SUM(solved::int) / COUNT(*))::int AS percent_solved
            FROM problems
            GROUP BY topic
            ORDER BY percent_solved ASC
        """).fetchall()