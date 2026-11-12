from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers.problems import router as problems_router
from routers.auth import router as auth_router

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

init_db()
app.include_router(problems_router)
app.include_router(auth_router)