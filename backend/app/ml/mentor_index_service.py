from app.ml.embedding_service import embedding_service
from app.ml.profile_text_service import profile_text_service
from app.ml.vector_store_service import vector_store_service


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

    def remove_mentor(self, mentor_id: int):
        vector_store_service.delete_mentor(mentor_id)

    def count(self):
        return vector_store_service.count()


mentor_index_service = MentorIndexService()