from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import Problem

router = APIRouter()


@router.get("/problems")
def get_problems(
    topic: Optional[str] = None,
    difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = None,
    solved: Optional[bool] = None,
    search: Optional[str] = None,
):
    query = "SELECT * FROM problems WHERE TRUE"
    params = []

    if topic:
        query += " AND topic ILIKE %s"
        params.append(topic)
    if difficulty:
        query += " AND difficulty = %s"
        params.append(difficulty)
    if solved is not None:
        query += " AND solved = %s"
        params.append(solved)
    if search:
        query += " AND title ILIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY id"

    with get_db() as conn:
        return conn.execute(query, params).fetchall()


@router.post("/problems", status_code=201)
def add_problem(problem: Problem):
    with get_db() as conn:
        row = conn.execute(
            """INSERT INTO problems (title, topic, solved, difficulty, link, notes)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
            (problem.title, problem.topic, problem.solved,
             problem.difficulty, problem.link, problem.notes),
        ).fetchone()
    return row


@router.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM problems WHERE id = %s", (problem_id,))
        deleted = cursor.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Problem not found")


@router.patch("/problems/{problem_id}")
def toggle_solved(problem_id: int):
    with get_db() as conn:
        row = conn.execute(
            "UPDATE problems SET solved = NOT solved WHERE id = %s RETURNING *",
            (problem_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return row


@router.get("/stats/topics")
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