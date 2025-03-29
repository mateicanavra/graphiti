"""Certification entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field

class Certification(BaseModel):
    """
    ## AI Persona
    You are a professional certification analyst who specializes in identifying and validating industry credentials.
    
    ## Task Definition
    Extract information about professional certifications, licenses, or credentials mentioned in the text, 
    including the certification name, issuing organization, date, and validity status.
    
    ## Context
    This entity represents a professional certification, license, or credential that a candidate has earned. 
    Each certification should be captured as a separate entity. These are typically found in dedicated 
    "Certifications" or "Professional Development" sections of resumes, but may also appear in summaries 
    or alongside education details.
    
    ## Instructions
    1. Extract the full, official name of the certification or credential.
    2. Identify the organization or body that issued the certification.
    3. Determine when the certification was earned or issued.
    4. Note the expiration date or validity period if mentioned.
    5. Capture any identification numbers, versions, or specific levels of the certification.
    6. Record related skills or technologies associated with the certification if mentioned.
    7. Note if the certification is highlighted as particularly significant or relevant.
    8. If information for any field is not present, leave it as None.
    9. Create a separate Certification entity for each distinct credential mentioned.
    
    ## Output Format
    A Certification entity with all available fields populated based on the information provided in the text.
    """
    
    name: str = Field(
        ...,
        description="The full, official name of the certification or credential."
    )
    
    issuing_organization: Optional[str] = Field(
        None, 
        description="The name of the organization or body that issued the certification."
    )
    
    issue_date: Optional[str] = Field(
        None, 
        description="When the certification was earned or issued (format: YYYY-MM or YYYY)."
    )
    
    expiration_date: Optional[str] = Field(
        None, 
        description="When the certification expires, if applicable (format: YYYY-MM or YYYY)."
    )
    
    is_active: Optional[bool] = Field(
        None, 
        description="Whether the certification is currently active/valid (True) or expired (False)."
    )
    
    credential_id: Optional[str] = Field(
        None, 
        description="Any identification number, version, or specific identifier for the certification."
    )
    
    credential_url: Optional[str] = Field(
        None, 
        description="URL to verify or view the certification if mentioned."
    )
    
    related_skills: Optional[List[str]] = Field(
        None, 
        description="Skills or technologies directly associated with this certification."
    )
    
    description: Optional[str] = Field(
        None, 
        description="Any additional details or context about the certification as provided in the source text."
    )

# No need for explicit registration - will be auto-registered 