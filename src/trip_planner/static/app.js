/**
 * Wanderlust AI — Trip Planner Client Application
 * Handles API interaction, markdown parsing, and interactive UI states.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const form = document.getElementById("planForm");
  const destinationInput = document.getElementById("destinationInput");
  const daysInput = document.getElementById("daysInput");
  const decrementDays = document.getElementById("decrementDays");
  const incrementDays = document.getElementById("incrementDays");
  const interestsInput = document.getElementById("interestsInput");
  const submitBtn = document.getElementById("submitBtn");
  const btnLabel = document.getElementById("btnLabel");
  
  const progressCard = document.getElementById("progressCard");
  const progressTitle = document.getElementById("progressTitle");
  const progressSubtitle = document.getElementById("progressSubtitle");
  
  const dossierContent = document.getElementById("dossierContent");
  const dossierUpdated = document.getElementById("dossierUpdated");
  
  const copyBtn = document.getElementById("copyMarkdownBtn");
  const downloadBtn = document.getElementById("downloadMarkdownBtn");
  const printBtn = document.getElementById("printBtn");
  
  const systemStatusDot = document.getElementById("systemStatusDot");
  const systemStatusText = document.getElementById("systemStatusText");
  const modelBadge = document.getElementById("modelBadge");
  const presetPills = document.querySelectorAll(".preset-pill");

  let rawDossierMarkdown = "";

  // 1. Check System Status & Model on Load
  async function checkSystemStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        systemStatusDot.style.backgroundColor = "#10B981";
        systemStatusText.textContent = data.search_enabled ? "Crew Ready (Live Search On)" : "Crew Ready (Offline LLM)";
        modelBadge.textContent = data.model || "gemini-2.0-flash";
      } else {
        throw new Error();
      }
    } catch {
      systemStatusDot.style.backgroundColor = "#EAB308";
      systemStatusText.textContent = "Server Connected";
    }
  }

  // 2. Fetch Previously Generated Plan
  async function fetchLastPlan() {
    try {
      const res = await fetch("/api/last-plan");
      const data = await res.json();
      
      if (data.exists && data.content) {
        rawDossierMarkdown = data.content;
        renderMarkdown(data.content);
        dossierUpdated.textContent = `Generated: ${data.updated_at || "Recent"}`;
      } else {
        dossierUpdated.textContent = "No saved plan found";
      }
    } catch (err) {
      console.warn("Could not load last plan:", err);
      dossierUpdated.textContent = "Ready for new plan";
    }
  }

  // 3. Render Markdown into Clean HTML
  function renderMarkdown(mdText) {
    if (typeof marked !== "undefined") {
      dossierContent.innerHTML = marked.parse(mdText);
    } else {
      dossierContent.innerText = mdText;
    }
  }

  // 4. Stepper Buttons
  decrementDays.addEventListener("click", () => {
    const val = parseInt(daysInput.value, 10) || 5;
    if (val > 1) daysInput.value = val - 1;
  });

  incrementDays.addEventListener("click", () => {
    const val = parseInt(daysInput.value, 10) || 5;
    if (val < 30) daysInput.value = val + 1;
  });

  // 5. Preset Pills Interaction
  presetPills.forEach(pill => {
    pill.addEventListener("click", () => {
      presetPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");

      destinationInput.value = pill.dataset.dest;
      daysInput.value = pill.dataset.days;
      interestsInput.value = pill.dataset.interests;

      const budgetRadio = document.querySelector(`input[name="budgetTier"][value="${pill.dataset.budget}"]`);
      if (budgetRadio) budgetRadio.checked = true;
    });
  });

  // 6. Handle Form Submission & Execution
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const selectedBudget = document.querySelector('input[name="budgetTier"]:checked')?.value || "mid";
    const payload = {
      destination: destinationInput.value.trim(),
      number_of_days: parseInt(daysInput.value, 10) || 5,
      budget_tier: selectedBudget,
      interests: interestsInput.value.trim(),
    };

    if (!payload.destination) {
      alert("Please specify a destination.");
      return;
    }

    // Set Loading UI State
    submitBtn.disabled = true;
    submitBtn.classList.add("loading");
    btnLabel.textContent = "Architecting Expedition...";
    
    // Reveal Progress Tracker
    progressCard.classList.remove("hidden");
    progressTitle.textContent = `Deploying Specialists to ${payload.destination}`;
    progressSubtitle.textContent = "Destination Researcher is investigating authentic cultural sights and dining...";
    
    // Smooth scroll down to progress on mobile
    if (window.innerWidth < 960) {
      progressCard.scrollIntoView({ behavior: "smooth" });
    }

    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned error (${response.status})`);
      }

      const result = await response.json();
      rawDossierMarkdown = result.markdown;
      renderMarkdown(result.markdown);
      dossierUpdated.textContent = `Generated: ${result.generated_at}`;

      // Progress complete message
      progressTitle.textContent = "Expedition Dossier Complete!";
      progressSubtitle.textContent = `All 3 specialist tasks completed for ${result.destination}.`;
      
      // Auto-hide progress after a few seconds
      setTimeout(() => {
        progressCard.classList.add("hidden");
      }, 4000);

    } catch (err) {
      console.error("Execution failed:", err);
      alert(`Expedition Planning Error:\n${err.message}`);
      progressCard.classList.add("hidden");
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove("loading");
      btnLabel.textContent = "Kickoff Multi-Agent Crew";
    }
  });

  // 7. Copy Markdown
  copyBtn.addEventListener("click", async () => {
    if (!rawDossierMarkdown) {
      alert("No dossier available to copy.");
      return;
    }
    try {
      await navigator.clipboard.writeText(rawDossierMarkdown);
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = "<span>✓</span> Copied!";
      setTimeout(() => {
        copyBtn.innerHTML = originalText;
      }, 2000);
    } catch {
      alert("Failed to copy to clipboard.");
    }
  });

  // 8. Download Dossier
  downloadBtn.addEventListener("click", () => {
    if (!rawDossierMarkdown) {
      alert("No dossier available to download.");
      return;
    }
    const blob = new Blob([rawDossierMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trip_plan_${(destinationInput.value || "expedition").toLowerCase().replace(/[^a-z0-9]/g, "_")}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // 9. Print / PDF Export
  printBtn.addEventListener("click", () => {
    window.print();
  });

  // Initialize
  checkSystemStatus();
  fetchLastPlan();
});
