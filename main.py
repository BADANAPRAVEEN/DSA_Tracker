import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi import HTTPException


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=[
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://dsa-tracker-1-sowf.onrender.com",
    ],
)

def get_db():
    conn = sqlite3.connect("tracker.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            solved INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Problem(BaseModel):
    title: str = Field(min_length = 1)
    topic: str = Field(min_length = 1)
    solved: bool = False

@app.get("/problems")
def get_problems():
    conn = get_db()
    rows = conn.execute("SELECT * FROM problems").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/problems", status_code=201)
def add_problem(problem: Problem):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO problems (title, topic, solved) VALUES (?, ?, ?)",
        (problem.title, problem.topic, int(problem.solved)),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, **problem.model_dump()}

@app.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int):
    conn = get_db()
    cursor = conn.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="problem not found")