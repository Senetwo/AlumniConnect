
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.api.profiles import get_db
from app.models.knowledge_resource import KnowledgeResource
from app.schemas.knowledge import (
    KnowledgeResourceCreate,
    KnowledgeResourceUpdate,
    KnowledgeResourceResponse,
)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Hub"])


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
