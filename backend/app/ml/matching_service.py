import numpy as np

from app.ml.embedding_service import embedding_service


class MatchingService:
    def create_profile_text(self, profile):
        return (
            f"Career domain: {profile.career_domain}. "
            f"Career path: {profile.career_path}. "
            f"Experience: {profile.experience}. "
            f"Skills: {profile.skills}. "
            f"Career goals: {profile.career_goals}. "
            f"Availability: {profile.availability}."
        )

    def similarity(self, profile_a, profile_b):
        text_a = self.create_profile_text(profile_a)
        text_b = self.create_profile_text(profile_b)

        embedding_a = embedding_service.encode(text_a)
        embedding_b = embedding_service.encode(text_b)

        score = float(np.dot(embedding_a, embedding_b))

        return score


matching_service = MatchingService()