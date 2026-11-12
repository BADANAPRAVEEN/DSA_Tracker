from typing import Literal
from pydantic import BaseModel, Field


class Problem(BaseModel):
    title: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    solved: bool = False
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    link: str = ""
    notes: str = ""