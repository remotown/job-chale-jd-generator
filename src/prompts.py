from src.models import JDGenerateRequest

SYSTEM_PROMPT_TEMPLATE = """You are an employer branding copywriter generating job-facing materials for a {experience_level} {job_title} role.

Brand voice: {voice_guide}
Length: Standard platform length

Voice application rule:
  Apply brand voice to: hooks, transitions, CTAs, and descriptive language.
  Do NOT let voice override: factual accuracy, structural completeness, or professional clarity.
  Formal sections (About Us, Requirements, Education) maintain professional structure;
    apply voice as tone only, never as a format disruption.
  The General JD format always uses ALL CAPS section headers and bullet lists, regardless of voice.

Before you write, make one conscious decision:
"Given this brand voice and this platform, what is the single tonal choice that will make
this version feel native to where a candidate actually reads it?"

GROUNDING RULES:
- Only include information explicitly provided in the input data
- Never invent, infer, or assume contact details, deadlines, or application instructions
- If a field is not provided in the input, omit that section entirely
- Do not generate placeholder text for missing information
"""

ROLE_OVERVIEW_INSTRUCTION = """ROLE OVERVIEW INSTRUCTION:
Write a narrative role overview for this position.
  Length: 3 to 4 sentences, strictly 60 to 100 words
  Do NOT start with "We are looking for" or "We are hiring"
  Do NOT open with a company introduction sentence
  Capture the essence of the role in narrative form
  Apply the brand voice ({voice_guide}) to make this feel authentic
"""

GENERAL_JD_PROMPT = """Write a clean, professional job description with ALL CAPS section headers:
ROLE OVERVIEW | KEY RESPONSIBILITIES | REQUIREMENTS | WHAT WE OFFER

Structure rules:
  Use bullet points for KEY RESPONSIBILITIES and REQUIREMENTS.
  REQUIREMENTS: factual only — experience level, must-have technical skills, prerequisites.
    Do NOT include attitude, personality, or culture-fit language in REQUIREMENTS.

{role_overview_instruction}

Tonality: {voice_guide}

{base_context}
"""

LINKEDIN_PROMPT = """LinkedIn job post.

Use this EXACT format structure:

Role Title: [Job Title]
Work Model: [Work Location Type]
[IMPORTANT NOTE if applicable]

ROLE OVERVIEW
[Role overview paragraph - 2-3 sentences describing the role's purpose]

KEY RESPONSIBILITIES
- [Responsibility 1]
- [Responsibility 2]
- [Continue with responsibilities based on inputs]

WHAT WE ARE LOOKING FOR
- [Requirement 1]
- [Requirement 2]
- [Continue with requirements based on inputs]

WHAT YOU WILL GAIN
- [Benefit / Salary / Details if provided]

Rules:
  Use bullet points (-) for all lists
  Keep section headers in ALL CAPS as shown
  Apply brand voice to the descriptive content while maintaining this structure

{role_overview_instruction}

Tonality: {voice_guide}

{base_context}
"""

WHATSAPP_PROMPT = """WhatsApp job post.

Reading context: A WhatsApp group or broadcast. The reader is on their phone, likely distracted.
They will read the first emoji and first line, then decide in 2 seconds whether to keep reading.

STRICT FORMATTING RULES — these override all other instructions:
  Line 1 must be exactly: 📌 [Job Title]
  After the 📌 line: write ZERO intro text. No welcome message.
    Go directly to the first emoji section with no gap paragraph.
  Use emojis ONLY as section markers — in this order:
    🎯 What you'll do
    ✅ What you need
    💰 Salary — include ONLY if salary is explicitly provided; OMIT entire section if not provided
    📍 Location — use the work location value exactly; do not infer or add a city name
  Every single bullet: one line maximum. No exceptions.
  Do NOT repeat content between sections.

GROUNDING RULES:
- Never invent or infer deadlines or contact details
- If not provided in input, omit those sections entirely

Tonality: {voice_guide}
Length override: WhatsApp posts must be scannable in under 60 seconds. Brevity takes precedence.

{base_context}
"""

FACEBOOK_PROMPT = """Facebook job post.

Use this EXACT format structure:

📢 WE'RE HIRING! [Job Title]
🌍 [Work Location] | 🎓 [Experience level]

The Role 💼
[Role overview paragraph - 2-3 sentences]

What You'll Do:
✅ [Responsibility 1]
✅ [Responsibility 2]
✅ [Continue with responsibilities]

What We're Looking For:
🔹 [Requirement 1]
🔹 [Requirement 2]
🔹 [Continue with requirements]

Tag someone who'd be perfect for this! 👇

Rules:
  Use emojis as section headers exactly as shown
  Keep bullet points with ✅ for responsibilities, 🔹 for requirements
  Short paragraphs: 2 to 3 sentences maximum per block
  End with engagement CTA (tag someone) — match brand voice
  Apply brand voice to the descriptive content while maintaining this structure

{role_overview_instruction}

GROUNDING RULES:
- Never invent or infer deadlines or contact details
- If not provided in input, omit those sections entirely

Tonality: {voice_guide}

{base_context}
"""


def get_salary_display(request: JDGenerateRequest) -> str:
    currency_str = f" {request.currency}" if request.currency else ""
    if request.salary_min or request.salary_max:
        s_min = str(request.salary_min) if request.salary_min is not None else ""
        s_max = str(request.salary_max) if request.salary_max is not None else ""
        if s_min and s_max:
            return f"{s_min} - {s_max}{currency_str}"
        elif s_min:
            return f"From {s_min}{currency_str}"
        elif s_max:
            return f"Up to {s_max}{currency_str}"
    
    if request.salary:
        return f"{request.salary}{currency_str}"
    return ""


def build_base_context(request: JDGenerateRequest) -> str:
    parts = []
    parts.append(f"Job Title: {request.job_title}")
    if request.experience_level:
        parts.append(f"Experience Level: {request.experience_level}")
    if request.employment_type:
        parts.append(f"Employment Type: {request.employment_type}")
    if request.location:
        parts.append(f"Location: {request.location}")
    
    salary_str = get_salary_display(request)
    if salary_str:
        parts.append(f"Salary: {salary_str}")

    if request.rough_idea:
        parts.append(f"Role Outline / Rough Details: {request.rough_idea}")
    return "\n".join(parts)


def build_prompts(request: JDGenerateRequest, target_format: str) -> tuple[str, str]:
    exp_level = request.experience_level if request.experience_level else "mid-level"
    voice = request.tone if request.tone else "professional"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        experience_level=exp_level,
        job_title=request.job_title,
        voice_guide=voice
    )

    base_context = build_base_context(request)
    role_overview_instruction = ROLE_OVERVIEW_INSTRUCTION.format(voice_guide=voice)
    fmt = target_format.lower()

    if fmt == "linkedin":
        user_prompt = LINKEDIN_PROMPT.format(
            voice_guide=voice, 
            base_context=base_context,
            role_overview_instruction=role_overview_instruction
        )
    elif fmt == "whatsapp":
        user_prompt = WHATSAPP_PROMPT.format(
            voice_guide=voice, 
            base_context=base_context
        )
    elif fmt == "facebook":
        user_prompt = FACEBOOK_PROMPT.format(
            voice_guide=voice, 
            base_context=base_context,
            role_overview_instruction=role_overview_instruction
        )
    else:  # default to general JD
        user_prompt = GENERAL_JD_PROMPT.format(
            voice_guide=voice, 
            base_context=base_context,
            role_overview_instruction=role_overview_instruction
        )

    return system_prompt, user_prompt
