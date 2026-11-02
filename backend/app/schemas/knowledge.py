
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class KnowledgeResourceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    category: str = Field(min_length=2, max_length=100)
    resource_type: str = Field(min_length=2, max_length=100)
    url: HttpUrl
    source_name: str | None = Field(default=None, max_length=200)
    source_author: str | None = Field(default=None, max_length=200)
    publication_date: date | None = None
    is_published: bool = False


class KnowledgeResourceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    resource_type: str | None = Field(default=None, min_length=2, max_length=100)
    url: HttpUrl | None = None
    source_name: str | None = Field(default=None, max_length=200)
    source_author: str | None = Field(default=None, max_length=200)
    publication_date: date | None = None
    is_published: bool | None = None


class KnowledgeResourceResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    resource_type: str
    url: str
    source_name: str | None = None
    source_author: str | None = None
    publication_date: date | None = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
