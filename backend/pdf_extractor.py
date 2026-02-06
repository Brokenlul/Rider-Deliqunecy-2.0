"""
PDF Extraction Module for Lily's Score
Handles text-based PDFs with pdfplumber and OCR fallback using pytesseract
"""

import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[str, bool, float]:
    """
    Extract text from PDF with OCR fallback.
    
    Returns:
        Tuple[str, bool, float]: (extracted_text, used_ocr, confidence_score)
    """
    text_content = ""
    used_ocr = False
    confidence_score = 1.0
    
    try:
        # First try pdfplumber for text-based PDFs
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            
            text_content = "\n".join(pages_text)
        
        # Check if we got meaningful text
        if len(text_content.strip()) < 100:
            # Fall back to OCR
            logger.info("Text extraction yielded little content, falling back to OCR")
            text_content, confidence_score = _extract_with_ocr(pdf_bytes)
            used_ocr = True
        else:
            # Calculate confidence based on text quality
            confidence_score = _calculate_text_confidence(text_content)
            
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}, falling back to OCR")
        try:
            text_content, confidence_score = _extract_with_ocr(pdf_bytes)
            used_ocr = True
        except Exception as ocr_error:
            logger.error(f"OCR also failed: {ocr_error}")
            raise ValueError(f"Could not extract text from PDF: {ocr_error}")
    
    return text_content, used_ocr, confidence_score


def _extract_with_ocr(pdf_bytes: bytes) -> Tuple[str, float]:
    """
    Extract text using OCR (pytesseract).
    
    Returns:
        Tuple[str, float]: (extracted_text, confidence_score)
    """
    try:
        # Convert PDF to images
        images = convert_from_bytes(pdf_bytes, dpi=300)
        
        all_text = []
        total_confidence = 0
        
        for i, image in enumerate(images):
            # Get detailed OCR data with confidence
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text
            page_text = pytesseract.image_to_string(image)
            all_text.append(page_text)
            
            # Calculate page confidence
            confidences = [int(c) for c in ocr_data['conf'] if c != '-1' and int(c) > 0]
            if confidences:
                page_confidence = sum(confidences) / len(confidences) / 100
                total_confidence += page_confidence
        
        combined_text = "\n".join(all_text)
        avg_confidence = total_confidence / len(images) if images else 0.5
        
        # Reduce confidence since OCR is less reliable
        avg_confidence *= 0.8
        
        return combined_text, max(0.1, min(1.0, avg_confidence))
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        raise


def _calculate_text_confidence(text: str) -> float:
    """
    Calculate confidence score based on text quality indicators.
    """
    confidence = 1.0
    
    # Check for common indicators of good extraction
    indicators = {
        'date': 0.1,
        'amount': 0.1,
        'balance': 0.1,
        'debit': 0.05,
        'credit': 0.05,
        'transaction': 0.05,
        'account': 0.05,
    }
    
    text_lower = text.lower()
    found_indicators = 0
    
    for indicator in indicators:
        if indicator in text_lower:
            found_indicators += 1
    
    # Base confidence on found indicators
    indicator_score = found_indicators / len(indicators)
    
    # Check for numeric content (amounts, dates)
    import re
    numeric_patterns = re.findall(r'\d+[,.]?\d*', text)
    has_numeric = len(numeric_patterns) > 10
    
    # Check for date patterns
    date_patterns = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
    has_dates = len(date_patterns) > 5
    
    # Calculate final confidence
    confidence = 0.4 + (indicator_score * 0.3) + (0.15 if has_numeric else 0) + (0.15 if has_dates else 0)
    
    return max(0.2, min(1.0, confidence))


def extract_tables_from_pdf(pdf_bytes: bytes) -> List[List[List[str]]]:
    """
    Extract tables from PDF using pdfplumber.
    
    Returns:
        List of tables, where each table is a list of rows, and each row is a list of cells.
    """
    tables = []
    
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
    except Exception as e:
        logger.warning(f"Table extraction failed: {e}")
    
    return tables
