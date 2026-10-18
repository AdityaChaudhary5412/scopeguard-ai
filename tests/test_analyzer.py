"""
Unit Tests for ScopeGuard AI
Verifies risk analysis, ambiguity detection, quote calculation, and SOW generation.
"""

import unittest
import sys
import os

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer import detect_risk_clauses, calculate_risk_score, analyze_proposal
from engine import GemmaEngine
from sow_generator import calculate_quote, format_pricing_table

class TestScopeGuard(unittest.TestCase):

    def test_detect_ambiguous_clauses(self):
        text = "We expect blazing fast performance, unlimited revisions until satisfied, and payment upon completion."
        clauses = detect_risk_clauses(text)
        self.assertTrue(len(clauses) >= 3)
        
        titles = [c["title"] for c in clauses]
        self.assertIn("Subjective Performance Metric", titles)
        self.assertIn("Infinite Revision Trap", titles)
        self.assertIn("Cash Flow / Payment Delay Risk", titles)

    def test_risk_score_calculation(self):
        clauses = [
            {"title": "Infinite Revision Trap", "severity": "critical"},
            {"title": "Excessive Legal Liability", "severity": "critical"},
            {"title": "Vague Work Cadence", "severity": "high"}
        ]
        meta = calculate_risk_score(clauses, 50)
        self.assertGreaterEqual(meta["score"], 55)
        self.assertIn(meta["tier"], ["High Risk", "Critical Risk"])
        self.assertGreaterEqual(meta["suggested_buffer_pct"], 35)

    def test_pricing_quote_math(self):
        quote = calculate_quote(base_hours=40, hourly_rate=100.0, buffer_pct=25.0)
        self.assertEqual(quote["base_cost"], 4000.0)
        self.assertEqual(quote["contingency_cost"], 1000.0)
        self.assertEqual(quote["recommended_fixed_bid"], 5000.0)
        self.assertEqual(quote["payment_schedule"]["deposit_40pct"], 2000.0)
        self.assertEqual(quote["payment_schedule"]["alpha_30pct"], 1500.0)
        self.assertEqual(quote["payment_schedule"]["final_30pct"], 1500.0)

    def test_deterministic_fallback_sow(self):
        engine = GemmaEngine()
        analysis = analyze_proposal("Need an app with unlimited revisions and payment upon completion.")
        result = engine.generate_hardened_sow("Need an app with unlimited revisions and payment upon completion.", analysis)
        
        self.assertIn("Statement of Work", result["sow_markdown"])
        self.assertIn("Explicitly Out-of-Scope", result["sow_markdown"])
        self.assertIn("Payment Schedule", result["sow_markdown"])
        self.assertGreaterEqual(result["buffer_pct"], 20)

    def test_pricing_table_formatter(self):
        quote = calculate_quote(base_hours=50, hourly_rate=80.0, buffer_pct=20.0)
        table = format_pricing_table(quote)
        self.assertIn("Base Estimated Hours", table)
        self.assertIn("$4800.00", table)

if __name__ == "__main__":
    unittest.main()
