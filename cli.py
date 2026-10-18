"""
ScopeGuard AI - Command Line Interface (CLI)
Audit proposals, compute scope risk scores, and generate hardened Statements of Work.
"""

import sys
import argparse
from analyzer import analyze_proposal
from engine import GemmaEngine
from sow_generator import calculate_quote, format_pricing_table

def main():
    parser = argparse.ArgumentParser(
        description="ScopeGuard AI: Local-first Proposal & SOW Risk Auditor powered by Gemma"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Audit a proposal text file for ambiguity and risk clauses")
    audit_parser.add_argument("file", help="Path to proposal or RFP text file")

    # Command: sow
    sow_parser = subparsers.add_parser("sow", help="Audit proposal and generate a hardened SOW with pricing")
    sow_parser.add_argument("file", help="Path to proposal or RFP text file")
    sow_parser.add_argument("--hours", type=float, default=40.0, help="Estimated base hours (default: 40)")
    sow_parser.add_argument("--rate", type=float, default=95.0, help="Hourly rate in USD (default: $95/hr)")
    sow_parser.add_argument("--model", type=str, default="gemma2:2b", help="Gemma model name (default: gemma2:2b)")
    sow_parser.add_argument("--output", type=str, default=None, help="Save generated SOW markdown to file")

    # Command: status
    subparsers.add_parser("status", help="Check local Ollama / Gemma connection status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "status":
        engine = GemmaEngine()
        available = engine.is_ollama_available()
        print("=" * 60)
        print("ScopeGuard AI - Local Model Engine Status")
        print("=" * 60)
        if available:
            print("[+] Ollama Local Service: ACTIVE & REACHABLE")
            print(f"[+] Default Target Model: {engine.model}")
            print("[+] Privacy Level: 100% Local Inference (Zero External Network Calls)")
        else:
            print("[-] Ollama Local Service: NOT DETECTED (port 11434 unreachable)")
            print("[*] ScopeGuard will operate in Deterministic Heuristic Engine Mode.")
            print("[*] To activate full Gemma generation: run 'ollama run gemma2:2b'")
        sys.exit(0)

    # Read input file
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            proposal_text = f.read()
    except Exception as e:
        print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_proposal(proposal_text)
    risk_meta = analysis["risk_meta"]

    if args.command == "audit":
        print("=" * 65)
        print("ScopeGuard AI - Proposal Risk Audit Report")
        print("=" * 65)
        print(f"File:               {args.file}")
        print(f"Word Count:         {analysis['word_count']}")
        print(f"Risk Score:         {risk_meta['score']} / 100")
        print(f"Risk Tier:          {risk_meta['tier']}")
        print(f"Suggested Buffer:   +{risk_meta['suggested_buffer_pct']}%")
        print(f"Summary:            {risk_meta['summary']}")
        print("-" * 65)
        print(f"Detected Risk Clauses ({analysis['clause_count']}):")
        for i, clause in enumerate(analysis["clauses_detected"], 1):
            print(f"\n{i}. [{clause['severity'].upper()}] {clause['title']}")
            print(f"   Matched Phrase: '{clause['phrase']}'")
            print(f"   Context:        {clause['snippet']}")
            print(f"   Mitigation:     {clause['recommendation']}")
        print("=" * 65)

    elif args.command == "sow":
        engine = GemmaEngine(model=args.model)
        sow_result = engine.generate_hardened_sow(proposal_text, analysis)
        quote = calculate_quote(args.hours, args.rate, sow_result["buffer_pct"])
        pricing_table = format_pricing_table(quote)

        full_output = f"{sow_result['sow_markdown']}\n\n## 6. Financial Estimate & Risk Pricing Schedule\n{pricing_table}"

        if args.output:
            with open(args.output, "w", encoding="utf-8") as out_f:
                out_f.write(full_output)
            print(f"[+] Hardened SOW written to: {args.output}")
        else:
            print(full_output)

if __name__ == "__main__":
    main()
