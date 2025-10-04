import pytest
from unittest.mock import patch, MagicMock
from app.services.resume_service import ResumeProcessingService


class TestResumeProcessingService:
    def setup_method(self):
        self.service = ResumeProcessingService()

    def test_redact_pii_with_spacy(self):
        """Test PII redaction with spaCy model."""
        text = "John Doe's email is john.doe@example.com and phone is 555-123-4567"
        result = self.service.redact_pii(text)
        
        # Should redact email and phone
        assert "[REDACTED]" in result
        assert "john.doe@example.com" not in result
        assert "555-123-4567" not in result

    def test_redact_pii_fallback(self):
        """Test PII redaction fallback when spaCy is not available."""
        with patch.object(self.service, 'nlp', None):
            text = "Contact John Smith at john@example.com or call 555-123-4567"
            result = self.service.redact_pii(text)
            
            # Should still redact using regex fallback
            assert "[REDACTED]" in result
            assert "john@example.com" not in result
            assert "555-123-4567" not in result

    def test_generate_embedding(self):
        """Test embedding generation."""
        text = "This is a test resume with Python and FastAPI experience"
        embedding = self.service.generate_embedding(text)
        
        # Should return a list of floats
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_extract_requirements(self):
        """Test requirement extraction from job description."""
        job_desc = """
        We are looking for a Python developer.
        Required skills:
        - Python 3.8+
        - FastAPI experience
        - PostgreSQL knowledge
        - Docker experience
        
        Nice to have:
        - Machine learning background
        - React frontend skills
        """
        
        requirements = self.service._extract_requirements(job_desc)
        
        # Should extract multiple requirements
        assert len(requirements) > 0
        assert any("Python" in req for req in requirements)
        assert any("FastAPI" in req for req in requirements)

    def test_extract_evidence(self):
        """Test evidence extraction from resume content."""
        resume_content = "I have 5 years of Python experience and worked with FastAPI for 2 years."
        job_description = "Looking for Python developer with FastAPI experience"
        
        evidence = self.service._extract_evidence(resume_content, job_description)
        
        # Should extract relevant sentences
        assert "Python" in evidence
        assert "FastAPI" in evidence

    @patch('app.services.resume_service.io.BytesIO')
    @patch('app.services.resume_service.pypdf.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader, mock_bytes_io):
        """Test PDF text extraction."""
        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        file_content = b"fake pdf content"
        result = self.service.extract_text_from_pdf(file_content)
        
        assert result == "Sample resume text"

    @patch('app.services.resume_service.io.BytesIO')
    @patch('app.services.resume_service.Document')
    def test_extract_text_from_docx(self, mock_document, mock_bytes_io):
        """Test DOCX text extraction."""
        # Mock document
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Sample resume text"
        mock_document.return_value.paragraphs = [mock_paragraph]
        
        file_content = b"fake docx content"
        result = self.service.extract_text_from_docx(file_content)
        
        assert result == "Sample resume text"

    def test_extract_text_from_file_unsupported(self):
        """Test error handling for unsupported file types."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            self.service.extract_text_from_file("test.txt", b"content")
