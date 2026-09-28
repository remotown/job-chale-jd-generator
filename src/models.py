from typing import Optional, Union, List, Dict
from pydantic import BaseModel, Field

class JDGenerateRequest(BaseModel):
    job_title: str = Field(..., description="Job Title for the role")
    rough_idea: Optional[str] = Field(default="", description="Rough outline or notes for the role")
    employment_type: Optional[str] = Field(default="", description="Full-time, Part-time, Contract, etc.")
    experience_level: Optional[str] = Field(default="", description="Entry level, Mid level, Senior, Executive, etc.")
    location: Optional[str] = Field(default="", description="City, Country, Remote, Hybrid, etc.")
    salary_min: Optional[Union[str, int, float]] = Field(default="", description="Minimum salary")
    salary_max: Optional[Union[str, int, float]] = Field(default="", description="Maximum salary")
    salary: Optional[Union[str, int, float]] = Field(default="", description="Single salary figure or range")
    currency: Optional[str] = Field(default="", description="Currency code (USD, GHS, NGN, etc.)")
    tone: Optional[str] = Field(default="professional", description="Desired brand voice or tone")
    format: Optional[Union[str, List[str]]] = Field(
        default=["general"], 
        description="Target platform format or list of formats: general, linkedin, whatsapp, facebook"
    )

    @property
    def format_list(self) -> List[str]:
        if isinstance(self.format, str):
            return [self.format]
        if isinstance(self.format, list):
            return self.format
        return ["general"]

class JDGenerateResponse(BaseModel):
    job_title: str
    formats: Dict[str, str]
