from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resumes = relationship("Resume", back_populates="owner")


class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_text = Column(Text, nullable=False)
    pii_redacted_content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)  # 384 dimensions for all-MiniLM-L6-v2
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="resumes")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)  # 384 dimensions for all-MiniLM-L6-v2
    created_at = Column(DateTime, default=datetime.utcnow)
