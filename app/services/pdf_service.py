"""PDF parsing service"""

import logging
from PyPDF2 import PdfReader
from io import BytesIO

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF file processing"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """
        Extract text content from PDF file
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF parsing fails
        """
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
            
            if not text_content:
                raise ValueError("No text content could be extracted from the PDF")
            
            full_text = "\n\n".join(text_content)
            logger.info(f"Successfully extracted {len(full_text)} characters from {len(pdf_reader.pages)} pages")
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise ValueError(f"Failed to parse PDF file: {str(e)}")
    
    @staticmethod
    def validate_pdf(pdf_bytes: bytes) -> bool:
        """
        Validate if the file is a valid PDF
        
        Args:
            pdf_bytes: File content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            pdf_file = BytesIO(pdf_bytes)
            PdfReader(pdf_file)
            return True
        except Exception:
            return False
