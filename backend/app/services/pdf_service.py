import PyPDF2
import pdfplumber
from typing import List, Dict, Optional
import os
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)


class PDFService:
    """
    Service for handling PDF file operations.
    Supports extraction with both PyPDF2 and pdfplumber.
    """
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True, parents=True)
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, str]:
        """
        Save uploaded PDF file and return document info.
        """
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Create safe filename
        safe_filename = self._sanitize_filename(filename)
        file_path = self.upload_dir / f"{document_id}_{safe_filename}"
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"Saved file: {file_path}")
        
        return {
            "document_id": document_id,
            "filename": safe_filename,
            "file_path": str(file_path)
        }
    
    def extract_text_pypdf2(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF using PyPDF2.
        Returns list of pages with text and page numbers.
        """
        pages_data = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip():
                        pages_data.append({
                            "page_number": page_num + 1,
                            "text": text
                        })
                
                logger.info(f"Extracted {len(pages_data)} pages from {file_path} using PyPDF2")
                return pages_data
        
        except Exception as e:
            logger.error(f"Error extracting with PyPDF2: {str(e)}")
            raise
    
    def extract_text_pdfplumber(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF using pdfplumber (more accurate for complex PDFs).
        """
        pages_data = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    
                    if text and text.strip():
                        pages_data.append({
                            "page_number": page_num + 1,
                            "text": text
                        })
                
                logger.info(f"Extracted {len(pages_data)} pages from {file_path} using pdfplumber")
                return pages_data
        
        except Exception as e:
            logger.error(f"Error extracting with pdfplumber: {str(e)}")
            raise
    
    def extract_text(self, file_path: str, method: str = "pdfplumber") -> List[Dict[str, any]]:
        """
        Extract text using specified method with fallback.
        """
        try:
            if method == "pdfplumber":
                return self.extract_text_pdfplumber(file_path)
            else:
                return self.extract_text_pypdf2(file_path)
        except Exception as e:
            logger.warning(f"Primary extraction method failed, trying fallback: {str(e)}")
            # Try alternative method
            if method == "pdfplumber":
                return self.extract_text_pypdf2(file_path)
            else:
                return self.extract_text_pdfplumber(file_path)
    
    def delete_file(self, document_id: str) -> bool:
        """
        Delete PDF file by document ID.
        """
        try:
            # Find file with document_id prefix
            for file_path in self.upload_dir.glob(f"{document_id}_*"):
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            
            logger.warning(f"No file found for document_id: {document_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    def get_file_path(self, document_id: str) -> Optional[str]:
        """
        Get file path by document ID.
        """
        for file_path in self.upload_dir.glob(f"{document_id}_*"):
            return str(file_path)
        return None
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent security issues.
        """
        # Remove path components
        filename = os.path.basename(filename)
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate that file is a proper PDF.
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                return header == b'%PDF-'
        except:
            return False