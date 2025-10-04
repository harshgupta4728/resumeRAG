from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Job, User
from ..schemas.schemas import JobCreate, JobResponse, MatchRequest, MatchResponse, MatchResult
from ..services.resume_service import resume_service
from .auth import get_current_user

router = APIRouter()


@router.post("/jobs", response_model=JobResponse)
def create_job(
    job: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job description."""
    # Generate embedding for job description
    embedding = resume_service.generate_embedding(job.description_text)
    
    db_job = Job(
        title=job.title,
        description_text=job.description_text,
        embedding=embedding
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific job description."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("/jobs/{job_id}/match", response_model=MatchResponse)
def match_candidates(
    job_id: int,
    match_request: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Match candidates to a job."""
    try:
        matches, missing_requirements = resume_service.match_candidates(
            job_id, 
            match_request.top_n, 
            db
        )
        
        # Convert matches to MatchResult objects
        match_results = []
        for match in matches:
            match_result = MatchResult(
                resume_id=match["resume_id"],
                filename=match["filename"],
                similarity_score=match["similarity_score"],
                evidence=match["evidence"],
                missing_requirements=missing_requirements
            )
            match_results.append(match_result)
        
        return MatchResponse(
            job_id=job_id,
            matches=match_results
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
