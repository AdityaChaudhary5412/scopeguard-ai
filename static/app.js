// ScopeGuard AI Frontend Application Logic

const SAMPLE_AMBIGUOUS_RFP = `Hi there,
We are looking for an experienced freelance developer to build an MVP for our new logistics platform.
The application needs to be blazing fast, modern, and super user-friendly.

Deliverables:
- Interactive dashboard for shipment tracking and analytics.
- Integration with various other APIs and payment gateways.
- Full responsive design, mobile optimization, etc.
- We expect you to work as needed to hit our launch deadline next month.
- We require unlimited revisions until satisfied before any invoice is approved.
- We offer payment upon completion on net-60 terms.
- Post-launch, you must provide free maintenance and ongoing support for 6 months.
- The contractor must agree to full indemnification and unlimited liability for any system downtime.

Let us know your estimate!`;

document.addEventListener("DOMContentLoaded", () => {
  const proposalInput = document.getElementById("proposalInput");
  const baseHoursInput = document.getElementById("baseHours");
  const hourlyRateInput = document.getElementById("hourlyRate");
  const gemmaModelSelect = document.getElementById("gemmaModel");
  
  const btnLoadSample = document.getElementById("btnLoadSample");
  const btnClear = document.getElementById("btnClear");
  const btnAudit = document.getElementById("btnAudit");
  const btnGenerate = document.getElementById("btnGenerate");
  const btnCopySOW = document.getElementById("btnCopySOW");
  
  const emptyState = document.getElementById("emptyState");
  const resultsContent = document.getElementById("resultsContent");
  
  const riskScoreEl = document.getElementById("riskScore");
  const riskTierEl = document.getElementById("riskTier");
  const bufferPctEl = document.getElementById("bufferPct");
  const bufferValueEl = document.getElementById("bufferValue");
  const fixedBidEl = document.getElementById("fixedBid");
  const depositSplitEl = document.getElementById("depositSplit");
  const clauseCountEl = document.getElementById("clauseCount");
  const criticalPillEl = document.getElementById("criticalPill");
  const clausesListEl = document.getElementById("clausesList");
  const engineTagEl = document.getElementById("engineTag");
  const sowPreviewEl = document.getElementById("sowPreview");
  const statusBadge = document.getElementById("statusBadge");

  // Check backend status
  fetch("/api/status")
    .then(res => res.json())
    .then(data => {
      if (data.local_ollama) {
        statusBadge.innerHTML = `🟢 Local Gemma Active (${data.model})`;
        statusBadge.className = "badge badge-privacy";
      } else {
        statusBadge.innerHTML = `🔒 Local Deterministic Mode (Privacy 100%)`;
      }
    })
    .catch(() => {
      statusBadge.innerHTML = `🔒 Offline Mode`;
    });

  // Load sample RFP
  btnLoadSample.addEventListener("click", () => {
    proposalInput.value = SAMPLE_AMBIGUOUS_RFP;
  });

  // Clear
  btnClear.addEventListener("click", () => {
    proposalInput.value = "";
    emptyState.classList.remove("hidden");
    resultsContent.classList.add("hidden");
  });

  // Audit Button
  btnAudit.addEventListener("click", async () => {
    const text = proposalInput.value.trim();
    if (!text) {
      alert("Please paste a proposal or click 'Load Sample Ambiguous RFP' first.");
      return;
    }

    btnAudit.disabled = true;
    btnAudit.innerHTML = "<span>⏳ Analyzing...</span>";

    try {
      const res = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();

      if (data.success) {
        renderAnalysis(data.analysis);
        sowPreviewEl.textContent = "Click 'Generate Hardened SOW' to formulate complete contractual deliverables, out-of-scope boundaries, and payment milestones.";
        engineTagEl.textContent = "Analysis Complete";
      } else {
        alert(data.error || "Analysis failed.");
      }
    } catch (err) {
      alert("Failed to communicate with local ScopeGuard server: " + err.message);
    } finally {
      btnAudit.disabled = false;
      btnAudit.innerHTML = "<span>🔍 Audit Proposal Risks</span>";
    }
  });

  // Generate SOW Button
  btnGenerate.addEventListener("click", async () => {
    const text = proposalInput.value.trim();
    if (!text) {
      alert("Please paste a proposal or click 'Load Sample Ambiguous RFP' first.");
      return;
    }

    const hours = parseFloat(baseHoursInput.value) || 40;
    const rate = parseFloat(hourlyRateInput.value) || 95;
    const model = gemmaModelSelect.value;

    btnGenerate.disabled = true;
    btnGenerate.innerHTML = "<span>⚡ Generating SOW...</span>";

    try {
      const res = await fetch("/api/generate-sow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, hours, rate, model })
      });
      const data = await res.json();

      if (data.success) {
        renderAnalysis(data.analysis);
        renderQuote(data.quote);
        engineTagEl.textContent = data.sow_result.engine;
        sowPreviewEl.textContent = data.full_document;
      } else {
        alert(data.error || "Generation failed.");
      }
    } catch (err) {
      alert("Failed to generate SOW: " + err.message);
    } finally {
      btnGenerate.disabled = false;
      btnGenerate.innerHTML = "<span>⚡ Generate Hardened SOW</span>";
    }
  });

  // Copy SOW
  btnCopySOW.addEventListener("click", () => {
    const content = sowPreviewEl.textContent;
    if (!content) return;
    navigator.clipboard.writeText(content).then(() => {
      const orig = btnCopySOW.textContent;
      btnCopySOW.textContent = "✅ Copied!";
      setTimeout(() => { btnCopySOW.textContent = orig; }, 2000);
    });
  });

  function renderAnalysis(analysis) {
    emptyState.classList.add("hidden");
    resultsContent.classList.remove("hidden");

    const meta = analysis.risk_meta;
    riskScoreEl.textContent = meta.score;
    riskScoreEl.style.color = meta.color;

    riskTierEl.textContent = meta.tier;
    riskTierEl.style.backgroundColor = meta.color + "25";
    riskTierEl.style.color = meta.color;

    bufferPctEl.textContent = `+${meta.suggested_buffer_pct}%`;
    clauseCountEl.textContent = analysis.clause_count;
    criticalPillEl.textContent = `${analysis.critical_count} Critical Red Flags`;

    // Render clauses
    clausesListEl.innerHTML = "";
    if (analysis.clauses_detected.length === 0) {
      clausesListEl.innerHTML = `<div class="clause-item"><p style="color:#10b981;">No explicit high-risk scope traps detected. Standard deliverables apply.</p></div>`;
    } else {
      analysis.clauses_detected.forEach(c => {
        const item = document.createElement("div");
        item.className = `clause-item ${c.severity}`;
        item.innerHTML = `
          <div class="clause-header">
            <span>${c.title}</span>
            <span class="clause-phrase">${escapeHtml(c.phrase)}</span>
          </div>
          <div class="clause-rec"><strong>Mitigation:</strong> ${escapeHtml(c.recommendation)}</div>
        `;
        clausesListEl.appendChild(item);
      });
    }

    // Default quote preview
    const hours = parseFloat(baseHoursInput.value) || 40;
    const rate = parseFloat(hourlyRateInput.value) || 95;
    const base = hours * rate;
    const contingency = base * (meta.suggested_buffer_pct / 100);
    const total = base + contingency;
    const deposit = total * 0.40;

    bufferValueEl.textContent = `+$${contingency.toFixed(2)} to quote`;
    fixedBidEl.textContent = `$${total.toFixed(2)}`;
    depositSplitEl.textContent = `Deposit: $${deposit.toFixed(2)} (40%)`;
  }

  function renderQuote(quote) {
    bufferPctEl.textContent = `+${quote.buffer_pct}%`;
    bufferValueEl.textContent = `+$${quote.contingency_cost.toFixed(2)} to quote`;
    fixedBidEl.textContent = `$${quote.recommended_fixed_bid.toFixed(2)}`;
    depositSplitEl.textContent = `Deposit: $${quote.payment_schedule.deposit_40pct.toFixed(2)} (40%)`;
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
