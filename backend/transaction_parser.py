"""
Transaction Parser Module for Lily's Score
Normalizes raw text into structured transaction schema
Handles common Indian bank statement formats (HDFC, ICICI, SBI, Axis)
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    date: str  # ISO format yyyy-mm-dd
    description: str
    debit: float
    credit: float
    balance: Optional[float]
    source_line: str


def parse_transactions(raw_text: str) -> Tuple[List[Dict], float]:
    """
    Parse raw text into normalized transactions.
    
    Returns:
        Tuple[List[Dict], float]: (transactions, parser_confidence)
    """
    lines = raw_text.split('\n')
    transactions = []
    successful_parses = 0
    total_attempts = 0
    
    # Try different parsing strategies
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
            
        # Skip header lines
        if _is_header_line(line):
            continue
        
        # Check if line looks like a transaction
        if _looks_like_transaction(line):
            total_attempts += 1
            transaction = _parse_transaction_line(line)
            if transaction:
                transactions.append(transaction)
                successful_parses += 1
    
    # Calculate parser confidence
    confidence = successful_parses / total_attempts if total_attempts > 0 else 0.0
    
    # Adjust confidence based on transaction quality
    if transactions:
        has_balance = any(t.get('balance') is not None for t in transactions)
        if has_balance:
            confidence = min(1.0, confidence + 0.1)
        
        # Check date consistency
        dates_valid = sum(1 for t in transactions if _validate_date(t.get('date', '')))
        date_ratio = dates_valid / len(transactions)
        confidence = confidence * (0.5 + date_ratio * 0.5)
    
    logger.info(f"Parsed {len(transactions)} transactions with confidence {confidence:.2f}")
    
    return [_transaction_to_dict(t) if isinstance(t, Transaction) else t for t in transactions], confidence


def _is_header_line(line: str) -> bool:
    """Check if line is a header."""
    headers = [
        'date', 'particulars', 'description', 'narration', 'withdrawal', 'deposit',
        'balance', 'dr', 'cr', 'cheque', 'chq', 'ref', 'transaction', 'debit', 'credit',
        'amount', 'opening', 'closing', 'statement', 'account'
    ]
    line_lower = line.lower()
    header_count = sum(1 for h in headers if h in line_lower)
    return header_count >= 3


def _looks_like_transaction(line: str) -> bool:
    """Check if line looks like a transaction."""
    # Must have a date pattern
    date_pattern = r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}'
    if not re.search(date_pattern, line):
        return False
    
    # Must have some amount (number with optional commas)
    amount_pattern = r'[\d,]+\.\d{2}'
    if not re.search(amount_pattern, line):
        # Try without decimals
        if not re.search(r'[\d,]{3,}', line):
            return False
    
    return True


def _parse_transaction_line(line: str) -> Optional[Dict]:
    """
    Parse a single transaction line.
    Tries multiple formats common in Indian bank statements.
    """
    # Try different parsing strategies
    strategies = [
        _parse_hdfc_format,
        _parse_icici_format,
        _parse_sbi_format,
        _parse_generic_format,
    ]
    
    for strategy in strategies:
        result = strategy(line)
        if result:
            return result
    
    return None


def _parse_hdfc_format(line: str) -> Optional[Dict]:
    """
    Parse HDFC-style format:
    DD/MM/YY or DD/MM/YYYY | Description | Withdrawal | Deposit | Balance
    """
    # Pattern: date description amount(s)
    pattern = r'^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)\s*([\d,]+\.?\d*)?\s*([\d,]+\.?\d*)?$'
    match = re.match(pattern, line)
    
    if match:
        date_str, desc, amt1, amt2, amt3 = match.groups()
        
        date = _parse_date(date_str)
        if not date:
            return None
        
        # Determine debit/credit/balance based on position and description
        debit, credit, balance = _determine_amounts(desc, amt1, amt2, amt3)
        
        return {
            'date': date,
            'description': desc.strip(),
            'debit': debit,
            'credit': credit,
            'balance': balance,
            'source_line': line
        }
    
    return None


def _parse_icici_format(line: str) -> Optional[Dict]:
    """
    Parse ICICI-style format with CR/DR markers.
    """
    # Pattern with CR/DR marker
    pattern = r'^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)\s*(CR|DR|Cr|Dr|cr|dr)?\s*([\d,]+\.?\d*)?$'
    match = re.match(pattern, line)
    
    if match:
        date_str, desc, amount, cr_dr, balance = match.groups()
        
        date = _parse_date(date_str)
        if not date:
            return None
        
        amount_val = _parse_amount(amount)
        balance_val = _parse_amount(balance) if balance else None
        
        # Determine debit/credit based on CR/DR marker or description
        if cr_dr and cr_dr.upper() == 'CR':
            debit, credit = 0.0, amount_val
        elif cr_dr and cr_dr.upper() == 'DR':
            debit, credit = amount_val, 0.0
        else:
            debit, credit = _infer_debit_credit(desc, amount_val)
        
        return {
            'date': date,
            'description': desc.strip(),
            'debit': debit,
            'credit': credit,
            'balance': balance_val,
            'source_line': line
        }
    
    return None


def _parse_sbi_format(line: str) -> Optional[Dict]:
    """
    Parse SBI-style format.
    DD-MMM-YY | Description | Debit | Credit | Balance
    """
    # Pattern with month names
    pattern = r'^(\d{1,2}[-\s]?[A-Za-z]{3}[-\s]?\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)?\s*([\d,]+\.?\d*)?\s*([\d,]+\.?\d*)?$'
    match = re.match(pattern, line)
    
    if match:
        date_str, desc, debit, credit, balance = match.groups()
        
        date = _parse_date(date_str)
        if not date:
            return None
        
        return {
            'date': date,
            'description': desc.strip(),
            'debit': _parse_amount(debit) if debit else 0.0,
            'credit': _parse_amount(credit) if credit else 0.0,
            'balance': _parse_amount(balance) if balance else None,
            'source_line': line
        }
    
    return None


def _parse_generic_format(line: str) -> Optional[Dict]:
    """
    Generic fallback parser.
    """
    # Find date
    date_match = re.search(r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})', line)
    if not date_match:
        return None
    
    date = _parse_date(date_match.group(1))
    if not date:
        return None
    
    # Find all amounts
    amounts = re.findall(r'([\d,]+\.\d{2})', line)
    if not amounts:
        amounts = re.findall(r'([\d,]{4,})', line)
    
    if not amounts:
        return None
    
    # Get description (everything between date and first amount)
    desc_start = date_match.end()
    amount_match = re.search(r'[\d,]+\.?\d*', line[desc_start:])
    if amount_match:
        desc_end = desc_start + amount_match.start()
        description = line[desc_start:desc_end].strip()
    else:
        description = line[desc_start:].strip()
    
    # Parse amounts
    parsed_amounts = [_parse_amount(a) for a in amounts[:3]]
    
    # Determine debit/credit
    if len(parsed_amounts) >= 3:
        debit = parsed_amounts[0]
        credit = parsed_amounts[1]
        balance = parsed_amounts[2]
    elif len(parsed_amounts) == 2:
        debit, credit = _infer_debit_credit(description, parsed_amounts[0])
        balance = parsed_amounts[1]
    else:
        debit, credit = _infer_debit_credit(description, parsed_amounts[0])
        balance = None
    
    return {
        'date': date,
        'description': description or 'Unknown',
        'debit': debit,
        'credit': credit,
        'balance': balance,
        'source_line': line
    }


def _parse_date(date_str: str) -> Optional[str]:
    """
    Parse various date formats and return ISO format (yyyy-mm-dd).
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Common formats to try
    formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
        '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
        '%Y-%m-%d', '%Y/%m/%d',
        '%d %b %Y', '%d-%b-%Y', '%d %b %y', '%d-%b-%y',
        '%d%b%Y', '%d%b%y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Handle 2-digit years
            if dt.year < 100:
                dt = dt.replace(year=dt.year + 2000)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


def _parse_amount(amount_str: str) -> float:
    """Parse amount string to float, handling commas and currency symbols."""
    if not amount_str:
        return 0.0
    
    # Remove currency symbols and whitespace
    amount_str = re.sub(r'[₹$€£\s]', '', amount_str)
    # Remove commas
    amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def _determine_amounts(desc: str, amt1: str, amt2: str, amt3: str) -> Tuple[float, float, Optional[float]]:
    """
    Determine debit, credit, balance from multiple amount columns.
    """
    amounts = [_parse_amount(a) for a in [amt1, amt2, amt3] if a]
    
    if len(amounts) == 3:
        # Assume: debit, credit, balance
        return amounts[0], amounts[1], amounts[2]
    elif len(amounts) == 2:
        # Check description for credit indicators
        credit_keywords = ['salary', 'credit', 'received', 'refund', 'cashback', 'interest']
        debit_keywords = ['debit', 'purchase', 'transfer', 'payment', 'atm', 'withdrawal']
        
        desc_lower = desc.lower()
        is_credit = any(kw in desc_lower for kw in credit_keywords)
        is_debit = any(kw in desc_lower for kw in debit_keywords)
        
        if is_credit and not is_debit:
            return 0.0, amounts[0], amounts[1]
        else:
            return amounts[0], 0.0, amounts[1]
    elif len(amounts) == 1:
        debit, credit = _infer_debit_credit(desc, amounts[0])
        return debit, credit, None
    
    return 0.0, 0.0, None


def _infer_debit_credit(description: str, amount: float) -> Tuple[float, float]:
    """
    Infer if transaction is debit or credit based on description.
    """
    desc_lower = description.lower()
    
    credit_keywords = [
        'salary', 'credit', 'received', 'refund', 'cashback', 'interest',
        'deposit', 'inward', 'cr', 'credited', 'reversal', 'bonus'
    ]
    
    debit_keywords = [
        'debit', 'purchase', 'transfer', 'payment', 'atm', 'withdrawal',
        'upi', 'neft', 'imps', 'rtgs', 'emi', 'ecs', 'nach', 'dr', 'debited'
    ]
    
    credit_score = sum(1 for kw in credit_keywords if kw in desc_lower)
    debit_score = sum(1 for kw in debit_keywords if kw in desc_lower)
    
    if credit_score > debit_score:
        return 0.0, amount
    else:
        return amount, 0.0


def _validate_date(date_str: str) -> bool:
    """Validate if date string is in correct ISO format."""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def _transaction_to_dict(t: Transaction) -> Dict:
    """Convert Transaction dataclass to dict."""
    return {
        'date': t.date,
        'description': t.description,
        'debit': t.debit,
        'credit': t.credit,
        'balance': t.balance,
        'source_line': t.source_line
    }


def generate_synthetic_transactions() -> List[Dict]:
    """
    Generate synthetic test transactions for testing scoring logic.
    """
    from datetime import timedelta
    import random
    
    transactions = []
    base_date = datetime(2024, 10, 1)
    running_balance = 25000.0
    
    # Simulate 3 months of transactions
    for month in range(3):
        # Monthly salary (credit)
        salary_date = base_date + timedelta(days=month * 30 + 1)
        salary = random.uniform(35000, 45000)
        running_balance += salary
        transactions.append({
            'date': salary_date.strftime('%Y-%m-%d'),
            'description': 'SALARY CREDIT ACME CORP',
            'debit': 0.0,
            'credit': round(salary, 2),
            'balance': round(running_balance, 2),
            'source_line': f'Synthetic salary transaction for month {month + 1}'
        })
        
        # Regular expenses throughout the month
        for week in range(4):
            # UPI payments
            for _ in range(random.randint(3, 7)):
                day = base_date + timedelta(days=month * 30 + week * 7 + random.randint(0, 6))
                amount = random.uniform(100, 2000)
                running_balance -= amount
                transactions.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'description': random.choice([
                        'UPI-SWIGGY', 'UPI-ZOMATO', 'UPI-AMAZON', 'UPI-FLIPKART',
                        'UPI-BIGBASKET', 'UPI-GROCERY', 'NEFT-TRANSFER'
                    ]),
                    'debit': round(amount, 2),
                    'credit': 0.0,
                    'balance': round(running_balance, 2),
                    'source_line': 'Synthetic expense'
                })
            
            # ATM withdrawal (once a week)
            if random.random() > 0.5:
                day = base_date + timedelta(days=month * 30 + week * 7 + random.randint(0, 6))
                amount = random.choice([2000, 3000, 5000])
                running_balance -= amount
                transactions.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'description': 'ATM CASH WITHDRAWAL',
                    'debit': amount,
                    'credit': 0.0,
                    'balance': round(running_balance, 2),
                    'source_line': 'Synthetic ATM withdrawal'
                })
        
        # Rent payment
        rent_date = base_date + timedelta(days=month * 30 + 5)
        rent = 12000
        running_balance -= rent
        transactions.append({
            'date': rent_date.strftime('%Y-%m-%d'),
            'description': 'NEFT-RENT PAYMENT',
            'debit': rent,
            'credit': 0.0,
            'balance': round(running_balance, 2),
            'source_line': 'Synthetic rent payment'
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    return transactions
