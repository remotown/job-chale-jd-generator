from fastapi.testclient import TestClient
from src.main import app
from src.prompts import build_prompts
from src.models import JDGenerateRequest

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_generate_jd_all_fields_single_format():
    payload = {
        "job_title": "Senior Python Developer",
        "rough_idea": "Build scalable FastAPI backend services.",
        "employment_type": "Full-time",
        "experience_level": "Senior",
        "location": "Remote",
        "salary_min": "80,000",
        "salary_max": "120,000",
        "currency": "USD",
        "tone": "casual",
        "format": "general"
    }
    response = client.post("/api/generate-jd", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Senior Python Developer"
    assert "general" in data["formats"]
    assert "Senior Python Developer" in data["formats"]["general"]
    assert "80,000 - 120,000 USD" in data["formats"]["general"]

def test_generate_jd_multi_format():
    payload = {
        "job_title": "Frontend Engineer",
        "location": "Accra, Ghana",
        "format": ["general", "whatsapp", "linkedin"]
    }
    response = client.post("/api/generate-jd", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Frontend Engineer"
    assert set(data["formats"].keys()) == {"general", "whatsapp", "linkedin"}
    assert "📌 Frontend Engineer" in data["formats"]["whatsapp"]
    assert "Accra, Ghana" in data["formats"]["whatsapp"]

def test_prompts_role_overview_embedded():
    req = JDGenerateRequest(job_title="Designer", tone="casual", format=["general"])
    sys_prompt, user_prompt = build_prompts(req, "general")
    assert "ROLE OVERVIEW INSTRUCTION" in user_prompt
    assert "Role overview paragraph" not in user_prompt or "ROLE OVERVIEW" in user_prompt
