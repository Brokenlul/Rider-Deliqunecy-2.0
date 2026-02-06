# Lily's Score - Product Requirements Document

## Project Overview
**Product Name:** Lily's Score  
**Company:** Lilypad  
**Version:** 1.0.0 MVP  
**Last Updated:** February 6, 2026

## Problem Statement
Build an end-to-end system that lets an operator upload a rider's bank statement PDF (last 3 months), extracts transactions, computes 5 financial risk metrics, assigns a Lily's Score (0–100), and outputs a rider quality classification + rent/security recommendation.

## User Personas
1. **Fleet Operators** - Upload statements and get instant risk assessments
2. **Risk Assessment Teams** - Review detailed breakdowns and recommendations
3. **Financial Analysts** - Deep dive into metric calculations

## Core Requirements (Static)

### Functional Requirements
1. PDF Upload with OCR fallback support
2. Transaction parsing for Indian bank formats (HDFC/ICICI/SBI/Axis)
3. 5 Financial Metrics Calculation:
   - Income Stability (30 pts)
   - Weekly Affordability (30 pts)
   - Liquidity Behavior (20 pts)
   - Expense Discipline (10 pts)
   - Negative Events (10 pts)
4. Lily's Score (0-100) with tier classification
5. Pricing recommendations based on tier
6. CLI mode for batch processing

### Non-Functional Requirements
- Stateless processing (no PDF storage)
- Max 10MB PDF upload limit
- Support for text-based and scanned PDFs

## What's Been Implemented ✅

### Backend (February 6, 2026)
- [x] `pdf_extractor.py` - PDF text extraction with pdfplumber + OCR fallback (pytesseract)
- [x] `transaction_parser.py` - Transaction normalization for Indian bank formats
- [x] `feature_engine.py` - All 5 financial metrics calculation
- [x] `scoring_engine.py` - Lily's Score calculation and tier assignment
- [x] `server.py` - FastAPI endpoints (/analyze, /synthetic-demo, /test-cases)
- [x] `cli.py` - Command-line interface with --pdf, --demo, --test options

### Frontend (February 6, 2026)
- [x] Dark theme with cyan accent (#00FFFF, #B0FFFF)
- [x] Upload page with PDF dropzone and weekly rent input
- [x] Results dashboard with score gauge, tier badge
- [x] 5 metric cards with progress bars and explanations
- [x] Recommendations panel with pricing suggestions
- [x] Transactions table with CSV download
- [x] Demo mode for testing without PDF

### APIs Implemented
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/health | GET | Health check |
| /api/analyze | POST | Analyze PDF upload |
| /api/synthetic-demo | GET | Demo with synthetic data |
| /api/test-cases | GET | Run 3 test cases |

## Tier Classification
| Score | Tier | Rent Multiplier | Security Deposit |
|-------|------|-----------------|------------------|
| 80-100 | Premium | 0.90x | 1 week |
| 60-79 | Standard | 1.00x | 2 weeks |
| 40-59 | Watchlist | 1.10x | 4 weeks |
| <40 | Reject | N/A | Manual Review |

## Prioritized Backlog

### P0 (Critical) - ✅ Complete
- PDF upload and analysis flow
- 5 metrics calculation
- Score and tier assignment
- Frontend dashboard

### P1 (Important) - Future V2
- Persistent storage for analysis history
- Batch PDF processing
- User authentication
- Multi-tenant support

### P2 (Nice-to-Have) - Future V3
- Work hours integration (Uber/Ola/Rapido APIs)
- KYC verification APIs
- Machine learning score refinement
- Mobile-responsive design improvements

## V2 Extension Notes (Not Implemented)

### Work Hours Integration
- Integrate with gig platform APIs (Uber, Ola, Rapido)
- Add new metric: Work Consistency (max 20 pts)
- Adjust existing metrics weights

### KYC APIs
- Aadhaar verification
- PAN card validation
- Address proof verification

## Security Notes
- PDFs processed in-memory only
- No permanent storage of uploaded files
- Derived metrics can be stored if configured
- All sensitive data should be encrypted in transit

## Tech Stack
- **Backend:** Python 3.11, FastAPI, pdfplumber, pytesseract, pandas
- **Frontend:** React 19, Tailwind CSS, shadcn/ui, Recharts
- **Database:** MongoDB (for future history storage)
- **OCR:** Tesseract OCR with pdf2image

## Run Instructions
```bash
# Backend
cd /app/backend
pip install -r requirements.txt
python -m uvicorn server:app --reload

# CLI Mode
python cli.py --pdf sample.pdf --weekly_rent 900
python cli.py --demo --weekly_rent 900
python cli.py --test

# Frontend
cd /app/frontend
yarn install
yarn start
```
