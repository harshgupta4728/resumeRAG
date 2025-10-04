import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models.models import Base, User, Resume, Job
from app.core.security import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user."""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        role="recruiter"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_register():
    """Test user registration."""
    response = client.post("/api/register", json={
        "email": "newuser@example.com",
        "password": "newpassword",
        "role": "recruiter"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "recruiter"

def test_login(test_user):
    """Test user login."""
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_create_job(auth_headers):
    """Test job creation."""
    response = client.post("/api/jobs", json={
        "title": "Python Developer",
        "description": "Looking for a Python developer with FastAPI experience"
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Python Developer"
    assert data["description_text"] == "Looking for a Python developer with FastAPI experience"

def test_get_job(auth_headers):
    """Test getting a job."""
    # First create a job
    create_response = client.post("/api/jobs", json={
        "title": "Test Job",
        "description": "Test description"
    }, headers=auth_headers)
    job_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/api/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Job"

def test_ask_question(auth_headers):
    """Test asking questions about resumes."""
    response = client.post("/api/ask", json={
        "query": "Who has Python experience?",
        "k": 3
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)

def test_rate_limiting():
    """Test rate limiting middleware."""
    # Make 61 requests quickly to trigger rate limit
    for i in range(61):
        response = client.get("/")
        if response.status_code == 429:
            assert response.json()["error"]["code"] == "RATE_LIMIT"
            break
    else:
        pytest.fail("Rate limiting should have been triggered")

def test_error_handling():
    """Test uniform error handling."""
    response = client.post("/api/login", json={
        "email": "invalid-email",
        "password": "test"
    })
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "field" in data["error"]
    assert "message" in data["error"]
