from fastapi import FastAPI, status, HTTPException, Request
from collections import defaultdict
import time
from src.config import settings
from src.models import JDGenerateRequest, JDGenerateResponse
from src.service import generate_job_descriptions

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, requests: int, period: int):
        self.requests = requests
        self.period = period
        self.clients = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        # Remove old requests outside the time window
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if now - timestamp < self.period
        ]
        
        if len(self.clients[client_id]) >= self.requests:
            return False
        
        self.clients[client_id].append(now)
        return True

rate_limiter = RateLimiter(settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_PERIOD)

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
def generate_jd(http_request: Request, request: JDGenerateRequest):
    client_id = http_request.client.host if http_request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_REQUESTS} requests per {settings.RATE_LIMIT_PERIOD} seconds."
        )
    
    try:
        return generate_job_descriptions(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
