"""Tests for JD generation service logic"""
import pytest
from src.models import JDGenerateRequest
from src.service import generate_job_descriptions, mock_generate_output
from src.prompts import build_prompts, get_salary_display, build_base_context


class TestJDGenerationLogic:
    """Test the core JD generation logic"""
    
    def test_generate_jd_single_format(self):
        """Test generating JD in a single format"""
        request = JDGenerateRequest(
            job_title="Software Engineer",
            rough_idea="Build web applications",
            format=["general"]
        )
        response = generate_job_descriptions(request)
        assert response.job_title == "Software Engineer"
        assert "general" in response.formats
        assert len(response.formats) == 1
    
    def test_generate_jd_multiple_formats(self):
        """Test generating JD in multiple formats"""
        request = JDGenerateRequest(
            job_title="Data Scientist",
            format=["general", "linkedin", "whatsapp"]
        )
        response = generate_job_descriptions(request)
        assert response.job_title == "Data Scientist"
        assert set(response.formats.keys()) == {"general", "linkedin", "whatsapp"}
    
    def test_mock_generation_with_casual_tone(self):
        """Test mock generation with casual tone"""
        request = JDGenerateRequest(
            job_title="Developer",
            tone="casual",
            format=["general"]
        )
        output = mock_generate_output(request, "general")
        assert "excited" in output.lower() or "awesome" in output.lower()
    
    def test_mock_generation_with_formal_tone(self):
        """Test mock generation with formal tone"""
        request = JDGenerateRequest(
            job_title="Developer",
            tone="formal",
            format=["general"]
        )
        output = mock_generate_output(request, "general")
        assert "notice" in output.lower() or "position" in output.lower()
    
    def test_mock_generation_whatsapp_format(self):
        """Test mock generation for WhatsApp format"""
        request = JDGenerateRequest(
            job_title="Developer",
            location="Remote",
            format=["whatsapp"]
        )
        output = mock_generate_output(request, "whatsapp")
        assert "📌" in output
        assert "🎯" in output
        assert "✅" in output
    
    def test_mock_generation_with_salary(self):
        """Test mock generation includes salary"""
        request = JDGenerateRequest(
            job_title="Developer",
            salary_min="50000",
            salary_max="70000",
            currency="USD",
            format=["general"]
        )
        output = mock_generate_output(request, "general")
        assert "50000" in output or "70000" in output
        assert "USD" in output


class TestPromptBuilding:
    """Test prompt building logic"""
    
    def test_build_prompts_general_format(self):
        """Test building prompts for general format"""
        request = JDGenerateRequest(
            job_title="Developer",
            tone="professional",
            format=["general"]
        )
        system_prompt, user_prompt = build_prompts(request, "general")
        assert "Developer" in system_prompt
        assert "professional" in system_prompt
        assert "job description" in user_prompt.lower()
        assert "ROLE OVERVIEW" in user_prompt
    
    def test_build_prompts_linkedin_format(self):
        """Test building prompts for LinkedIn format"""
        request = JDGenerateRequest(
            job_title="Developer",
            format=["linkedin"]
        )
        system_prompt, user_prompt = build_prompts(request, "linkedin")
        assert "LinkedIn job post" in user_prompt
        assert "Role Title:" in user_prompt
    
    def test_build_prompts_whatsapp_format(self):
        """Test building prompts for WhatsApp format"""
        request = JDGenerateRequest(
            job_title="Developer",
            format=["whatsapp"]
        )
        system_prompt, user_prompt = build_prompts(request, "whatsapp")
        assert "WhatsApp job post" in user_prompt
        assert "📌" in user_prompt
    
    def test_build_prompts_facebook_format(self):
        """Test building prompts for Facebook format"""
        request = JDGenerateRequest(
            job_title="Developer",
            format=["facebook"]
        )
        system_prompt, user_prompt = build_prompts(request, "facebook")
        assert "Facebook job post" in user_prompt
        assert "📢 WE'RE HIRING" in user_prompt
    
    def test_build_prompts_with_experience_level(self):
        """Test prompts include experience level"""
        request = JDGenerateRequest(
            job_title="Developer",
            experience_level="Senior",
            format=["general"]
        )
        system_prompt, user_prompt = build_prompts(request, "general")
        assert "Senior" in system_prompt
    
    def test_build_prompts_default_experience_level(self):
        """Test prompts use default experience level when not provided"""
        request = JDGenerateRequest(
            job_title="Developer",
            format=["general"]
        )
        system_prompt, user_prompt = build_prompts(request, "general")
        assert "mid-level" in system_prompt


class TestSalaryDisplay:
    """Test salary display logic"""
    
    def test_salary_display_min_max(self):
        """Test salary display with min and max"""
        request = JDGenerateRequest(
            job_title="Dev",
            salary_min="50000",
            salary_max="70000",
            currency="USD"
        )
        display = get_salary_display(request)
        assert "50000" in display
        assert "70000" in display
        assert "USD" in display
    
    def test_salary_display_min_only(self):
        """Test salary display with only minimum"""
        request = JDGenerateRequest(
            job_title="Dev",
            salary_min="50000",
            currency="USD"
        )
        display = get_salary_display(request)
        assert "From" in display
        assert "50000" in display
    
    def test_salary_display_max_only(self):
        """Test salary display with only maximum"""
        request = JDGenerateRequest(
            job_title="Dev",
            salary_max="70000",
            currency="USD"
        )
        display = get_salary_display(request)
        assert "Up to" in display
        assert "70000" in display
    
    def test_salary_display_single_value(self):
        """Test salary display with single value"""
        request = JDGenerateRequest(
            job_title="Dev",
            salary="60000",
            currency="USD"
        )
        display = get_salary_display(request)
        assert "60000" in display
        assert "USD" in display
    
    def test_salary_display_no_salary(self):
        """Test salary display when no salary provided"""
        request = JDGenerateRequest(job_title="Dev")
        display = get_salary_display(request)
        assert display == ""
    
    def test_salary_display_numeric_values(self):
        """Test salary display with numeric types"""
        request = JDGenerateRequest(
            job_title="Dev",
            salary_min=50000,
            salary_max=70000,
            currency="USD"
        )
        display = get_salary_display(request)
        assert "50000" in display
        assert "70000" in display


class TestBaseContext:
    """Test base context building"""
    
    def test_build_base_context_all_fields(self):
        """Test building context with all fields"""
        request = JDGenerateRequest(
            job_title="Developer",
            experience_level="Senior",
            employment_type="Full-time",
            location="Remote",
            salary_min="50000",
            salary_max="70000",
            currency="USD",
            rough_idea="Build APIs"
        )
        context = build_base_context(request)
        assert "Job Title: Developer" in context
        assert "Experience Level: Senior" in context
        assert "Employment Type: Full-time" in context
        assert "Location: Remote" in context
        assert "Salary:" in context
        assert "Role Outline" in context
    
    def test_build_base_context_minimal(self):
        """Test building context with minimal fields"""
        request = JDGenerateRequest(job_title="Developer")
        context = build_base_context(request)
        assert "Job Title: Developer" in context
        assert "Experience Level" not in context
    
    def test_build_base_context_empty_optional_fields(self):
        """Test building context ignores empty optional fields"""
        request = JDGenerateRequest(
            job_title="Developer",
            experience_level="",
            location=""
        )
        context = build_base_context(request)
        assert "Job Title: Developer" in context
        assert "Experience Level:" not in context
        assert "Location:" not in context
    
    def test_build_base_context_with_company_info(self):
        """Test building context includes about_company"""
        request = JDGenerateRequest(
            job_title="Developer",
            about_company="TechCorp is a great place to work"
        )
        context = build_base_context(request)
        assert "About the Company: TechCorp is a great place to work" in context
    
    def test_build_base_context_with_perks(self):
        """Test building context includes perks_and_benefits"""
        request = JDGenerateRequest(
            job_title="Developer",
            perks_and_benefits="Health insurance, remote work"
        )
        context = build_base_context(request)
        assert "Perks and Benefits: Health insurance, remote work" in context
    
    def test_build_base_context_without_company_info(self):
        """Test building context omits about_company when not provided"""
        request = JDGenerateRequest(job_title="Developer")
        context = build_base_context(request)
        assert "About the Company:" not in context
        assert "Perks and Benefits:" not in context
