"""WorkExperience entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field

class WorkExperience(BaseModel):
    """
    ## AI Persona
    You are a career history analyst who specializes in extracting work experience details.
    
    ## Task Definition
    Extract comprehensive information about a candidate's work experience from the provided text, 
    including job details, responsibilities, achievements, and technologies used.
    
    ## Context
    This entity represents a single job position or role held by a candidate. Each work experience
    should be captured as a separate entity. This information is typically found in the "Work Experience"
    or "Professional Experience" sections of resumes, CVs, or professional profiles.
    
    ## Instructions
    1. Extract the job title or position held by the candidate.
    2. Identify the name of the company or organization where they worked.
    3. Determine the start and end dates of employment (current position may not have an end date).
    4. Note the location where they worked (city, state, country).
    5. Capture key responsibilities and duties performed in the role.
    6. Extract notable achievements, projects, or accomplishments.
    7. Identify technologies, tools, or methodologies used, if mentioned.
    8. Note any promotions or role changes within the same company, if applicable.
    9. If information for any field is not present, leave it as None.
    10. Create a separate WorkExperience entity for each position mentioned.
    
    ## Output Format
    A WorkExperience entity with all available fields populated based on the information in the text.
    """
    
    job_title: str = Field(
        ...,
        description="The title or position held by the candidate."
    )
    
    company_name: str = Field(
        ...,
        description="The name of the company or organization where the candidate worked."
    )
    
    start_date: Optional[str] = Field(
        None, 
        description="When the candidate started this role (e.g., 'Jan 2020', 'March 2018', '2015')."
    )
    
    end_date: Optional[str] = Field(
        None, 
        description="When the candidate ended this role (e.g., 'Present', 'Current', 'Dec 2022')."
    )
    
    is_current: Optional[bool] = Field(
        None, 
        description="Whether this is the candidate's current position."
    )
    
    location: Optional[str] = Field(
        None, 
        description="Where the job was located (city, state, country)."
    )
    
    responsibilities: Optional[List[str]] = Field(
        None, 
        description="Key responsibilities, duties, or tasks performed in this role."
    )
    
    achievements: Optional[List[str]] = Field(
        None, 
        description="Notable achievements, accomplishments, or successful projects in this role."
    )
    
    technologies_used: Optional[List[str]] = Field(
        None, 
        description="Technologies, tools, frameworks, languages, or methodologies used in this role."
    )
    
    description: Optional[str] = Field(
        None, 
        description="A general description or summary of the role as provided in the source text."
    )
    
    summary: str = Field(
        default="Work experience at a company",
        description="A brief summary of this work experience for entity node representation."
    )

# No need for explicit registration - will be auto-registered 