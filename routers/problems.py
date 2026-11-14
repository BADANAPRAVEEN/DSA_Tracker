from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from routers.auth import get_current_user
from schemas import Problem, ReviewResult

router = APIRouter()
INTERVAL_DAYS = [1, 3, 7, 14, 30]


@router.get("/problems")
def get_problems(
    topic: Optional[str] = None,
    difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = None,
    solved: Optional[bool] = None,
    search: Optional[str] = None,
    user_id: int = Depends(get_current_user),
):
    query = "SELECT * FROM problems WHERE user_id = %s"
    params = [user_id]

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
def add_problem(problem: Problem, user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            """INSERT INTO problems (title, topic, solved, difficulty, link, notes, user_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
            (problem.title, problem.topic, problem.solved,
             problem.difficulty, problem.link, problem.notes, user_id),
        ).fetchone()
    return row


@router.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int, user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM problems WHERE id = %s AND user_id = %s",
            (problem_id, user_id),
        )
        deleted = cursor.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Problem not found")


@router.patch("/problems/{problem_id}")
def toggle_solved(problem_id: int, user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            """UPDATE problems
               SET solved = NOT solved,
                   review_stage = 0,
                   next_review = CASE WHEN solved THEN NULL ELSE CURRENT_DATE + 1 END
               WHERE id = %s AND user_id = %s RETURNING *""",
            (problem_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return row


@router.get("/stats/topics")
def topic_stats(user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        return conn.execute("""
            SELECT topic,
                   COUNT(*)::int AS total,
                   SUM(solved::int)::int AS solved,
                   ROUND(100.0 * SUM(solved::int) / COUNT(*))::int AS percent_solved
            FROM problems
            WHERE user_id = %s
            GROUP BY topic
            ORDER BY percent_solved ASC
        """, (user_id,)).fetchall()


@router.get("/problems/due")
def due_problems(user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        return conn.execute(
            """SELECT * FROM problems
               WHERE user_id = %s AND solved AND next_review <= CURRENT_DATE
               ORDER BY next_review, id""",
            (user_id,),
        ).fetchall()


@router.post("/problems/{problem_id}/review")
def review_problem(problem_id: int, result: ReviewResult, user_id: int = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT review_stage, solved FROM problems WHERE id = %s AND user_id = %s",
            (problem_id, user_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Problem not found")
        if not row["solved"]:
            raise HTTPException(status_code=409, detail="Only solved problems can be reviewed")

        if result.remembered:
            stage = min(row["review_stage"] + 1, len(INTERVAL_DAYS) - 1)
        else:
            stage = 0

        updated = conn.execute(
            """UPDATE problems
               SET review_stage = %s,
                   next_review = CURRENT_DATE + %s::int,
                   last_reviewed = CURRENT_DATE
               WHERE id = %s AND user_id = %s RETURNING *""",
            (stage, INTERVAL_DAYS[stage], problem_id, user_id),
        ).fetchone()
    return updated