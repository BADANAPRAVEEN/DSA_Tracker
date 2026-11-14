# DSA Tracker

A full-stack web app to track DSA practice problems and find weak topics. Each user has their own account and their own problems.

**Live demo:** https://dsa-tracker-1-sowf.onrender.com
**API docs:** https://dsa-tracker-wakr.onrender.com/docs

> Hosted on a free plan, so the first request can take up to a minute while the server wakes up.

## Features
- Sign up and log in (JWT authentication, bcrypt-hashed passwords)
- Each user sees only their own problems (new accounts start with 4 sample problems)
- Add, toggle solved, and delete problems, with difficulty, link and notes
- Filter and search by topic, difficulty and solved status
- Topic-wise stats with the weakest topics first
- Input validation and friendly error messages
- Automated test suite (pytest)
- Spaced-repetition revision scheduler with a "due today" list.

## Tech stack
- **Backend:** Python, FastAPI, PostgreSQL (psycopg), Pydantic
- **Frontend:** HTML, CSS, JavaScript (fetch API)
- **Auth:** JWT (PyJWT), bcrypt
- **Testing:** pytest, FastAPI TestClient
- **Hosting:** Render (API and static frontend), Neon (PostgreSQL)

## How it works
```
Browser (JavaScript fetch + token) -> FastAPI route -> SQL (filtered by user_id) -> PostgreSQL -> JSON -> page updates
```
The frontend never touches the database. It sends HTTP requests with a Bearer token, and the backend verifies the token, applies ownership checks in SQL, and returns JSON with a status code.

## API endpoints
| Method | URL | Auth | Purpose |
|--------|-----|------|---------|
| POST | /auth/signup | No | Create an account (409 if the email exists, 422 on invalid input) |
| POST | /auth/login | No | Returns a JWT (401 on wrong credentials) |
| GET | /problems | Yes | List my problems (filters: topic, difficulty, solved, search) |
| POST | /problems | Yes | Add a problem (201, or 422 on invalid input) |
| PATCH | /problems/{id} | Yes | Toggle solved (404 if not mine) |
| DELETE | /problems/{id} | Yes | Delete a problem (204, or 404 if not mine) |
| GET | /stats/topics | Yes | Per-topic stats using SQL GROUP BY, weakest first |
| GET | /problems/due |
|POST | /problems/{id}/review |

## Security
- Passwords are hashed with bcrypt (salted), never stored in plain text.
- JWTs are signed with a server-side secret and expire after 60 minutes.
- Per-user data isolation: every query includes `WHERE user_id = ...`.
- SQL queries are parameterized to prevent SQL injection.
- The frontend only creates links that start with http(s) and uses `textContent`, to prevent XSS.
- CORS allows only the known frontend origins; secrets live in environment variables.

## Run locally
1. `python -m venv venv`, then activate it (`venv\Scripts\activate` on Windows)
2. `pip install -r requirements.txt`
3. Set environment variables: `DATABASE_URL` (a PostgreSQL connection string) and `SECRET_KEY` (a long random string)
4. `uvicorn main:app --reload`
5. Open `frontend/index.html` with Live Server
6. API docs are at `http://127.0.0.1:8000/docs`

## Run the tests
1. Create a separate PostgreSQL database or branch for testing (never use production).
2. Set `TEST_DATABASE_URL` to its connection string.
3. `pytest -v`

The tests refuse to run if `TEST_DATABASE_URL` is missing or equals `DATABASE_URL`.

## Project structure
```
dsa-tracker/
  main.py              # app setup, CORS, routers
  database.py          # connection, tables, migrations
  schemas.py           # request validation models
  routers/
    auth.py            # signup, login, token verification
    problems.py        # problem routes and stats
  tests/
    conftest.py        # shared fixtures and safety guard
    test_api.py        # API tests
  frontend/
    index.html, app.js, style.css
```

## What I learned
- How a frontend talks to a backend: HTTP requests, JSON, and status codes.
- CORS, and why browsers block cross-origin requests by default.
- Designing SQL tables, `GROUP BY` analytics, and schema migrations with `ALTER TABLE`.
- Moving from SQLite to hosted PostgreSQL after finding data was lost on every restart.
- Authentication vs authorization: password hashing, salting, signed JWTs, and ownership checks.
- Preventing SQL injection and XSS, and keeping secrets out of the repo.
- Writing automated tests against an isolated database branch.
- Deploying a frontend and backend separately, and debugging deploys from logs.

## Known limitations
- The JWT is stored in localStorage; httpOnly cookies would be safer against XSS.
- No rate limiting on login, no email verification or password reset.
- Free hosting sleeps when idle, so the first request can be slow.

## Planned improvements
- Progress dashboard with charts
- AI-generated hints