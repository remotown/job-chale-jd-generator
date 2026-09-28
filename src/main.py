from fastapi import FastAPI, status
from src.config import settings
from src.models import JDGenerateRequest, JDGenerateResponse
from src.service import generate_job_descriptions

app = FastAPI(
    title="Job Chale JD Generator",
    description="Backend service for generating Job Chale Job Descriptions with unique field requirements.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Job Chale JD Generator API",
        "environment": settings.APP_ENV
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/generate-jd", response_model=JDGenerateResponse, status_code=status.HTTP_200_OK)
def generate_jd(request: JDGenerateRequest):
    return generate_job_descriptions(request)
