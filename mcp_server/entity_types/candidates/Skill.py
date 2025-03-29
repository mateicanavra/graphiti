"""Skill entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class SkillType(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    TOOL = "tool"
    PLATFORM = "platform"
    METHODOLOGY = "methodology"
    DOMAIN = "domain"
    OTHER = "other"

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNKNOWN = "unknown"

class Skill(BaseModel):
    """
    ## AI Persona
    You are a skills assessment specialist who identifies and categorizes professional skills from candidate information.
    
    ## Task Definition
    Extract skills mentioned in the text, categorize them by type, and assess proficiency level when possible.
    
    ## Context
    This entity represents a specific professional skill possessed by a candidate. Skills can include technical abilities 
    (programming languages, tools, platforms), soft skills (communication, leadership), language proficiencies, methodologies, 
    and domain expertise. Skills are typically listed in dedicated "Skills" sections of resumes, but may also be mentioned 
    throughout work experience descriptions, summaries, or project sections.
    
    ## Instructions
    1. Identify distinct skills mentioned in the text.
    2. Categorize each skill by its type (technical, soft, language, tool, platform, methodology, domain, other).
    3. Determine the proficiency level if explicitly stated or strongly implied.
    4. Extract any years of experience with the skill if mentioned.
    5. Note if the skill is explicitly highlighted as a core or key skill.
    6. For technical skills, identify related technologies or platforms if mentioned.
    7. Create a separate Skill entity for each distinct skill identified.
    8. Do not infer skills that aren't explicitly mentioned or strongly implied.
    9. If information for any field is not present, leave it as None or use the appropriate default.
    
    ## Output Format
    A Skill entity with name, type, and other available attributes populated based on the information in the text.
    """
    
    name: str = Field(
        ...,
        description="The name of the skill (e.g., 'Python', 'Project Management', 'Data Analysis')."
    )
    
    skill_type: SkillType = Field(
        ...,
        description="The category or type of skill (technical, soft, language, tool, platform, methodology, domain, other)."
    )
    
    level: Optional[SkillLevel] = Field(
        None, 
        description="The candidate's proficiency level with this skill if mentioned."
    )
    
    years_experience: Optional[int] = Field(
        None, 
        description="Number of years of experience with this skill, if explicitly stated."
    )
    
    is_core_skill: Optional[bool] = Field(
        None, 
        description="Whether this is highlighted as a core or key skill for the candidate."
    )
    
    related_technologies: Optional[List[str]] = Field(
        None, 
        description="For technical skills, other technologies, tools, or platforms mentioned in connection with this skill."
    )
    
    description: Optional[str] = Field(
        None, 
        description="Any additional descriptions or context about the skill as provided in the source text."
    )

# No need for explicit registration - will be auto-registered 