class ProfileTextService:

    def create_profile_text(self, profile) -> str:
        return (
            f"Career domain: {profile.career_domain}. "
            f"Career path: {profile.career_path}. "
            f"Experience: {profile.experience}. "
            f"Skills: {profile.skills}. "
            f"Career goals: {profile.career_goals}. "
            f"Availability: {profile.availability}."
        )


profile_text_service = ProfileTextService()