from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from ..models.models import UserRole


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Resume schemas
class ResumeBase(BaseModel):
    filename: str


class ResumeCreate(ResumeBase):
    content_text: str
    pii_redacted_content: str


class ResumeResponse(ResumeBase):
    id: int
    content_text: str
    pii_redacted_content: str
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResumeSearchResponse(ResumeBase):
    id: int
    pii_redacted_content: str
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Job schemas
class JobBase(BaseModel):
    title: str
    description_text: str


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Search schemas
class AskQuery(BaseModel):
    query: str
    k: int = 3


class AskResponse(BaseModel):
    results: List[dict]


class MatchRequest(BaseModel):
    top_n: int = 5


class MatchResult(BaseModel):
    resume_id: int
    filename: str
    similarity_score: float
    evidence: str
    missing_requirements: List[str]


class MatchResponse(BaseModel):
    job_id: int
    matches: List[MatchResult]


# Error schemas
class ErrorDetail(BaseModel):
    code: str
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
