import logging

from app.database.database import settings
from app.ml.embedding_service import embedding_service
from app.ml.profile_text_service import profile_text_service
from app.ml.vector_store_service import vector_store_service


logger = logging.getLogger(__name__)


class MentorIndexService:

    def index_mentor(self, mentor):
        profile_text = profile_text_service.create_profile_text(mentor)

        embedding = embedding_service.encode(profile_text)

        metadata = {
            "career_domain": mentor.career_domain,
            "career_path": mentor.career_path,
            "experience": mentor.experience,
        }

        vector_store_service.add_mentor(
            mentor_id=mentor.id,
            embedding=embedding,
            metadata=metadata
        )

    def sync_profile(self, profile, user):
        """Keep the matching index in step with a profile.

        Mentors are indexed so mentees can be matched to them; anyone else is removed.
        This must never block sign-up or a profile edit, so failures are only logged.
        """
        if settings.app_env == "test":
            return
        try:
            # Admins keep their mentor access but are not offered to mentees as recommendations.
            if (user.community_role or user.role) == "mentor" and user.role != "admin" and user.is_active:
                self.index_mentor(profile)
            else:
                self.remove_mentor(profile.id)
        except Exception:
            logger.exception("Could not update the mentor matching index for profile %s", profile.id)

    def remove_mentor(self, mentor_id: int):
        vector_store_service.delete_mentor(mentor_id)

    def count(self):
        return vector_store_service.count()


mentor_index_service = MentorIndexService()