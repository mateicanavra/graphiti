"""Education entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class DegreeLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"
    OTHER = "other"

class Education(BaseModel):
    """
    ## AI Persona
    You are an educational background analyst who specializes in academic credential verification.
    
    ## Task Definition
    Extract and organize information about a candidate's educational background, including institutions attended, 
    degrees earned, areas of study, and relevant academic achievements.
    
    ## Context
    This entity represents a single educational qualification or program completed by a candidate. Each degree, 
    certificate, or formal educational program should be captured as a separate Education entity. These entries 
    typically appear in the "Education" section of resumes, CVs, or professional profiles.
    
    ## Instructions
    1. Extract the name of the educational institution (university, college, school).
    2. Identify the degree level and type (Bachelor's, Master's, PhD, Certificate, etc.).
    3. Determine the field of study, major, or specialization.
    4. Extract the start and completion dates (year is typically sufficient).
    5. Note any academic achievements mentioned (GPA, honors, class rank, etc.).
    6. Capture relevant coursework if it's highlighted and relevant to the candidate's career goals.
    7. Record any notable projects, thesis topics, or research work if mentioned.
    8. If information for any field is not present, leave it as None.
    9. Create a separate Education entity for each degree or educational program mentioned.
    
    ## Output Format
    An Education entity with all available fields populated based on the information in the text.
    """
    
    institution: str = Field(
        ...,
        description="The name of the educational institution (university, college, school)."
    )
    
    degree_level: DegreeLevel = Field(
        ...,
        description="The level of the degree or educational qualification."
    )
    
    degree_name: Optional[str] = Field(
        None, 
        description="The specific name of the degree (e.g., 'Bachelor of Science', 'Master of Business Administration')."
    )
    
    field_of_study: Optional[str] = Field(
        None, 
        description="The major, specialization, or field of study."
    )
    
    start_date: Optional[str] = Field(
        None, 
        description="When the candidate started this educational program (typically just the year)."
    )
    
    end_date: Optional[str] = Field(
        None, 
        description="When the candidate completed this educational program (or expected completion date)."
    )
    
    is_completed: Optional[bool] = Field(
        None, 
        description="Whether the education has been completed (True) or is still in progress (False)."
    )
    
    gpa: Optional[str] = Field(
        None, 
        description="The Grade Point Average or academic score achieved, if mentioned."
    )
    
    honors: Optional[List[str]] = Field(
        None, 
        description="Any academic honors, distinctions, or awards received during this education."
    )
    
    relevant_coursework: Optional[List[str]] = Field(
        None, 
        description="Specific courses highlighted as relevant to the candidate's career goals."
    )
    
    projects: Optional[List[str]] = Field(
        None, 
        description="Notable academic projects, research, or thesis work completed during this education."
    )
    
    location: Optional[str] = Field(
        None, 
        description="The location (city, state, country) of the educational institution."
    )
    
    summary: str = Field(
        default="Education at an institution",
        description="A brief summary of this education record for entity node representation."
    )

# No need for explicit registration - will be auto-registered 