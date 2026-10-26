
from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    remote: bool = False
    description: str = Field(min_length=1)


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
