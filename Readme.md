# DSA Tracker

A full-stack web app to track DSA practice problems and find weak topics.

## Features
- Add, view, delete problems
- Toggle a problem as solved or unsolved
- Topic-wise stats, weakest topics first
- Input validation (empty titles are rejected)

## Tech stack
- **Backend:** Python, FastAPI, PostgreSQL(hosted on neon)
- **Frontend:** HTML, CSS, JavaScript (fetch API)

## How to run locally
1. `python -m venv venv` and activate it (`venv\Scripts\activate` on Windows)
2. `pip install -r requirements.txt`
3. `uvicorn main:app --reload`
4. Open `frontend/index.html` with Live Server
5. API docs are at `http://127.0.0.1:8000/docs`
6. Set a DATABASE_URL environment variable to a PostgreSQL connection string before running uvicorn

## API endpoints
| Method | URL | Purpose |
|--------|-----|---------|
| GET | /problems | List all problems |
| POST | /problems | Add a problem (201 on success, 422 on bad input) |
| PATCH | /problems/{id} | Toggle solved |
| DELETE | /problems/{id} | Delete a problem (404 if not found) |
| GET | /stats/topics | Per-topic stats using SQL GROUP BY |

## What I learned
- How the frontend talks to the backend: HTTP requests with `fetch`, JSON responses, and status codes (2xx success, 4xx client error, 5xx server error).
- Why browsers block cross-origin requests (CORS) and how to allow specific origins in FastAPI.
- Designing a SQL table and using `GROUP BY` to compute per-topic statistics.
- Validating input with Pydantic and returning correct errors, such as 422 for bad data and 404 for a missing row.
- Using Git and GitHub, including `.gitignore` and small commits.
- Moved from SQLite to hosted PostgreSQL, using environment variables for credentials so secrets never enter the repo.

## Future improvements
- User login, revision reminders, and AI-generated hints