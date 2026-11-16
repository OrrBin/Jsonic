"""A simple model whose presentation format also works with the old reader."""
from pydantic import BaseModel, Field


class Model(BaseModel):
    value: int = Field(alias='input')
