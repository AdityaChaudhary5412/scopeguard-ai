"""
ScopeGuard AI - Statement of Work (SOW) & Pricing Calculator
Transforms raw proposal inputs and risk analysis into professional commercial quotes.
"""

from typing import Dict, Any

def calculate_quote(base_hours: float, hourly_rate: float, buffer_pct: float) -> Dict[str, Any]:
    """Calculate commercial pricing options with risk contingency buffers."""
    base_cost = base_hours * hourly_rate
    contingency_cost = base_cost * (buffer_pct / 100.0)
    recommended_fixed_bid = base_cost + contingency_cost
    
    # Milestone breakdown (40% / 30% / 30%)
    deposit = round(recommended_fixed_bid * 0.40, 2)
    alpha = round(recommended_fixed_bid * 0.30, 2)
    final = round(recommended_fixed_bid * 0.30, 2)

    return {
        "base_hours": base_hours,
        "hourly_rate": hourly_rate,
        "base_cost": round(base_cost, 2),
        "buffer_pct": buffer_pct,
        "contingency_cost": round(contingency_cost, 2),
        "recommended_fixed_bid": round(recommended_fixed_bid, 2),
        "payment_schedule": {
            "deposit_40pct": deposit,
            "alpha_30pct": alpha,
            "final_30pct": final
        },
        "monthly_retainer_recommendation": round(base_hours * 0.15 * hourly_rate, 2)
    }

def format_pricing_table(quote: Dict[str, Any]) -> str:
    """Format quote into markdown pricing summary."""
    return f"""| Item | Value |
|---|---|
| **Base Estimated Hours** | {quote['base_hours']} hrs |
| **Contractor Hourly Rate** | ${quote['hourly_rate']:.2f}/hr |
| **Base Deliverable Estimate** | ${quote['base_cost']:.2f} |
| **Risk & Ambiguity Buffer ({quote['buffer_pct']}%)** | +${quote['contingency_cost']:.2f} |
| **Recommended Fixed Bid** | **${quote['recommended_fixed_bid']:.2f}** |
| • Upfront Deposit (40%) | ${quote['payment_schedule']['deposit_40pct']:.2f} |
| • Milestone Alpha (30%) | ${quote['payment_schedule']['alpha_30pct']:.2f} |
| • Final Completion (30%) | ${quote['payment_schedule']['final_30pct']:.2f} |
| **Suggested Post-Launch Retainer** | ${quote['monthly_retainer_recommendation']:.2f}/month |
"""
