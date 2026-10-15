"""Tests for rate limiting functionality"""
import pytest
import time
from fastapi.testclient import TestClient
from src.main import app, rate_limiter
from src.config import settings


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Reset rate limiter for each test"""
        # Clear the rate limiter's client tracking
        rate_limiter.clients.clear()
    
    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within limit are allowed"""
        client_id = "127.0.0.1"
        
        # Make requests up to the limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            assert rate_limiter.is_allowed(client_id) is True
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over limit are blocked"""
        client_id = "127.0.0.1"
        
        # Exhaust the limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            rate_limiter.is_allowed(client_id)
        
        # Next request should be blocked
        assert rate_limiter.is_allowed(client_id) is False
    
    def test_rate_limiter_resets_after_period(self):
        """Test that rate limit resets after time period"""
        from src.main import RateLimiter
        
        client_id = "127.0.0.1"
        
        # Create a test-specific rate limiter with short period
        test_limiter = RateLimiter(requests=3, period=1)  # 3 requests per 1 second
        
        # Exhaust the limit
        for _ in range(3):
            test_limiter.is_allowed(client_id)
        
        # Should be blocked
        assert test_limiter.is_allowed(client_id) is False
        
        # Wait for period to expire
        time.sleep(1.1)  # Wait slightly longer than period
        
        # Should be allowed again
        assert test_limiter.is_allowed(client_id) is True
    
    def test_rate_limiter_different_clients_independent(self):
        """Test that different clients have independent limits"""
        client1 = "192.168.1.1"
        client2 = "192.168.1.2"
        
        # Exhaust limit for client1
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            rate_limiter.is_allowed(client1)
        
        # client1 should be blocked
        assert rate_limiter.is_allowed(client1) is False
        
        # client2 should still be allowed
        assert rate_limiter.is_allowed(client2) is True
    
    def test_rate_limiter_unknown_client(self):
        """Test that unknown client identifier works"""
        client_id = "unknown"
        assert rate_limiter.is_allowed(client_id) is True
    
    def test_api_endpoint_rate_limiting(self):
        """Test rate limiting on actual API endpoint"""
        client = TestClient(app)
        
        # Reset rate limiter
        rate_limiter.clients.clear()
        
        # Make requests up to limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            response = client.post("/api/generate-jd", json={"job_title": "Developer"})
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.post("/api/generate-jd", json={"job_title": "Developer"})
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
    
    def test_rate_limit_error_message(self):
        """Test that rate limit error message is informative"""
        client = TestClient(app)
        
        # Reset rate limiter
        rate_limiter.clients.clear()
        
        # Exhaust limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            client.post("/api/generate-jd", json={"job_title": "Developer"})
        
        # Check error message
        response = client.post("/api/generate-jd", json={"job_title": "Developer"})
        assert response.status_code == 429
        detail = response.json()["detail"]
        assert str(settings.RATE_LIMIT_REQUESTS) in detail
        assert str(settings.RATE_LIMIT_PERIOD) in detail
