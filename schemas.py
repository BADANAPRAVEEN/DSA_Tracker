from typing import Literal
from pydantic import BaseModel, Field


class Problem(BaseModel):
    title: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    solved: bool = False
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    link: str = ""
    notes: str = ""

class UserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=64)