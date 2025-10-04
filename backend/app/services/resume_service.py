import io
import zipfile
from typing import List, Tuple, Optional
import pypdf
from docx import Document
import spacy
from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.models import Resume, Job
import re


class ResumeProcessingService:
    def __init__(self):
        # Load spaCy model for PII detection
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model not found
            self.nlp = None
        
        # Load sentence transformer model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")
    
    def extract_text_from_file(self, filename: str, file_content: bytes) -> str:
        """Extract text from file based on extension."""
        if filename.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_content)
        elif filename.lower().endswith('.docx'):
            return self.extract_text_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text using spaCy."""
        if not self.nlp:
            # Simple regex fallback if spaCy model not available
            # Redact email addresses
            text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', text)
            # Redact phone numbers
            text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED]', text)
            # Redact names (simple pattern)
            text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[REDACTED]', text)
            return text
        
        doc = self.nlp(text)
        redacted_text = text
        
        # Redact names, emails, and phone numbers
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "EMAIL", "PHONE"]:
                redacted_text = redacted_text.replace(ent.text, "[REDACTED]")
        
        # Additional regex patterns for better coverage
        redacted_text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', redacted_text)
        redacted_text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED]', redacted_text)
        
        return redacted_text
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence transformers."""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def process_resume_file(self, filename: str, file_content: bytes) -> Tuple[str, str, List[float]]:
        """Process a resume file and return content, redacted content, and embedding."""
        # Extract text
        content_text = self.extract_text_from_file(filename, file_content)
        
        # Redact PII
        pii_redacted_content = self.redact_pii(content_text)
        
        # Generate embedding
        embedding = self.generate_embedding(pii_redacted_content)
        
        return content_text, pii_redacted_content, embedding
    
    def process_zip_file(self, zip_content: bytes) -> List[Tuple[str, str, str, List[float]]]:
        """Process a ZIP file containing multiple resumes."""
        results = []
        
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            for filename in zip_file.namelist():
                if filename.lower().endswith(('.pdf', '.docx')):
                    try:
                        file_content = zip_file.read(filename)
                        content_text, pii_redacted_content, embedding = self.process_resume_file(
                            filename, file_content
                        )
                        results.append((filename, content_text, pii_redacted_content, embedding))
                    except Exception as e:
                        # Skip files that can't be processed
                        continue
        
        return results
    
    def search_similar_resumes(self, query: str, k: int, db: Session) -> List[dict]:
        """Search for similar resumes using vector similarity."""
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        
        # Perform vector similarity search
        query_sql = text("""
            SELECT id, filename, pii_redacted_content, 
                   (embedding <=> :query_embedding) as distance
            FROM resumes 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :k
        """)
        
        result = db.execute(
            query_sql,
            {
                "query_embedding": str(query_embedding),
                "k": k
            }
        ).fetchall()
        
        results = []
        for row in result:
            results.append({
                "resume_id": row.id,
                "filename": row.filename,
                "content": row.pii_redacted_content,
                "similarity_score": 1 - row.distance  # Convert distance to similarity
            })
        
        return results
    
    def match_candidates(self, job_id: int, top_n: int, db: Session) -> Tuple[List[dict], List[str]]:
        """Match candidates to a job using vector similarity."""
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")
        
        if not job.embedding:
            raise ValueError("Job has no embedding")
        
        # Perform vector similarity search
        query_sql = text("""
            SELECT r.id, r.filename, r.pii_redacted_content,
                   (r.embedding <=> :job_embedding) as distance
            FROM resumes r
            WHERE r.embedding IS NOT NULL
            ORDER BY r.embedding <=> :job_embedding
            LIMIT :top_n
        """)
        
        result = db.execute(
            query_sql,
            {
                "job_embedding": str(job.embedding),
                "top_n": top_n
            }
        ).fetchall()
        
        matches = []
        for row in result:
            similarity_score = 1 - row.distance
            evidence = self._extract_evidence(row.pii_redacted_content, job.description_text)
            
            matches.append({
                "resume_id": row.id,
                "filename": row.filename,
                "similarity_score": similarity_score,
                "evidence": evidence
            })
        
        # Analyze missing requirements
        missing_requirements = self._analyze_missing_requirements(
            job.description_text, [match["evidence"] for match in matches]
        )
        
        return matches, missing_requirements
    
    def _extract_evidence(self, resume_content: str, job_description: str) -> str:
        """Extract relevant evidence from resume that matches job requirements."""
        # Simple keyword matching for evidence extraction
        job_keywords = set(job_description.lower().split())
        resume_sentences = resume_content.split('.')
        
        evidence_sentences = []
        for sentence in resume_sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in job_keywords if len(keyword) > 3):
                evidence_sentences.append(sentence.strip())
        
        return '. '.join(evidence_sentences[:3])  # Return top 3 evidence sentences
    
    def _analyze_missing_requirements(self, job_description: str, evidence_texts: List[str]) -> List[str]:
        """Analyze what requirements are missing from the matched candidates."""
        # Extract key requirements from job description
        job_requirements = self._extract_requirements(job_description)
        
        # Combine all evidence texts
        combined_evidence = ' '.join(evidence_texts).lower()
        
        missing_requirements = []
        for requirement in job_requirements:
            if not any(keyword in combined_evidence for keyword in requirement.lower().split()):
                missing_requirements.append(requirement)
        
        return missing_requirements[:5]  # Return top 5 missing requirements
    
    def _extract_requirements(self, job_description: str) -> List[str]:
        """Extract key requirements from job description."""
        # Simple extraction of requirements (can be enhanced with NLP)
        lines = job_description.split('\n')
        requirements = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['required', 'must have', 'should have', 'experience', 'skills']):
                if len(line) > 10:  # Filter out very short lines
                    requirements.append(line)
        
        return requirements


# Global instance
resume_service = ResumeProcessingService()
