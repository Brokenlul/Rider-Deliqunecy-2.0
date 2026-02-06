"""
Feature Engineering Module for Lily's Score
Computes 5 financial risk metrics from normalized transactions
"""

import re
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


def compute_all_metrics(transactions: List[Dict], weekly_rent: float) -> Dict[str, Any]:
    """
    Compute all 5 financial metrics from transactions.
    
    Args:
        transactions: List of normalized transaction dicts
        weekly_rent: Weekly rent amount provided by user
        
    Returns:
        Dict containing all metric results
    """
    results = {
        'income_stability': compute_income_stability(transactions),
        'weekly_affordability': compute_weekly_affordability(transactions, weekly_rent),
        'liquidity_behavior': compute_liquidity_behavior(transactions),
        'expense_discipline': compute_expense_discipline(transactions),
        'negative_events': compute_negative_events(transactions),
    }
    
    return results


def compute_income_stability(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Metric 1: Income Stability (max 30 points)
    - Use credit transactions
    - Group by month
    - Compute monthly total credits
    - Compute volatility = std(monthly_totals)/mean(monthly_totals)
    """
    MAX_POINTS = 30
    
    # Group credits by month
    monthly_credits = defaultdict(float)
    
    for txn in transactions:
        credit = txn.get('credit', 0) or 0
        if credit > 0:
            date_str = txn.get('date', '')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    month_key = f"{dt.year}-{dt.month:02d}"
                    monthly_credits[month_key] += credit
                except ValueError:
                    continue
    
    monthly_totals = list(monthly_credits.values())
    
    if len(monthly_totals) < 2:
        # Not enough data for volatility calculation
        return {
            'points': MAX_POINTS * 0.5,
            'max_points': MAX_POINTS,
            'volatility': None,
            'monthly_totals': dict(monthly_credits),
            'mean_monthly': monthly_totals[0] if monthly_totals else 0,
            'explanation': 'Insufficient data for volatility calculation (need at least 2 months)',
            'score_reason': 'Partial score due to limited data'
        }
    
    mean_income = statistics.mean(monthly_totals)
    std_income = statistics.stdev(monthly_totals)
    volatility = std_income / mean_income if mean_income > 0 else 1.0
    
    # Scoring based on volatility
    if volatility <= 0.15:
        percentage = 1.0
        reason = 'Very stable income (volatility ≤ 15%)'
    elif volatility <= 0.35:
        percentage = 0.8
        reason = 'Moderately stable income (volatility 15-35%)'
    elif volatility <= 0.60:
        percentage = 0.55
        reason = 'Variable income (volatility 35-60%)'
    else:
        percentage = 0.25
        reason = 'Highly variable income (volatility > 60%)'
    
    points = MAX_POINTS * percentage
    
    return {
        'points': round(points, 2),
        'max_points': MAX_POINTS,
        'volatility': round(volatility, 4),
        'monthly_totals': dict(monthly_credits),
        'mean_monthly': round(mean_income, 2),
        'std_monthly': round(std_income, 2),
        'explanation': f'Monthly income volatility: {volatility:.2%}',
        'score_reason': reason
    }


def compute_weekly_affordability(transactions: List[Dict], weekly_rent: float) -> Dict[str, Any]:
    """
    Metric 2: Weekly Affordability Ratio (max 30 points)
    - Compute avg weekly inflow = mean(weekly total credits)
    - ratio = weekly_rent / avg_weekly_inflow
    """
    MAX_POINTS = 30
    
    # Group credits by week
    weekly_credits = defaultdict(float)
    
    for txn in transactions:
        credit = txn.get('credit', 0) or 0
        if credit > 0:
            date_str = txn.get('date', '')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    # ISO week number
                    week_key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
                    weekly_credits[week_key] += credit
                except ValueError:
                    continue
    
    weekly_totals = list(weekly_credits.values())
    
    if not weekly_totals:
        return {
            'points': 0,
            'max_points': MAX_POINTS,
            'ratio': None,
            'avg_weekly_inflow': 0,
            'weekly_rent': weekly_rent,
            'explanation': 'No credit transactions found',
            'score_reason': 'Cannot assess - no income data',
            'risk_level': 'Unknown'
        }
    
    avg_weekly_inflow = statistics.mean(weekly_totals)
    ratio = weekly_rent / avg_weekly_inflow if avg_weekly_inflow > 0 else 1.0
    
    # Scoring based on ratio
    if ratio < 0.20:
        percentage = 1.0
        risk_level = 'Very Safe'
        reason = f'Rent is only {ratio:.1%} of weekly income - very affordable'
    elif ratio < 0.30:
        percentage = 0.8
        risk_level = 'Safe'
        reason = f'Rent is {ratio:.1%} of weekly income - affordable'
    elif ratio < 0.40:
        percentage = 0.5
        risk_level = 'Risky'
        reason = f'Rent is {ratio:.1%} of weekly income - borderline affordable'
    else:
        percentage = 0.2
        risk_level = 'High Risk'
        reason = f'Rent is {ratio:.1%} of weekly income - may struggle to afford'
    
    points = MAX_POINTS * percentage
    
    return {
        'points': round(points, 2),
        'max_points': MAX_POINTS,
        'ratio': round(ratio, 4),
        'avg_weekly_inflow': round(avg_weekly_inflow, 2),
        'weekly_rent': weekly_rent,
        'weeks_analyzed': len(weekly_totals),
        'explanation': f'Weekly rent ({weekly_rent}) is {ratio:.1%} of avg weekly income ({avg_weekly_inflow:.2f})',
        'score_reason': reason,
        'risk_level': risk_level
    }


def compute_liquidity_behavior(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Metric 3: Liquidity Behavior (max 20 points)
    - Use balance column if available
    - Compute fraction of rows with balance < 1000
    - Compute median balance
    """
    MAX_POINTS = 20
    
    balances = []
    for txn in transactions:
        balance = txn.get('balance')
        if balance is not None:
            balances.append(balance)
    
    if not balances:
        # Try to reconstruct running balance
        balances = _reconstruct_balance(transactions)
    
    if not balances:
        return {
            'points': MAX_POINTS * 0.5,
            'max_points': MAX_POINTS,
            'rows_below_1000': None,
            'fraction_below_1000': None,
            'median_balance': None,
            'min_balance': None,
            'max_balance': None,
            'explanation': 'Balance data not available',
            'score_reason': 'Partial score due to missing balance information',
            'balance_available': False
        }
    
    rows_below_1000 = sum(1 for b in balances if b < 1000)
    fraction_below_1000 = rows_below_1000 / len(balances)
    median_balance = statistics.median(balances)
    min_balance = min(balances)
    max_balance = max(balances)
    
    # Scoring based on liquidity metrics
    # Penalize heavily for frequent near-zero balances
    base_score = 1.0
    
    # Deduct for low median balance
    if median_balance < 1000:
        base_score -= 0.4
    elif median_balance < 5000:
        base_score -= 0.2
    elif median_balance < 10000:
        base_score -= 0.1
    
    # Deduct for frequent low balances
    if fraction_below_1000 > 0.5:
        base_score -= 0.4
    elif fraction_below_1000 > 0.3:
        base_score -= 0.25
    elif fraction_below_1000 > 0.1:
        base_score -= 0.1
    
    # Deduct for very low minimum balance
    if min_balance < 0:
        base_score -= 0.2
    elif min_balance < 500:
        base_score -= 0.1
    
    points = MAX_POINTS * max(0, min(1, base_score))
    
    # Generate explanation
    if base_score >= 0.8:
        reason = 'Good liquidity - maintains healthy balance'
    elif base_score >= 0.6:
        reason = 'Moderate liquidity - occasional low balances'
    elif base_score >= 0.4:
        reason = 'Concerning liquidity - frequent low balances'
    else:
        reason = 'Poor liquidity - balance often near zero'
    
    return {
        'points': round(points, 2),
        'max_points': MAX_POINTS,
        'rows_below_1000': rows_below_1000,
        'fraction_below_1000': round(fraction_below_1000, 4),
        'median_balance': round(median_balance, 2),
        'min_balance': round(min_balance, 2),
        'max_balance': round(max_balance, 2),
        'total_balance_records': len(balances),
        'explanation': f'Median balance: ₹{median_balance:,.2f}, {fraction_below_1000:.1%} records below ₹1000',
        'score_reason': reason,
        'balance_available': True
    }


def compute_expense_discipline(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Metric 4: Expense Discipline (max 10 points)
    - Use debits and description keyword flags
    - Red flag keywords: gambling, cash withdrawals, loan/bnpl
    """
    MAX_POINTS = 10
    
    # Define red flag categories with keywords
    red_flags = {
        'gambling': ['dream11', 'mpl', 'rummy', 'poker', 'casino', 'bet', 'stake', 'winzo', 'ludo'],
        'cash_withdrawals': ['atm', 'cash withdraw', 'cash withdrawal', 'cashback'],
        'loan_bnpl': ['emi', 'loan', 'paylater', 'bnpl', 'slice', 'lazy', 'kreditbee', 'simpl', 'zestmoney']
    }
    
    flag_counts = {category: [] for category in red_flags}
    total_debit = 0
    
    for txn in transactions:
        debit = txn.get('debit', 0) or 0
        if debit > 0:
            total_debit += debit
            desc = (txn.get('description', '') or '').lower()
            
            for category, keywords in red_flags.items():
                for keyword in keywords:
                    if keyword in desc:
                        flag_counts[category].append({
                            'date': txn.get('date'),
                            'description': txn.get('description'),
                            'amount': debit
                        })
                        break
    
    # Calculate penalty
    gambling_count = len(flag_counts['gambling'])
    cash_count = len(flag_counts['cash_withdrawals'])
    loan_count = len(flag_counts['loan_bnpl'])
    
    # Weighted penalties
    penalty = 0
    penalty += gambling_count * 2.5  # Gambling is heavily penalized
    penalty += min(cash_count * 0.5, 2)  # Cash withdrawals capped at 2 points
    penalty += loan_count * 1.5  # BNPL/loans moderately penalized
    
    points = max(0, MAX_POINTS - penalty)
    
    # Generate explanation
    explanations = []
    if gambling_count > 0:
        explanations.append(f'{gambling_count} gambling transactions detected')
    if cash_count > 0:
        explanations.append(f'{cash_count} ATM/cash withdrawals')
    if loan_count > 0:
        explanations.append(f'{loan_count} EMI/loan/BNPL payments')
    
    if points >= 8:
        reason = 'Good expense discipline - minimal red flags'
    elif points >= 5:
        reason = 'Moderate expense discipline - some concerns'
    else:
        reason = 'Poor expense discipline - multiple red flags'
    
    return {
        'points': round(points, 2),
        'max_points': MAX_POINTS,
        'flag_counts': {
            'gambling': gambling_count,
            'cash_withdrawals': cash_count,
            'loan_bnpl': loan_count
        },
        'flagged_transactions': {
            'gambling': flag_counts['gambling'][:5],  # Limit to 5 examples
            'cash_withdrawals': flag_counts['cash_withdrawals'][:5],
            'loan_bnpl': flag_counts['loan_bnpl'][:5]
        },
        'total_debit_amount': round(total_debit, 2),
        'explanation': '; '.join(explanations) if explanations else 'No red flags detected',
        'score_reason': reason
    }


def compute_negative_events(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Metric 5: Negative Events (max 10 points)
    - Scan for: cheque return, bounce, insufficient, penalty, charges, overdraft, etc.
    """
    MAX_POINTS = 10
    
    negative_keywords = [
        'cheque return', 'returned', 'bounce', 'bounced', 'insufficient',
        'penalty', 'charges', 'fee', 'overdraft', 'nfs', 'ecs return',
        'imps return', 'rejected', 'failed', 'dishonour', 'dishonored'
    ]
    
    negative_events = []
    
    for txn in transactions:
        desc = (txn.get('description', '') or '').lower()
        for keyword in negative_keywords:
            if keyword in desc:
                negative_events.append({
                    'date': txn.get('date'),
                    'description': txn.get('description'),
                    'keyword_matched': keyword,
                    'amount': txn.get('debit', 0) or txn.get('credit', 0)
                })
                break
    
    event_count = len(negative_events)
    
    # Scoring based on event count
    if event_count == 0:
        points = MAX_POINTS
        reason = 'No negative events detected - excellent track record'
    elif event_count == 1:
        points = 7
        reason = '1 negative event found - minor concern'
    elif event_count == 2:
        points = 4
        reason = '2 negative events found - moderate concern'
    else:
        points = 1
        reason = f'{event_count} negative events found - significant concern'
    
    return {
        'points': points,
        'max_points': MAX_POINTS,
        'event_count': event_count,
        'events': negative_events[:10],  # Limit to 10 examples
        'explanation': f'{event_count} negative event(s) detected' if event_count > 0 else 'Clean record - no negative events',
        'score_reason': reason
    }


def _reconstruct_balance(transactions: List[Dict]) -> List[float]:
    """
    Attempt to reconstruct running balance from debits and credits.
    """
    if not transactions:
        return []
    
    # Sort by date
    sorted_txns = sorted(transactions, key=lambda x: x.get('date', ''))
    
    # Start with an estimated initial balance
    total_credits = sum(t.get('credit', 0) or 0 for t in sorted_txns)
    total_debits = sum(t.get('debit', 0) or 0 for t in sorted_txns)
    
    # Assume starting balance is roughly 20% of total credits
    running_balance = total_credits * 0.2
    balances = []
    
    for txn in sorted_txns:
        credit = txn.get('credit', 0) or 0
        debit = txn.get('debit', 0) or 0
        running_balance = running_balance + credit - debit
        balances.append(running_balance)
    
    return balances
