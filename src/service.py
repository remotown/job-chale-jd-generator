import logging
from typing import Dict
from openai import OpenAI
from src.config import settings
from src.models import JDGenerateRequest, JDGenerateResponse
from src.prompts import build_prompts, get_salary_display

logger = logging.getLogger(__name__)

def generate_job_descriptions(request: JDGenerateRequest) -> JDGenerateResponse:
    formats_output: Dict[str, str] = {}
    requested_formats = request.format_list

    for fmt in requested_formats:
        formats_output[fmt] = _generate_single_format(request, fmt)

    return JDGenerateResponse(
        job_title=request.job_title,
        formats=formats_output
    )

def _generate_single_format(request: JDGenerateRequest, target_format: str) -> str:
    system_prompt, user_prompt = build_prompts(request, target_format)

    # Mock fallback for testing or when API key is not configured
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
        logger.warning("DeepSeek API key not provided; returning mock output for testing.")
        return mock_generate_output(request, target_format)

    try:
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )

        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling LLM API for format '{target_format}': {e}")
        return f"[Error connecting to DeepSeek API: {str(e)}]\n\n" + mock_generate_output(request, target_format)


def mock_generate_output(request: JDGenerateRequest, target_format: str) -> str:
    tone_str = request.tone.lower() if request.tone else "professional"
    fmt = target_format.lower()

    if tone_str in ["casual", "playful", "friendly"]:
        tone_intro = "Hey there! We are excited to announce an awesome opening!"
    elif tone_str in ["formal", "executive", "corporate"]:
        tone_intro = "Notice of Position Availability: Applications are invited for the following role."
    else:
        tone_intro = f"Job Description for {request.job_title}"

    salary_display = get_salary_display(request)

    if fmt == "whatsapp":
        lines = [f"📌 {request.job_title}", f"🎯 What you'll do\n- {request.rough_idea or 'Execute core responsibilities'}"]
        lines.append(f"✅ What you need\n- {request.experience_level or 'Experience in the field'}")
        if salary_display:
            lines.append(f"💰 Salary\n- {salary_display}")
        lines.append(f"📍 Location\n- {request.location or 'Not specified'}")
        return "\n\n".join(lines)

    output_lines = [
        tone_intro,
        f"Role Title: {request.job_title}",
    ]
    if request.employment_type:
        output_lines.append(f"Employment Type: {request.employment_type}")
    if request.experience_level:
        output_lines.append(f"Experience Level: {request.experience_level}")
    if request.location:
        output_lines.append(f"Location: {request.location}")
    if salary_display:
        output_lines.append(f"Salary: {salary_display}")
    if request.rough_idea:
        output_lines.append(f"Overview: {request.rough_idea}")

    return "\n".join(output_lines)
