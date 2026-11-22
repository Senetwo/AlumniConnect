import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.api.profiles import get_db
from app.database.database import settings
from app.ml.knowledge_index_service import knowledge_index_service
from app.models.knowledge_resource import KnowledgeResource
from app.services import rag_answer
from app.schemas.knowledge import (
    KnowledgeResourceCreate,
    KnowledgeResourceUpdate,
    KnowledgeResourceResponse,
)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Hub"])

_ask_times: dict[int, deque] = defaultdict(deque)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskSource(BaseModel):
    type: str | None = None
    id: int | None = None
    title: str | None = None
    url: str | None = None
    similarity: float


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]
    grounded: bool
    generated: bool = False


def enforce_ask_limit(user_id: int) -> None:
    """Per-member sliding hour window. In memory, so it resets on restart (single-process prototype)."""
    now = time.monotonic()
    times = _ask_times[user_id]
    while times and now - times[0] > 3600:
        times.popleft()
    if len(times) >= settings.rag_questions_per_hour:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "You have asked many questions recently. Please try again later.")
    times.append(now)


@router.post("/ask", response_model=AskResponse)
def ask_the_library(data: AskRequest, current_user=Depends(get_current_user)):
    question = data.question.strip()
    if len(question) < 3:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Please enter a question.")
    enforce_ask_limit(current_user.id)
    try:
        return rag_answer.ask(question)
    except rag_answer.LLMNotConfigured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The library assistant is not configured.")
    except rag_answer.LLMUnavailable:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The library assistant is unavailable right now. Please try again.")


@router.post("/reindex")
def reindex_library(current_user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return knowledge_index_service.reindex_all(db)


@router.get("/", response_model=list[KnowledgeResourceResponse])
def list_published_resources(
    search: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(KnowledgeResource).filter(
        KnowledgeResource.is_published.is_(True)
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            KnowledgeResource.title.ilike(term)
            | KnowledgeResource.description.ilike(term)
            | KnowledgeResource.category.ilike(term)
        )

    if category and category.strip():
        query = query.filter(
            KnowledgeResource.category.ilike(category.strip())
        )

    return query.order_by(KnowledgeResource.created_at.desc()).all()


@router.get(
    "/admin",
    response_model=list[KnowledgeResourceResponse],
)
def list_all_resources(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    return (
        db.query(KnowledgeResource)
        .order_by(KnowledgeResource.created_at.desc())
        .all()
    )


@router.post(
    "/",
    response_model=KnowledgeResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    data: KnowledgeResourceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    resource = KnowledgeResource(
        title=data.title.strip(),
        description=data.description.strip(),
        category=data.category.strip(),
        resource_type=data.resource_type.strip(),
        url=str(data.url),
        source_name=data.source_name.strip() if data.source_name else None,
        source_author=data.source_author.strip() if data.source_author else None,
        publication_date=data.publication_date,
        is_published=data.is_published,
    )

    db.add(resource)
    db.commit()
    db.refresh(resource)
    knowledge_index_service.sync_resource(resource)
    return resource


@router.patch(
    "/{resource_id}",
    response_model=KnowledgeResourceResponse,
)
def update_resource(
    resource_id: int,
    data: KnowledgeResourceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    resource = (
        db.query(KnowledgeResource)
        .filter(KnowledgeResource.id == resource_id)
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip()
        if field == "url" and value is not None:
            value = str(value)
        setattr(resource, field, value)

    db.commit()
    db.refresh(resource)
    knowledge_index_service.sync_resource(resource)
    return resource


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    resource = (
        db.query(KnowledgeResource)
        .filter(KnowledgeResource.id == resource_id)
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

    db.delete(resource)
    db.commit()
    knowledge_index_service.remove_resource(resource_id)
