"""
Resume Parser Module
Extracts structured information from PDF, DOCX, and TXT resumes.
Includes text normalization, PII redaction for privacy, and robust error handling.
"""
import os
import json
import re
from typing import Dict, Any, List, Optional
from app.models import Resume, ResumeExtraction
from app.extensions import db
from app.services.skill_extractor import SkillExtractor


class ResumeParser:
    """Parse resumes and extract structured information with privacy protection and error guards."""

    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

    def __init__(self):
        self.skill_extractor = SkillExtractor()

    def parse_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """
        Parse a resume file and extract structured information.

        Args:
            resume_id: ID of the resume record

        Returns:
            dict: Extracted information
        """
        resume = db.session.get(Resume, resume_id)
        if not resume:
            return None

        if resume.source_type == 'url':
            raise ValueError('A resume URL is saved, but its document must be uploaded to analyze it.')

        if not resume.file_path or not os.path.exists(resume.file_path):
            raise ValueError('Resume file was not found on the server. Please re-upload your resume.')

        # Validate file size
        file_size = os.path.getsize(resume.file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f'File size ({file_size / (1024*1024):.1f}MB) exceeds the maximum allowed 16MB.')

        extension = os.path.splitext(resume.filename or resume.file_path)[1].lower()
        if extension == '.pdf':
            text = self._extract_pdf_text(resume.file_path)
        elif extension == '.docx':
            text = self._extract_docx_text(resume.file_path)
        elif extension == '.txt':
            text = self._extract_txt_text(resume.file_path)
        else:
            raise ValueError('Unsupported resume format. Upload a PDF, DOCX, or TXT file.')

        return self._save_extraction(resume, text)

    def parse_text(self, resume_id: int, text: str) -> Dict[str, Any]:
        """Analyze resume text directly submitted by the user."""
        resume = db.session.get(Resume, resume_id)
        if not resume:
            raise ValueError('Resume record was not found.')
        if not text or not text.strip():
            raise ValueError('Resume text cannot be empty.')
        return self._save_extraction(resume, text)

    def normalize_text(self, text: str) -> str:
        """Clean and normalize extracted resume text."""
        if not text:
            return ""
        # Remove null bytes and non-printable control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Clean horizontal whitespace around newlines
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r' ?\n ?', '\n', text)
        # Collapse multiple empty lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def redact_pii(self, text: str) -> str:
        """
        Redact sensitive personal identifiers (phone numbers, emails) from stored text
        to prevent accidental privacy leaks in audit logs and snapshots.
        """
        if not text:
            return ""
        # Redact email addresses
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        text = re.sub(email_pattern, '[EMAIL_REDACTED]', text)
        # Redact phone numbers (10+ digits, common international formats)
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
        text = re.sub(phone_pattern, '[PHONE_REDACTED]', text)
        return text

    def _save_extraction(self, resume: Resume, raw_text: str) -> Dict[str, Any]:
        normalized = self.normalize_text(raw_text)
        if not normalized:
            raise ValueError('No readable text was found in this resume.')

        # Extract structured information
        extracted = {
            'skills': self._extract_skills(normalized),
            'education': self._extract_education(normalized),
            'projects': self._extract_projects(normalized),
            'certifications': self._extract_certifications(normalized),
            'experience': self._extract_experience(normalized)
        }

        # Privacy-conscious text storage: redact sensitive PII before saving to DB
        safe_stored_text = self.redact_pii(normalized)

        # Save extraction
        extraction = ResumeExtraction.query.filter_by(resume_id=resume.id).first()
        if extraction is None:
            extraction = ResumeExtraction(resume_id=resume.id)
            db.session.add(extraction)

        extraction.raw_text = safe_stored_text
        extraction.extracted_skills = json.dumps(extracted['skills'])
        extraction.extracted_education = json.dumps(extracted['education'])
        extraction.extracted_projects = json.dumps(extracted['projects'])
        extraction.extracted_certifications = json.dumps(extracted['certifications'])
        extraction.extracted_experience = json.dumps(extracted['experience'])
        resume.is_processed = True
        db.session.commit()

        return extracted

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF (fitz) with error handling."""
        import fitz
        try:
            with fitz.open(file_path) as doc:
                if len(doc) == 0:
                    raise ValueError('The uploaded PDF has no pages.')
                text = ''.join(page.get_text() for page in doc)
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f'Unable to parse PDF file: {str(e)}')

        if not text.strip():
            raise ValueError('No selectable text was found in this PDF. Upload a text-based PDF or paste the resume text.')
        return text

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx with error handling."""
        from docx import Document
        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text:
                            paragraphs.append(cell.text)
            text = '\n'.join(paragraphs)
        except Exception as e:
            raise ValueError(f'Unable to parse DOCX document: {str(e)}')

        if not text.strip():
            raise ValueError('No text was found in this DOCX file.')
        return text

    def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT with multiple encoding fallbacks."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        text = None
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    text = f.read()
                break
            except (UnicodeDecodeError, OSError):
                continue
        if text is None:
            raise ValueError('Unable to read text file. Please check file encoding.')
        if not text.strip():
            raise ValueError('Text file is empty.')
        return text

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills using SkillExtractor taxonomy."""
        return self.skill_extractor.extract_skills(text)

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education details using pattern matching."""
        education = []
        degree_patterns = [
            (r'\bb\.?\s?tech\b', 'B.Tech'),
            (r'\bb\.?\s?e\.?\b', 'B.E.'),
            (r'\bb\.?\s?sc\b', 'B.Sc'),
            (r'\bb\.?\s?com\b', 'B.Com'),
            (r'\bb\.?\s?a\.?\b', 'B.A.'),
            (r'\bm\.?\s?tech\b', 'M.Tech'),
            (r'\bm\.?\s?e\.?\b', 'M.E.'),
            (r'\bm\.?\s?sc\b', 'M.Sc'),
            (r'\bmba\b', 'MBA'),
            (r'\bmca\b', 'MCA'),
            (r'\bph\.?d\b', 'PhD')
        ]
        text_lower = text.lower()
        for regex, name in degree_patterns:
            if re.search(regex, text_lower):
                education.append({
                    'qualification': name,
                    'institution': 'Identified from resume',
                    'year': None
                })
        return education

    def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract project highlights."""
        projects = []
        project_keywords = ['project', 'developed', 'built', 'created', 'implemented', 'designed']
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in project_keywords):
            projects.append({
                'name': 'Project Section Detected',
                'description': 'Relevant technical project details found in resume'
            })
        return projects

    def _extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract certifications."""
        certifications = []
        cert_keywords = ['certified', 'certificate', 'certification', 'license']
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in cert_keywords):
            certifications.append({
                'name': 'Certification Detected',
                'issuer': 'Identified from resume'
            })
        return certifications

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work or internship experience."""
        experience = []
        exp_keywords = ['experience', 'worked at', 'employed', 'intern', 'internship', 'trainee']
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in exp_keywords):
            experience.append({
                'company': 'Experience Detected',
                'role': 'Role identified in resume',
                'duration': 'N/A'
            })
        return experience
