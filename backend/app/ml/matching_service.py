from app.ml.embedding_service import embedding_service
from app.ml.profile_text_service import profile_text_service
from app.ml.vector_store_service import vector_store_service


class MatchingService:

    def create_embedding(self, profile):
        profile_text = profile_text_service.create_profile_text(profile)
        return embedding_service.encode(profile_text)

    def similarity(self, profile_a, profile_b):
        embedding_a = self.create_embedding(profile_a)
        embedding_b = self.create_embedding(profile_b)

        return float(embedding_a @ embedding_b)

    def rank_matches(self, mentee, mentors):
        matches = []

        for mentor in mentors:
            similarity = self.similarity(mentee, mentor)

            matches.append({
                "id": mentor.id,
                "career_domain": mentor.career_domain,
                "career_path": mentor.career_path,
                "experience": mentor.experience,
                "skills": mentor.skills.split(","),
                "similarity_score": round(similarity * 100, 2)
            })

        matches.sort(
            key=lambda x: x["similarity_score"],
            reverse=True
        )

        return matches

    def retrieve_mentor_candidates(
        self,
        mentee,
        n_results: int = 5
    ):
        embedding = self.create_embedding(mentee)

        return vector_store_service.search_mentors(
            embedding,
            n_results=n_results
        )


matching_service = MatchingService()