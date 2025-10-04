from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import zipfile
import io
from ..database import get_db
from ..models.models import Resume, User
from ..schemas.schemas import ResumeResponse, ResumeSearchResponse, AskQuery, AskResponse
from ..services.resume_service import resume_service
from .auth import get_current_user

router = APIRouter()


@router.post("/resumes", response_model=List[ResumeResponse])
def upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload one or more resume files."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    processed_resumes = []
    
    for file in files:
        if not file.filename:
            continue
            
        # Read file content
        file_content = file.file.read()
        
        try:
            if file.filename.lower().endswith('.zip'):
                # Process ZIP file
                zip_results = resume_service.process_zip_file(file_content)
                for filename, content_text, pii_redacted_content, embedding in zip_results:
                    resume = Resume(
                        filename=filename,
                        content_text=content_text,
                        pii_redacted_content=pii_redacted_content,
                        embedding=embedding,
                        owner_id=current_user.id
                    )
                    db.add(resume)
                    processed_resumes.append(resume)
            else:
                # Process single file
                content_text, pii_redacted_content, embedding = resume_service.process_resume_file(
                    file.filename, file_content
                )
                resume = Resume(
                    filename=file.filename,
                    content_text=content_text,
                    pii_redacted_content=pii_redacted_content,
                    embedding=embedding,
                    owner_id=current_user.id
                )
                db.add(resume)
                processed_resumes.append(resume)
                
        except Exception as e:
            # Skip files that can't be processed
            continue
    
    db.commit()
    
    # Refresh all resumes to get their IDs
    for resume in processed_resumes:
        db.refresh(resume)
    
    return processed_resumes


@router.get("/resumes", response_model=List[ResumeSearchResponse])
def get_resumes(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resumes with optional search."""
    query = db.query(Resume)
    
    if q:
        # Simple text search in redacted content
        query = query.filter(Resume.pii_redacted_content.ilike(f"%{q}%"))
    
    resumes = query.offset(offset).limit(limit).all()
    return resumes


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Apply RBAC: only recruiters can see unredacted content
    if current_user.role.value != "recruiter":
        # Return redacted version for non-recruiters
        resume.content_text = resume.pii_redacted_content
    
    return resume


@router.post("/ask", response_model=AskResponse)
def ask_question(
    query_data: AskQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question and get relevant resume snippets."""
    results = resume_service.search_similar_resumes(
        query_data.query, 
        query_data.k, 
        db
    )
    
    return AskResponse(results=results)
