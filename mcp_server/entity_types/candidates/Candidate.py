"""Candidate entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field

class Candidate(BaseModel):
    """
    ## AI Persona
    You are a knowledgeable recruitment specialist who extracts candidate profile information from text.
    
    ## Task Definition
    Extract core information about a candidate from the provided text, including their name, 
    contact details, current position, location, and a high-level summary of their background.
    
    ## Context
    This entity represents a job candidate in the recruitment process. It captures the essential 
    identifying and contact information for a person applying for jobs or being considered for 
    positions. This information is typically found in resumes, LinkedIn profiles, or candidate 
    databases.
    
    ## Instructions
    1. Extract the candidate's full name as it appears in the text.
    2. Identify all contact information (email, phone, LinkedIn URL).
    3. Extract their current role/title and company if available.
    4. Note their current location (city, state, country).
    5. Capture years of experience if explicitly mentioned.
    6. Create a brief summary of their professional background.
    7. If information for any field is not present, leave it as None.
    8. Do not fabricate or infer information that is not stated or strongly implied in the text.
    
    ## Output Format
    A Candidate entity with the extracted fields populated according to the information available.
    """
    
    name: str = Field(
        ...,
        description="The candidate's full name (first and last name, and middle name if available)."
    )
    
    email: Optional[str] = Field(
        None, 
        description="The candidate's email address for contact purposes."
    )
    
    phone: Optional[str] = Field(
        None, 
        description="The candidate's phone number for contact purposes."
    )
    
    linkedin_url: Optional[str] = Field(
        None, 
        description="URL to the candidate's LinkedIn profile."
    )
    
    current_title: Optional[str] = Field(
        None, 
        description="The candidate's current job title or position."
    )
    
    current_company: Optional[str] = Field(
        None, 
        description="The company where the candidate is currently employed."
    )
    
    location: Optional[str] = Field(
        None, 
        description="The candidate's current location, typically city and state/country."
    )
    
    years_of_experience: Optional[int] = Field(
        None, 
        description="Total years of professional experience the candidate has, if explicitly stated."
    )
    
    headline: Optional[str] = Field(
        None, 
        description="A short professional headline or title the candidate uses to describe themselves."
    )
    
    summary: Optional[str] = Field(
        None, 
        description="A brief summary of the candidate's background, expertise, and key qualifications."
    ) 

# No need for explicit registration - will be auto-registered 