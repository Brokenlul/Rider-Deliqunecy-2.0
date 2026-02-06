"""
Scoring Engine Module for Lily's Score
Calculates final score and rider classification
"""

from typing import Dict, Any


def calculate_lily_score(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate final Lily's Score from all metrics.
    
    Args:
        metrics: Dict containing all 5 metric results
        
    Returns:
        Dict with final score, tier, and recommendations
    """
    # Sum all metric points
    total_points = 0
    max_possible = 0
    
    breakdown = []
    
    for metric_name, metric_data in metrics.items():
        points = metric_data.get('points', 0)
        max_points = metric_data.get('max_points', 0)
        total_points += points
        max_possible += max_points
        
        breakdown.append({
            'metric': _format_metric_name(metric_name),
            'points': points,
            'max_points': max_points,
            'percentage': round((points / max_points * 100) if max_points > 0 else 0, 1),
            'explanation': metric_data.get('explanation', ''),
            'score_reason': metric_data.get('score_reason', '')
        })
    
    # Clamp final score to 0-100
    final_score = max(0, min(100, total_points))
    
    # Determine rider tier
    tier_info = _get_tier_info(final_score)
    
    # Generate recommendations
    recommendations = _generate_recommendations(final_score, metrics, tier_info)
    
    return {
        'final_score': round(final_score, 1),
        'max_score': 100,
        'tier': tier_info['tier'],
        'tier_description': tier_info['description'],
        'tier_color': tier_info['color'],
        'rent_multiplier': tier_info['rent_multiplier'],
        'security_deposit': tier_info['security_deposit'],
        'breakdown': breakdown,
        'recommendations': recommendations,
        'summary': _generate_summary(final_score, tier_info, breakdown)
    }


def _format_metric_name(name: str) -> str:
    """Convert snake_case to Title Case."""
    return name.replace('_', ' ').title()


def _get_tier_info(score: float) -> Dict[str, Any]:
    """
    Determine rider tier based on score.
    
    Score ranges:
    - 80-100: Premium
    - 60-79: Standard
    - 40-59: Watchlist
    - <40: Reject/Manual Review
    """
    if score >= 80:
        return {
            'tier': 'Premium',
            'description': 'Excellent financial health. Low risk rider.',
            'color': 'emerald',
            'rent_multiplier': 0.90,
            'security_deposit': 'Low (1 week)',
            'security_weeks': 1,
            'approval': 'Auto-Approve'
        }
    elif score >= 60:
        return {
            'tier': 'Standard',
            'description': 'Good financial standing. Average risk.',
            'color': 'cyan',
            'rent_multiplier': 1.00,
            'security_deposit': 'Medium (2 weeks)',
            'security_weeks': 2,
            'approval': 'Auto-Approve'
        }
    elif score >= 40:
        return {
            'tier': 'Watchlist',
            'description': 'Some financial concerns. Higher risk.',
            'color': 'amber',
            'rent_multiplier': 1.10,
            'security_deposit': 'High (4 weeks)',
            'security_weeks': 4,
            'approval': 'Conditional Approval'
        }
    else:
        return {
            'tier': 'Reject',
            'description': 'Significant financial concerns. Manual review required.',
            'color': 'red',
            'rent_multiplier': None,
            'security_deposit': 'Not Applicable',
            'security_weeks': None,
            'approval': 'Manual Review Required'
        }


def _generate_recommendations(score: float, metrics: Dict, tier_info: Dict) -> Dict[str, Any]:
    """Generate pricing and operational recommendations."""
    
    weekly_rent = metrics.get('weekly_affordability', {}).get('weekly_rent', 0)
    
    recommendations = {
        'pricing': {},
        'operational': [],
        'risk_factors': []
    }
    
    if tier_info['rent_multiplier']:
        adjusted_rent = weekly_rent * tier_info['rent_multiplier']
        recommendations['pricing'] = {
            'weekly_rent_input': weekly_rent,
            'rent_multiplier': tier_info['rent_multiplier'],
            'recommended_weekly_rent': round(adjusted_rent, 2),
            'security_deposit_weeks': tier_info['security_weeks'],
            'security_deposit_amount': round(adjusted_rent * tier_info['security_weeks'], 2)
        }
    else:
        recommendations['pricing'] = {
            'weekly_rent_input': weekly_rent,
            'recommendation': 'Do not proceed without manual review'
        }
    
    # Add operational recommendations
    income_stability = metrics.get('income_stability', {})
    if income_stability.get('volatility') and income_stability['volatility'] > 0.35:
        recommendations['operational'].append('Consider weekly payment schedule due to income volatility')
        recommendations['risk_factors'].append('High income volatility')
    
    liquidity = metrics.get('liquidity_behavior', {})
    if liquidity.get('fraction_below_1000') and liquidity['fraction_below_1000'] > 0.3:
        recommendations['operational'].append('Monitor payment timeliness closely')
        recommendations['risk_factors'].append('Frequent low balance')
    
    expense = metrics.get('expense_discipline', {})
    if expense.get('flag_counts', {}).get('gambling', 0) > 0:
        recommendations['operational'].append('Flag for additional verification')
        recommendations['risk_factors'].append('Gambling activity detected')
    
    if expense.get('flag_counts', {}).get('loan_bnpl', 0) > 2:
        recommendations['operational'].append('High existing debt obligations')
        recommendations['risk_factors'].append('Multiple EMI/BNPL payments')
    
    negative = metrics.get('negative_events', {})
    if negative.get('event_count', 0) > 0:
        recommendations['operational'].append('Review negative events before approval')
        recommendations['risk_factors'].append(f"{negative['event_count']} negative banking events")
    
    return recommendations


def _generate_summary(score: float, tier_info: Dict, breakdown: list) -> str:
    """Generate a human-readable summary."""
    
    # Find strongest and weakest metrics
    sorted_breakdown = sorted(breakdown, key=lambda x: x['percentage'], reverse=True)
    strongest = sorted_breakdown[0]
    weakest = sorted_breakdown[-1]
    
    summary_parts = [
        f"Lily's Score: {score:.0f}/100 ({tier_info['tier']} Tier)",
        f"Strongest area: {strongest['metric']} ({strongest['percentage']:.0f}%)",
        f"Area for concern: {weakest['metric']} ({weakest['percentage']:.0f}%)",
        f"Recommendation: {tier_info['approval']}"
    ]
    
    return " | ".join(summary_parts)


def run_test_cases():
    """
    Run synthetic test cases to validate scoring logic.
    Returns test results.
    """
    from transaction_parser import generate_synthetic_transactions
    from feature_engine import compute_all_metrics
    
    test_results = []
    
    # Test Case 1: Good rider
    test1_txns = generate_synthetic_transactions()
    test1_metrics = compute_all_metrics(test1_txns, weekly_rent=900)
    test1_score = calculate_lily_score(test1_metrics)
    test_results.append({
        'case': 'Good Rider - Regular salary, normal expenses',
        'score': test1_score['final_score'],
        'tier': test1_score['tier'],
        'expected_tier': 'Premium or Standard'
    })
    
    # Test Case 2: High gambling activity
    test2_txns = generate_synthetic_transactions()
    # Add gambling transactions
    for i in range(5):
        test2_txns.append({
            'date': f'2024-11-{10+i:02d}',
            'description': 'UPI-DREAM11',
            'debit': 1000,
            'credit': 0,
            'balance': 5000,
            'source_line': 'Test gambling'
        })
    test2_metrics = compute_all_metrics(test2_txns, weekly_rent=900)
    test2_score = calculate_lily_score(test2_metrics)
    test_results.append({
        'case': 'Risky Rider - Multiple gambling transactions',
        'score': test2_score['final_score'],
        'tier': test2_score['tier'],
        'expected_tier': 'Lower due to gambling penalties'
    })
    
    # Test Case 3: Low income, high rent
    test3_txns = []
    for i in range(3):
        test3_txns.append({
            'date': f'2024-{10+i:02d}-01',
            'description': 'SALARY CREDIT',
            'debit': 0,
            'credit': 15000,  # Low salary
            'balance': 5000,
            'source_line': 'Low salary'
        })
    test3_metrics = compute_all_metrics(test3_txns, weekly_rent=2000)  # High rent
    test3_score = calculate_lily_score(test3_metrics)
    test_results.append({
        'case': 'High Risk - Low income with high rent',
        'score': test3_score['final_score'],
        'tier': test3_score['tier'],
        'expected_tier': 'Watchlist or Reject'
    })
    
    return test_results
