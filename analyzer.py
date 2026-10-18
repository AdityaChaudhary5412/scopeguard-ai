"""
ScopeGuard AI - Statement of Work (SOW) & Proposal Risk Analyzer
Provides heuristic & LLM-assisted multi-factor risk assessment for freelance client proposals.
"""

import re
from typing import Dict, List, Any

# Common ambiguous terms and red flags in freelance/agency proposals
AMBIGUOUS_PATTERNS = [
    (r"\b(as needed|ad[\s-]hoc|when required)\b", "Vague Work Cadence", "high",
     "Specifies undefined availability. Define exact sprint hours or SLA response windows."),
    (r"\b(etc\.?|and so on|and more|various other)\b", "Open-Ended Scope", "high",
     "Open-ended lists create implicit expectations. Replace with an explicit, exhaustive list of deliverables."),
    (r"\b(fast|blazing fast|snappy|smooth)\b", "Subjective Performance Metric", "medium",
     "Subjective performance criteria can trigger endless rework. Define target Core Web Vitals or p95 response time in milliseconds."),
    (r"\b(user[\s-]friendly|modern|intuitive|clean)\b", "Subjective Design Requirement", "medium",
     "Aesthetic terms are subjective. Tie acceptance to Figma design sign-off rather than subjective adjectives."),
    (r"\b(unlimited revisions|until satisfied|to client satisfaction)\b", "Infinite Revision Trap", "critical",
     "Infinite revisions eliminate profit margins. Cap revisions to 2 rounds per deliverable, with additional rounds billed at standard hourly rates."),
    (r"\b(free maintenance|ongoing support|warranty)\b", "Unfunded Maintenance Obligation", "high",
     "Maintenance is a separate recurring retainer. Limit warranty to 14 days of bug fixes for original scope only."),
    (r"\b(scalable to millions|enterprise-ready|future-proof)\b", "Over-Engineered Architecture Expectation", "medium",
     "Scalability expectations without defined infrastructure budget. Specify target concurrent users and load limits."),
    (r"\b(integrat(e|ion) with (any|all|various) APIs)\b", "Unbounded Third-Party Integration", "high",
     "Third-party APIs vary widely in documentation and rate limits. Explicitly enumerate supported API endpoints and version numbers."),
    (r"\b(payment upon completion|net[\s-]60|net[\s-]90)\b", "Cash Flow / Payment Delay Risk", "high",
     "Deferred payment puts full credit risk on you. Mandate 30-50% upfront deposit and milestone-based invoicing on Net-15 terms."),
    (r"\b(indemnif(y|ication)|unlimited liability)\b", "Excessive Legal Liability", "critical",
     "Unlimited liability risks your personal assets. Cap total aggregate liability to the fees actually paid under the SOW.")
]

def detect_risk_clauses(text: str) -> List[Dict[str, Any]]:
    """Scan proposal text for known high-risk language, ambiguous terms, and scope traps."""
    findings = []
    seen = set()
    lines = text.split("\n")

    for pattern, title, severity, counter_measure in AMBIGUOUS_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            matched_phrase = m.group(0)
            key = (title, matched_phrase.lower())
            if key in seen:
                continue
            seen.add(key)

            # Find snippet context
            start_idx = max(0, m.start() - 40)
            end_idx = min(len(text), m.end() + 40)
            context_snippet = "..." + text[start_idx:end_idx].replace("\n", " ") + "..."

            findings.append({
                "title": title,
                "phrase": matched_phrase,
                "severity": severity,
                "recommendation": counter_measure,
                "snippet": context_snippet
            })

    return findings

def calculate_risk_score(findings: List[Dict[str, Any]], word_count: int) -> Dict[str, Any]:
    """Calculate normalized risk score (0-100) and recommended pricing buffer."""
    weights = {
        "critical": 25,
        "high": 15,
        "medium": 8,
        "low": 4
    }

    raw_score = sum(weights.get(f.get("severity", "medium"), 8) for f in findings)
    
    # Text length normalization factor
    normalized = min(100, max(5, int(raw_score)))
    
    if normalized < 25:
        tier = "Low Risk"
        color = "#10b981"
        suggested_buffer_pct = 10
        summary = "Proposal is relatively well-bounded. Standard 10% contingency buffer recommended."
    elif normalized < 55:
        tier = "Moderate Risk"
        color = "#f59e0b"
        suggested_buffer_pct = 20
        summary = "Several ambiguous deliverable terms detected. Recommended 20% price buffer and tighter acceptance criteria."
    elif normalized < 80:
        tier = "High Risk"
        color = "#f97316"
        suggested_buffer_pct = 35
        summary = "Significant scope creep vulnerabilities found. Redraft key sections and require minimum 35% risk buffer."
    else:
        tier = "Critical Risk"
        color = "#ef4444"
        suggested_buffer_pct = 50
        summary = "Hazardous contract terms (infinite revisions, undefined acceptance, or liability traps). Do not sign without complete restructuring."

    return {
        "score": normalized,
        "tier": tier,
        "color": color,
        "suggested_buffer_pct": suggested_buffer_pct,
        "summary": summary
    }

def analyze_proposal(text: str) -> Dict[str, Any]:
    """Execute complete analysis on proposal text."""
    clean_text = text.strip()
    words = len(clean_text.split())
    clauses = detect_risk_clauses(clean_text)
    risk_meta = calculate_risk_score(clauses, words)

    return {
        "word_count": words,
        "risk_meta": risk_meta,
        "clauses_detected": clauses,
        "clause_count": len(clauses),
        "critical_count": sum(1 for c in clauses if c["severity"] == "critical"),
        "high_count": sum(1 for c in clauses if c["severity"] == "high"),
        "medium_count": sum(1 for c in clauses if c["severity"] == "medium")
    }
