"""
Lily's Score - FastAPI Backend
Bank Statement Analysis API for Rider Credit Scoring
"""

from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import tempfile

# Local modules
from pdf_extractor import extract_text_from_pdf, extract_tables_from_pdf
from transaction_parser import parse_transactions, generate_synthetic_transactions
from feature_engine import compute_all_metrics
from scoring_engine import calculate_lily_score, run_test_cases

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(
    title="Lily's Score API",
    description="Bank Statement Analysis for Rider Credit Scoring",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic Models
class TransactionSchema(BaseModel):
    date: str
    description: str
    debit: float
    credit: float
    balance: Optional[float] = None
    source_line: str


class AnalysisRequest(BaseModel):
    weekly_rent: float = Field(..., gt=0, description="Weekly rent amount")


class MetricBreakdown(BaseModel):
    metric: str
    points: float
    max_points: float
    percentage: float
    explanation: str
    score_reason: str


class AnalysisResponse(BaseModel):
    success: bool
    rider_id: str
    final_score: float
    max_score: float
    tier: str
    tier_description: str
    tier_color: str
    rent_multiplier: Optional[float]
    security_deposit: str
    breakdown: List[Dict[str, Any]]
    recommendations: Dict[str, Any]
    summary: str
    transactions_count: int
    parser_confidence: float
    used_ocr: bool
    metrics_detail: Dict[str, Any]


class TestCaseResult(BaseModel):
    case: str
    score: float
    tier: str
    expected_tier: str


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Lily's Score API - Bank Statement Analysis"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@api_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_bank_statement(
    file: UploadFile = File(...),
    weekly_rent: float = Form(..., gt=0)
):
    """
    Analyze a bank statement PDF and return Lily's Score.
    
    - Upload PDF file
    - Provide weekly rent amount
    - Returns score, tier, and detailed breakdown
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        # Read file content
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        rider_id = str(uuid.uuid4())[:8]
        logger.info(f"Processing statement for rider {rider_id}")
        
        # Extract text from PDF
        raw_text, used_ocr, extraction_confidence = extract_text_from_pdf(pdf_bytes)
        
        if not raw_text or len(raw_text.strip()) < 50:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract meaningful text from PDF. Please ensure the file is not corrupted."
            )
        
        # Parse transactions
        transactions, parse_confidence = parse_transactions(raw_text)
        
        if not transactions:
            raise HTTPException(
                status_code=400,
                detail="Could not parse any transactions from the statement. Please check if the file is a valid bank statement."
            )
        
        # Combined parser confidence
        parser_confidence = (extraction_confidence * 0.4) + (parse_confidence * 0.6)
        
        # Compute metrics
        metrics = compute_all_metrics(transactions, weekly_rent)
        
        # Calculate final score
        score_result = calculate_lily_score(metrics)
        
        logger.info(f"Rider {rider_id}: Score={score_result['final_score']}, Tier={score_result['tier']}")
        
        return AnalysisResponse(
            success=True,
            rider_id=rider_id,
            final_score=score_result['final_score'],
            max_score=score_result['max_score'],
            tier=score_result['tier'],
            tier_description=score_result['tier_description'],
            tier_color=score_result['tier_color'],
            rent_multiplier=score_result['rent_multiplier'],
            security_deposit=score_result['security_deposit'],
            breakdown=score_result['breakdown'],
            recommendations=score_result['recommendations'],
            summary=score_result['summary'],
            transactions_count=len(transactions),
            parser_confidence=round(parser_confidence, 2),
            used_ocr=used_ocr,
            metrics_detail=metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@api_router.get("/transactions/{rider_id}")
async def get_transactions(rider_id: str, limit: int = 50):
    """
    Get parsed transactions for a rider.
    Note: In this stateless MVP, transactions are not stored.
    This endpoint is for future use with storage.
    """
    return {
        "rider_id": rider_id,
        "message": "Transactions are returned in the /analyze response. This endpoint is for future use with persistent storage."
    }


@api_router.post("/analyze-transactions")
async def analyze_transactions_only(
    transactions: List[TransactionSchema],
    weekly_rent: float = Form(...)
):
    """
    Analyze pre-parsed transactions without PDF upload.
    Useful for testing or when transactions are already parsed.
    """
    try:
        txn_dicts = [t.model_dump() for t in transactions]
        
        metrics = compute_all_metrics(txn_dicts, weekly_rent)
        score_result = calculate_lily_score(metrics)
        
        return {
            "success": True,
            "final_score": score_result['final_score'],
            "tier": score_result['tier'],
            "breakdown": score_result['breakdown'],
            "recommendations": score_result['recommendations'],
            "metrics_detail": metrics
        }
    except Exception as e:
        logger.error(f"Transaction analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/test-cases", response_model=List[TestCaseResult])
async def run_synthetic_tests():
    """
    Run synthetic test cases to validate scoring logic.
    Returns test results for 3 hardcoded scenarios.
    """
    try:
        results = run_test_cases()
        return results
    except Exception as e:
        logger.error(f"Test cases failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/synthetic-demo")
async def synthetic_demo(weekly_rent: float = 900):
    """
    Run a demo analysis using synthetic transactions.
    Useful for testing without uploading a PDF.
    """
    try:
        transactions = generate_synthetic_transactions()
        metrics = compute_all_metrics(transactions, weekly_rent)
        score_result = calculate_lily_score(metrics)
        
        return {
            "success": True,
            "demo_mode": True,
            "final_score": score_result['final_score'],
            "tier": score_result['tier'],
            "tier_description": score_result['tier_description'],
            "breakdown": score_result['breakdown'],
            "recommendations": score_result['recommendations'],
            "summary": score_result['summary'],
            "transactions_count": len(transactions),
            "transactions_sample": transactions[:10],
            "metrics_detail": metrics
        }
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Lily's Score API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Lily's Score API shutting down...")
