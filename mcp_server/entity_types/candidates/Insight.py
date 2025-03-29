"""Insight entity type for Graphiti MCP Server."""

from typing import List, Optional
# Remove datetime import since we'll use string representation instead
# from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class InsightType(str, Enum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CULTURAL = "cultural"
    COMMUNICATION = "communication"
    MOTIVATION = "motivation"
    LEADERSHIP = "leadership"
    GROWTH = "growth"
    OTHER = "other"

class InsightSource(str, Enum):
    INTERVIEW = "interview"
    RESUME_ANALYSIS = "resume_analysis"
    PORTFOLIO_REVIEW = "portfolio_review"
    REFERENCE_CHECK = "reference_check"
    SKILL_ASSESSMENT = "skill_assessment"
    CONVERSATION = "conversation"
    OTHER = "other"

class Insight(BaseModel):
    """
    ## AI Persona
    You are a perceptive talent evaluator who identifies unique insights about candidates beyond what's explicitly stated in their resume or profile.
    
    ## Task Definition
    Extract or document meaningful insights about candidates that provide deeper understanding of their abilities, potential fit, strengths, or areas for development.
    
    ## Context
    This entity represents a unique insight discovered about a candidate during the recruitment process. Insights go beyond explicit resume data and capture observations, patterns, 
    or conclusions that might influence hiring decisions. These could come from interviews, conversations, resume analysis, or other interactions with the candidate.
    
    ## Instructions
    1. Identify meaningful insights that provide deeper understanding about the candidate.
    2. Categorize the insight by type (behavioral, technical, cultural, etc.).
    3. Specify the source of the insight (interview, resume analysis, conversation, etc.).
    4. Provide a clear, specific description of the insight with supporting context.
    5. Note the date when the insight was observed or identified.
    6. Assess the relevance of this insight to specific roles or positions if applicable.
    7. Record any recommendations or actions that should be taken based on this insight.
    8. If information for any field is not present, leave it as None or use the appropriate default.
    9. Do not fabricate insights; only record observations with sufficient supporting evidence.
    
    ## Output Format
    An Insight entity with description, type, source, and other available attributes populated based on the information observed.
    """
    
    candidate_name: str = Field(
        ...,
        description="The name of the candidate this insight is about."
    )
    
    description: str = Field(
        ...,
        description="A clear, specific description of the insight discovered about the candidate."
    )
    
    insight_type: InsightType = Field(
        ...,
        description="The category or type of insight (behavioral, technical, cultural, communication, motivation, leadership, growth, other)."
    )
    
    source: InsightSource = Field(
        ...,
        description="The source or context where this insight was observed or identified."
    )
    
    date_observed: Optional[str] = Field(
        None, 
        description="The date when this insight was observed or identified (format: YYYY-MM-DD)."
    )
    
    supporting_evidence: Optional[str] = Field(
        None, 
        description="Specific examples, quotes, or observations that support this insight."
    )
    
    relevance_to_roles: Optional[List[str]] = Field(
        None, 
        description="Specific roles or positions for which this insight is particularly relevant."
    )
    
    recommendations: Optional[str] = Field(
        None, 
        description="Any recommendations or actions that should be taken based on this insight."
    )
    
    confidence_level: Optional[int] = Field(
        None, 
        description="Subjective confidence in this insight on a scale of 1-5, with 5 being highest confidence."
    )
    
    tags: Optional[List[str]] = Field(
        None, 
        description="Keywords or tags that can be used to categorize or search for this insight."
    )

# No need for explicit registration - will be auto-registered 