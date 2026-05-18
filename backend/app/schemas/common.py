from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
