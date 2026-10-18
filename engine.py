"""
ScopeGuard AI - Local Gemma Model Engine
Interfaces with local open-weight models (Gemma 2B / 9B via Ollama or custom local server)
with deterministic, zero-dependency offline fallback.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma2:2b"

GEMMA_AUDIT_PROMPT = """You are ScopeGuard AI, an expert freelance legal and scope auditor.
Analyze the following client proposal/RFP and generate a hardened, professional Statement of Work (SOW).

Client Request:
{proposal_text}

Detected Risk Score: {risk_score}/100 ({risk_tier})
Ambiguities Detected: {findings_summary}

Instructions:
1. Identify all vague deliverables and rewrite them with measurable acceptance criteria.
2. Formulate an explicit "Out of Scope" section preventing unpaid scope creep.
3. Define a phased payment milestone schedule (Deposit, Alpha, Final Sign-off).
4. Restrict revisions to 2 rounds per milestone.

Format your response in structured Markdown with sections:
# Hardened Statement of Work (SOW)
## 1. Project Objective & Core Deliverables (Bounded)
## 2. Explicitly Out-of-Scope (Add-on Items)
## 3. Review & Acceptance Criteria (Strict)
## 4. Payment Milestones & Risk Contingency
## 5. Change Order Policy
"""

class GemmaEngine:
    def __init__(self, endpoint: str = DEFAULT_OLLAMA_ENDPOINT, model: str = DEFAULT_MODEL):
        self.endpoint = endpoint
        self.model = model

    def is_ollama_available(self) -> bool:
        """Check if local Ollama service is reachable."""
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "ScopeGuard-AI"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return response.status == 200
        except Exception:
            return False

    def query_gemma(self, prompt: str, timeout: int = 45) -> Optional[str]:
        """Query local Gemma instance via Ollama REST API."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "ScopeGuard-AI"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    body = json.loads(response.read().decode("utf-8"))
                    return body.get("response", "")
        except Exception as e:
            # Fall back cleanly
            return None

    def generate_hardened_sow(self, proposal_text: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hardened SOW using Gemma if available, or deterministic template engine."""
        risk_meta = analysis.get("risk_meta", {})
        clauses = analysis.get("clauses_detected", [])
        
        findings_summary = ", ".join([f"{c['title']} ('{c['phrase']}')" for c in clauses[:5]])
        if not findings_summary:
            findings_summary = "None detected."

        prompt = GEMMA_AUDIT_PROMPT.format(
            proposal_text=proposal_text,
            risk_score=risk_meta.get("score", 50),
            risk_tier=risk_meta.get("tier", "Moderate Risk"),
            findings_summary=findings_summary
        )

        model_used = f"Local Gemma ({self.model})"
        generated_markdown = None

        if self.is_ollama_available():
            generated_markdown = self.query_gemma(prompt)

        if not generated_markdown:
            # Deterministic, rule-based fallback generator
            model_used = "ScopeGuard Local Heuristic Engine (Deterministic Mode)"
            generated_markdown = self._generate_fallback_sow(proposal_text, analysis)

        return {
            "sow_markdown": generated_markdown,
            "engine": model_used,
            "is_local_gemma_active": self.is_ollama_available(),
            "buffer_pct": risk_meta.get("suggested_buffer_pct", 20)
        }

    def _generate_fallback_sow(self, proposal_text: str, analysis: Dict[str, Any]) -> str:
        """High-grade deterministic SOW generator ensuring 100% offline availability."""
        risk_meta = analysis.get("risk_meta", {})
        clauses = analysis.get("clauses_detected", [])
        buffer = risk_meta.get("suggested_buffer_pct", 20)
        
        # Extract title or first sentence
        first_line = proposal_text.strip().split("\n")[0][:80]
        if not first_line:
            first_line = "Custom Software Development & Implementation"

        risk_warnings = "\n".join([
            f"- **{c['title']}**: Detected '{c['phrase']}'. *Counter-measure:* {c['recommendation']}"
            for c in clauses
        ]) if clauses else "- No high-risk clauses detected. Standard commercial terms apply."

        sow = f"""# Statement of Work (SOW): {first_line}

**Document Version:** 1.0 (Hardened ScopeGuard Draft)  
**Contract Risk Rating:** {risk_meta.get('tier', 'Moderate')} ({risk_meta.get('score', 0)}/100)  
**Recommended Contingency Buffer:** {buffer}%  
**Governing Principle:** Zero-Surprise Fixed Deliverables with Change-Order Protection  

---

## 1. Project Objective & Bounded Deliverables
The contractor will deliver the core functionality strictly defined below:
1. **Milestone 1 - Technical Architecture & Data Schema:** Complete system architecture specification and interface mockups.
2. **Milestone 2 - Core Engine & Functional Implementation:** Development of primary business logic and specified API integrations.
3. **Milestone 3 - Staging Verification & Handover:** Deployment to staging environment, verification testing, and delivery of documentation.

*Acceptance Criteria:* Deliverables are deemed accepted once functional testing passes against pre-agreed acceptance test scripts. Client must provide written feedback within five (5) business days of milestone handover.

---

## 2. Explicitly Out-of-Scope (Add-on Items)
To preserve timeline and budget predictability, the following items are strictly excluded from this baseline agreement:
- Migration or cleanup of legacy, corrupted, or unformatted client data.
- Integration with third-party APIs not explicitly enumerated in Section 1.
- Native mobile application builds (unless explicitly contracted).
- Ongoing post-launch maintenance, monitoring, or 24/7 SLA availability (available via separate Monthly Retainer).
- Unlimited design revisions or substantive structural changes after wireframe sign-off.

---

## 3. Revision Policy & Quality Guard
- **Revision Allowance:** Up to two (2) consolidated rounds of feedback per milestone deliverable.
- **Feedback Format:** Feedback must be collated in a single centralized document with prioritized items.
- **Scope Creep Mechanism:** Requests deviating from the baseline specifications will be estimated as a formal **Change Order** with additional cost and timeline extensions before implementation.

---

## 4. Payment Schedule & Milestones
All invoices are payable on Net-15 terms upon milestone completion:
- **Phase 1 (Kickoff Deposit):** 40% due prior to project commencement.
- **Phase 2 (Alpha Delivery):** 30% due upon delivery of functional prototype.
- **Phase 3 (Final Sign-off):** 30% (incorporating {buffer}% contingency buffer) due upon staging sign-off prior to production credential handover.

---

## 5. Risk Clause Mitigations Identified During Audit
{risk_warnings}

---
*Generated by ScopeGuard AI — 100% Local Inference, Zero Data Leakage.*
"""
        return sow.strip()
