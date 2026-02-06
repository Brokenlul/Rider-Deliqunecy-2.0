#!/usr/bin/env python3
"""
Lily's Score CLI
Command-line interface for bank statement analysis

Usage:
    python cli.py --pdf sample.pdf --weekly_rent 900
    python cli.py --demo --weekly_rent 900
    python cli.py --test
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pdf_extractor import extract_text_from_pdf
from transaction_parser import parse_transactions, generate_synthetic_transactions
from feature_engine import compute_all_metrics
from scoring_engine import calculate_lily_score, run_test_cases


def analyze_pdf(pdf_path: str, weekly_rent: float) -> dict:
    """Analyze a PDF bank statement and return Lily's Score."""
    
    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print(f"📄 Reading PDF: {pdf_path}")
    print(f"💰 Weekly Rent: ₹{weekly_rent}")
    print("-" * 50)
    
    # Extract text
    print("📖 Extracting text from PDF...")
    raw_text, used_ocr, extraction_confidence = extract_text_from_pdf(pdf_bytes)
    
    if used_ocr:
        print("⚠️  OCR was used (scanned document detected)")
    
    print(f"✓ Extraction confidence: {extraction_confidence:.2%}")
    
    # Parse transactions
    print("🔍 Parsing transactions...")
    transactions, parse_confidence = parse_transactions(raw_text)
    
    print(f"✓ Found {len(transactions)} transactions")
    print(f"✓ Parse confidence: {parse_confidence:.2%}")
    
    if not transactions:
        return {
            "success": False,
            "error": "No transactions could be parsed from the document"
        }
    
    # Compute metrics
    print("📊 Computing financial metrics...")
    metrics = compute_all_metrics(transactions, weekly_rent)
    
    # Calculate score
    print("🎯 Calculating Lily's Score...")
    score_result = calculate_lily_score(metrics)
    
    # Build result
    result = {
        "success": True,
        "final_score": score_result['final_score'],
        "tier": score_result['tier'],
        "tier_description": score_result['tier_description'],
        "rent_multiplier": score_result['rent_multiplier'],
        "security_deposit": score_result['security_deposit'],
        "summary": score_result['summary'],
        "transactions_count": len(transactions),
        "parser_confidence": round((extraction_confidence * 0.4) + (parse_confidence * 0.6), 2),
        "used_ocr": used_ocr,
        "breakdown": score_result['breakdown'],
        "recommendations": score_result['recommendations'],
        "metrics_detail": metrics
    }
    
    return result


def run_demo(weekly_rent: float) -> dict:
    """Run analysis on synthetic demo data."""
    
    print("🎮 Running Demo Mode with Synthetic Data")
    print(f"💰 Weekly Rent: ₹{weekly_rent}")
    print("-" * 50)
    
    # Generate synthetic transactions
    print("🔄 Generating synthetic transactions...")
    transactions = generate_synthetic_transactions()
    print(f"✓ Generated {len(transactions)} transactions")
    
    # Compute metrics
    print("📊 Computing financial metrics...")
    metrics = compute_all_metrics(transactions, weekly_rent)
    
    # Calculate score
    print("🎯 Calculating Lily's Score...")
    score_result = calculate_lily_score(metrics)
    
    return {
        "success": True,
        "demo_mode": True,
        "final_score": score_result['final_score'],
        "tier": score_result['tier'],
        "tier_description": score_result['tier_description'],
        "summary": score_result['summary'],
        "transactions_count": len(transactions),
        "breakdown": score_result['breakdown'],
        "recommendations": score_result['recommendations']
    }


def run_tests() -> dict:
    """Run synthetic test cases."""
    
    print("🧪 Running Test Cases")
    print("-" * 50)
    
    results = run_test_cases()
    
    for i, result in enumerate(results, 1):
        print(f"\nTest Case {i}: {result['case']}")
        print(f"  Score: {result['score']}")
        print(f"  Tier: {result['tier']}")
        print(f"  Expected: {result['expected_tier']}")
    
    return {
        "success": True,
        "test_results": results
    }


def print_result(result: dict, verbose: bool = False):
    """Pretty print the analysis result."""
    
    print("\n" + "=" * 50)
    print("📋 LILY'S SCORE REPORT")
    print("=" * 50)
    
    if not result.get('success'):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    # Score and Tier
    score = result['final_score']
    tier = result['tier']
    
    tier_emoji = {
        'Premium': '🌟',
        'Standard': '✅',
        'Watchlist': '⚠️',
        'Reject': '❌'
    }.get(tier, '❓')
    
    print(f"\n{tier_emoji} Final Score: {score}/100")
    print(f"📊 Tier: {tier}")
    print(f"📝 {result.get('tier_description', '')}")
    
    if result.get('rent_multiplier'):
        print(f"\n💵 Rent Multiplier: {result['rent_multiplier']}x")
        print(f"🏦 Security Deposit: {result['security_deposit']}")
    
    # Breakdown
    print("\n📈 METRIC BREAKDOWN:")
    print("-" * 40)
    
    for metric in result.get('breakdown', []):
        bar_length = int(metric['percentage'] / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)
        print(f"  {metric['metric']:<22} {metric['points']:>5.1f}/{metric['max_points']} [{bar}] {metric['percentage']:.0f}%")
    
    # Recommendations
    if verbose and result.get('recommendations'):
        recs = result['recommendations']
        
        if recs.get('pricing') and not recs['pricing'].get('recommendation'):
            print("\n💰 PRICING RECOMMENDATION:")
            print("-" * 40)
            pricing = recs['pricing']
            print(f"  Weekly Rent Input: ₹{pricing.get('weekly_rent_input', 'N/A')}")
            print(f"  Recommended Rent: ₹{pricing.get('recommended_weekly_rent', 'N/A')}")
            print(f"  Security Deposit: ₹{pricing.get('security_deposit_amount', 'N/A')} ({pricing.get('security_deposit_weeks', 0)} weeks)")
        
        if recs.get('risk_factors'):
            print("\n⚠️  RISK FACTORS:")
            for factor in recs['risk_factors']:
                print(f"  • {factor}")
    
    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Lily's Score - Bank Statement Credit Assessment CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pdf statement.pdf --weekly_rent 900
  %(prog)s --demo --weekly_rent 900
  %(prog)s --test
  %(prog)s --pdf statement.pdf --weekly_rent 900 --json
        """
    )
    
    parser.add_argument('--pdf', type=str, help='Path to bank statement PDF')
    parser.add_argument('--weekly_rent', type=float, default=900, help='Weekly rent amount (default: 900)')
    parser.add_argument('--demo', action='store_true', help='Run demo with synthetic data')
    parser.add_argument('--test', action='store_true', help='Run test cases')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.test:
        result = run_tests()
    elif args.demo:
        result = run_demo(args.weekly_rent)
    elif args.pdf:
        if not Path(args.pdf).exists():
            print(f"❌ Error: File not found: {args.pdf}")
            sys.exit(1)
        result = analyze_pdf(args.pdf, args.weekly_rent)
    else:
        parser.print_help()
        sys.exit(0)
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_result(result, verbose=args.verbose)


if __name__ == '__main__':
    main()
