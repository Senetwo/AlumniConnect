import logging

from app.database.database import settings
from app.ml.embedding_service import embedding_service
from app.ml.vector_store_service import vector_store_service


logger = logging.getLogger(__name__)


def resource_key(resource_id: int) -> str:
    return f"resource:{resource_id}"


def announcement_key(announcement_id: int) -> str:
    return f"announcement:{announcement_id}"


class KnowledgeIndexService:
    """Keeps the "Ask the library" index in step with admin-curated content.

    Only published resources and announcements are indexed, so unpublished or private
    text can never be retrieved. Like mentor indexing, a failure here is logged and must
    never block the admin action that triggered it.
    """

    def index_resource(self, resource):
        text = f"{resource.title}. {resource.description}"
        vector_store_service.upsert_knowledge(
            doc_id=resource_key(resource.id),
            embedding=embedding_service.encode(text),
            document=text,
            metadata={
                "source_type": "resource",
                "source_id": resource.id,
                "title": resource.title,
                "url": resource.url or "",
            },
        )

    def index_announcement(self, announcement):
        text = f"{announcement.title}. {announcement.body}"
        vector_store_service.upsert_knowledge(
            doc_id=announcement_key(announcement.id),
            embedding=embedding_service.encode(text),
            document=text,
            metadata={
                "source_type": "announcement",
                "source_id": announcement.id,
                "title": announcement.title,
                "url": "",
            },
        )

    def sync_resource(self, resource):
        if settings.app_env == "test":
            return
        try:
            if resource.is_published:
                self.index_resource(resource)
            else:
                vector_store_service.delete_knowledge(resource_key(resource.id))
        except Exception:
            logger.exception("Could not update the library index for resource %s", resource.id)

    def remove_resource(self, resource_id: int):
        if settings.app_env == "test":
            return
        try:
            vector_store_service.delete_knowledge(resource_key(resource_id))
        except Exception:
            logger.exception("Could not remove resource %s from the library index", resource_id)

    def sync_announcement(self, announcement):
        if settings.app_env == "test":
            return
        try:
            self.index_announcement(announcement)
        except Exception:
            logger.exception("Could not index announcement %s", announcement.id)

    def reindex_all(self, db) -> dict:
        """Rebuild the index from the database (backfill, or repair after drift)."""
        from app.models.knowledge_resource import KnowledgeResource
        from app.models.network import Announcement

        wanted = {}
        for resource in db.query(KnowledgeResource).filter(KnowledgeResource.is_published.is_(True)).all():
            wanted[resource_key(resource.id)] = ("resource", resource)
        for announcement in db.query(Announcement).all():
            wanted[announcement_key(announcement.id)] = ("announcement", announcement)

        for stale in set(vector_store_service.knowledge_ids()) - set(wanted):
            vector_store_service.delete_knowledge(stale)

        for kind, item in wanted.values():
            if kind == "resource":
                self.index_resource(item)
            else:
                self.index_announcement(item)

        return {"indexed": len(wanted)}


knowledge_index_service = KnowledgeIndexService()
