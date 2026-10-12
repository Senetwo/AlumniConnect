AlumniConnect

An Intelligent Alumni Engagement and Mentorship Platform

AlumniConnect is a web-based platform designed to strengthen alumni engagement, facilitate professional mentorship, and promote knowledge sharing within the Kenya Airways alumni community.

The system uses semantic matching powered by Sentence-BERT embeddings to recommend relevant mentors based on career interests, professional experience, skills, and mentorship goals.

Project Overview

Traditional alumni networks often lack structured mechanisms for connecting professionals with suitable mentors. AlumniConnect addresses this challenge through an intelligent recommendation system and a centralized platform for professional networking.

The platform is designed to support alumni from different career domains, including aviation, engineering, technology, commercial operations, finance, human resources, and other professional fields.

Objectives

* Provide secure registration and authentication for mentors and mentees.
* Enable users to create and maintain professional profiles.
* Recommend suitable mentors using semantic similarity.
* Allow mentees to submit mentorship requests.
* Enable mentors to accept or decline incoming requests.
* Support future knowledge sharing and alumni engagement features.

Technology Stack

Layer	Technology
Frontend	React, Vite, JavaScript, HTML, CSS
Backend	Python, FastAPI
Database	PostgreSQL
ORM	SQLAlchemy
Machine Learning	Sentence-BERT, Sentence Transformers
Vector Database	ChromaDB
Authentication	JWT, Role-Based Access Control
Testing	Pytest, FastAPI TestClient
Development Tools	VS Code, Git, GitHub, Docker

System Architecture

AlumniConnect follows a modular architecture consisting of:

1. Presentation Layer: React-based user interface.
2. Application Layer: FastAPI REST endpoints handling authentication, profiles, matching, and mentorship workflows.
3. Data Layer: PostgreSQL for structured records and ChromaDB for vector embeddings.
4. Machine Learning Layer: Sentence-BERT embeddings and similarity-based mentor recommendations.

Mentor Recommendation Workflow

1. A user registers and completes a professional profile.
2. Relevant profile information is prepared for semantic analysis.
3. The system generates embeddings using a fine-tuned Sentence-BERT model.
4. Mentor embeddings are stored and retrieved through ChromaDB.
5. Candidate mentors are ranked by semantic similarity.
6. The mentee receives mentor recommendations and can submit mentorship requests.

Features

Implemented Backend Features

* User registration and login
* JWT authentication
* Mentor and mentee role-based access control
* Professional profile creation and updates
* Semantic mentor recommendations
* Mentor profile vector indexing and retrieval
* Mentorship request creation
* Incoming mentorship request retrieval
* Mentorship request acceptance and rejection

Frontend Features

* Responsive landing page
* User registration and login
* Mentor discovery interface
* Mentorship request submission
* Editable user profiles
* Mentor Workspace for reviewing and responding to requests

Planned Features

* Knowledge Hub and shared professional resources
* Notifications
* Mentorship session scheduling
* Direct messaging
* Enhanced alumni community engagement
* Administrative moderation and reporting

Planned features are not yet represented as completed functionality.

Project Structure

AlumniConnect/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── ml/
│   │   ├── models/
│   │   └── schemas/
│   ├── ml_models/
│   │   └── alumniconnect_sbert_finetuned/
│   └── tests/
├── frontend/
│   ├── src/
│   └── package.json
├── .env
└── README.md

Installation and Setup

Prerequisites

* Python 3.13
* Node.js and npm
* PostgreSQL
* Docker (optional for running PostgreSQL)
* Git

1. Clone the Repository

git clone https://github.com/Senetwo/AlumniConnect.git
cd AlumniConnect

The repository is private; access is required to clone it.

2. Configure the Backend

cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

Install backend dependencies using the project’s dependency file, if available.

Create a .env file in the repository root with the required configuration:

APP_ENV=development
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME
SECRET_KEY=REPLACE_WITH_A_SECURE_SECRET
CHROMA_PERSIST_DIRECTORY=./chroma_data
EMBEDDING_MODEL=./backend/ml_models/alumniconnect_sbert_finetuned
LLM_API_KEY=

Replace placeholder credentials and secrets with local development values. Do not commit .env or production credentials.

The fine-tuned embedding model must be available at the configured location.

3. Start the Backend

From the backend directory:

uvicorn app.main:app --reload

API server:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

4. Start the Frontend

Open a separate terminal:

cd frontend
npm install
npm run dev

Open the application at:

http://localhost:5173

API Endpoints

Method	Endpoint	Description
POST	/api/auth/register	Register a new user
POST	/api/auth/login	Authenticate a user
GET	/api/auth/me	Retrieve the authenticated user
GET	/api/profiles/me	Retrieve the current user’s profile
PATCH	/api/profiles/me	Update the current user’s profile
GET	/api/matches/me	Retrieve recommended mentors
POST	/api/mentorships/	Submit a mentorship request
GET	/api/mentorships/incoming	Retrieve a mentor’s incoming requests
PATCH	/api/mentorships/{mentorship_id}/respond	Accept or decline a request

Protected endpoints require a valid JWT bearer token. Role-based authorization restricts access to appropriate users.

Machine Learning Approach

AlumniConnect uses Sentence-BERT to represent professional profile information as dense vector embeddings.

The recommendation process compares mentee profiles with indexed mentor profiles using semantic similarity.

Model Evaluation

The recommendation approach has been evaluated using synthetic profile data and relevance-labelled mentor–mentee pairs.

Evaluation metrics include:

* Precision@5
* Recall@5
* Mean Reciprocal Rank (MRR)
* F1@5

The evaluation compared TF-IDF, pretrained Sentence-BERT, and fine-tuned Sentence-BERT approaches.

The fine-tuned model achieved Precision@5 of 0.96, Recall@5 of approximately 0.5524, and MRR of 1.0 on the synthetic test set. These results matched the TF-IDF baseline on the reported metrics and should not be interpreted as evidence of superiority over TF-IDF or performance on real alumni data.

Testing

The backend uses Pytest for automated testing.

From the backend directory:

python -m pytest tests/ -v

The latest recorded backend test run completed successfully:

34 passed, 2 deprecation warnings.

The test suite covers authentication, access control, matching, mentorship workflows, profile endpoints, and vector-store functionality.

End-to-end frontend verification and additional integration testing remain part of ongoing development.

Security

The system incorporates:

* Password hashing
* JWT-based authentication
* Role-based authorization
* Protected API endpoints
* User-specific profile access
* Ownership checks for mentorship request responses
* Environment-based configuration for sensitive credentials

The project is currently a development prototype and should undergo further security testing before production deployment.

Current Development Status

AlumniConnect is under active development.

The core backend services and automated tests are functional. Frontend implementation and end-to-end integration are ongoing, including verification of the complete mentor–mentee workflow.

Knowledge management, notifications, and other extended community features are planned for subsequent development.

Academic Context

AlumniConnect is developed as a final-year Computer Science project, with Kenya Airways serving as the industry context for the proposed alumni engagement platform.

The system is intended to demonstrate the application of software engineering, artificial intelligence, database management, and web technologies to professional networking and mentorship.

Author

Senetwo

Computer Science Final-Year Project

GitHub: Senetwo

License

No open-source license has been specified. All rights remain reserved unless a license is added to the repository.