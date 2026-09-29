from app.models.user import User

def test_register_mentee(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Mentee",
            "email": "mentee@test.com",
            "password": "SecurePassword123!",
            "role": "mentee",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "2 years",
                "skills": ["Python", "FastAPI"],
                "certifications": ["AWS Cloud Practitioner"],
                "career_goals": "Become a backend engineer",
                "mentorship_interests": ["Backend Development"],
                "availability": "Weekends",
                "bio": "Test mentee profile"
            }
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Mentee"
    assert data["email"] == "mentee@test.com"
    assert data["role"] == "mentee"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_mentor(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Mentor",
            "email": "mentor@test.com",
            "password": "SecurePassword123!",
            "role": "mentor",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Cloud Engineering",
                "experience": "8 years",
                "skills": ["AWS", "Docker", "Kubernetes"],
                "certifications": ["AWS Solutions Architect"],
                "career_goals": "Mentor upcoming engineers",
                "mentorship_interests": ["Cloud Computing"],
                "availability": "Evenings",
                "bio": "Test mentor profile"
            }
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Mentor"
    assert data["email"] == "mentor@test.com"
    assert data["role"] == "mentor"
    assert "password" not in data
    assert "password_hash" not in data
    
def test_admin_self_registration_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Admin",
            "email": "admin@test.com",
            "password": "SecurePassword123!",
            "role": "admin",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "5 years",
                "skills": ["Python"],
                "certifications": [],
                "career_goals": "Manage the platform",
                "mentorship_interests": [],
                "availability": "Weekdays",
                "bio": "Test admin registration"
            }
        }
    )

    assert response.status_code == 422
    
def test_duplicate_email_registration_is_rejected(client):
    payload = {
        "full_name": "First User",
        "email": "duplicate@test.com",
        "password": "SecurePassword123!",
        "role": "mentee",
        "profile": {
            "career_domain": "Technology & Digital",
            "career_path": "Software Engineering",
            "experience": "2 years",
            "skills": ["Python"],
            "certifications": [],
            "career_goals": "Become a software engineer",
            "mentorship_interests": ["Backend Development"],
            "availability": "Weekends",
            "bio": "First test user"
        }
    }

    first_response = client.post(
        "/api/auth/register",
        json=payload
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/api/auth/register",
        json=payload
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Email is already registered"
    
def test_valid_login_returns_access_token(client):
    registration_response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Login Test User",
            "email": "login@test.com",
            "password": "SecurePassword123!",
            "role": "mentee",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "2 years",
                "skills": ["Python", "FastAPI"],
                "certifications": [],
                "career_goals": "Become a backend engineer",
                "mentorship_interests": ["Backend Development"],
                "availability": "Weekends",
                "bio": "Login test user"
            }
        }
    )

    assert registration_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "login@test.com",
            "password": "SecurePassword123!"
        }
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    
def test_invalid_login_is_rejected(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Invalid Login User",
            "email": "invalid-login@test.com",
            "password": "SecurePassword123!",
            "role": "mentee",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "2 years",
                "skills": ["Python"],
                "certifications": [],
                "career_goals": "Become a backend engineer",
                "mentorship_interests": ["Backend Development"],
                "availability": "Weekends",
                "bio": "Invalid login test user"
            }
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "invalid-login@test.com",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    
def test_authenticated_user_can_be_retrieved(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "JWT Test User",
            "email": "jwt@test.com",
            "password": "SecurePassword123!",
            "role": "mentee",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "3 years",
                "skills": ["Python", "FastAPI"],
                "certifications": [],
                "career_goals": "Build secure backend systems",
                "mentorship_interests": ["Backend Development"],
                "availability": "Evenings",
                "bio": "JWT test user"
            }
        }
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "jwt@test.com",
            "password": "SecurePassword123!"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == "JWT Test User"
    assert data["email"] == "jwt@test.com"
    assert data["role"] == "mentee"
    
def test_unauthenticated_user_cannot_access_profiles(client):
    response = client.get("/api/profiles/")

    assert response.status_code == 401
    
def test_mentee_cannot_access_admin_profiles_endpoint(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Role Test Mentee",
            "email": "role-test@test.com",
            "password": "SecurePassword123!",
            "role": "mentee",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "2 years",
                "skills": ["Python"],
                "certifications": [],
                "career_goals": "Become a software engineer",
                "mentorship_interests": ["Backend Development"],
                "availability": "Weekends",
                "bio": "Role authorization test"
            }
        }
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "role-test@test.com",
            "password": "SecurePassword123!"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/profiles/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"
    
def test_registration_creates_linked_user_and_profile(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Relationship Test User",
            "email": "relationship@test.com",
            "password": "SecurePassword123!",
            "role": "mentor",
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Cloud Engineering",
                "experience": "7 years",
                "skills": ["AWS", "Docker", "Kubernetes"],
                "certifications": ["AWS Solutions Architect"],
                "career_goals": "Help upcoming cloud engineers",
                "mentorship_interests": ["Cloud Computing"],
                "availability": "Evenings",
                "bio": "Relationship test mentor"
            }
        }
    )

    assert response.status_code == 201

    user = db.query(User).filter(
        User.email == "relationship@test.com"
    ).first()

    assert user is not None
    assert user.profile is not None
    assert user.profile.user_id == user.id
    assert user.profile.career_domain == "Technology & Digital"
    assert user.profile.career_path == "Cloud Engineering"