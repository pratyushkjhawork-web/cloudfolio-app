// Relative path — works because the backend now serves this frontend
// directly (same origin, no CORS needed). If you ever split them again
// (e.g. frontend on S3/CloudFront, backend on EC2), change this back to
// an absolute URL like "http://<ec2-ip>:8000/api".
const API_BASE = "/api";

let currentResumeId = null; // set after first successful save; used for edit + PDF download
let itemCounter = 0; // gives each dynamically-added textarea a unique id, so AI Improve can target it

// ---------- Repeatable section helpers (Experience / Projects / Education) ----------

function addExperience() {
  const container = document.getElementById("experience-list");
  const uid = `exp-desc-${itemCounter++}`;
  const div = document.createElement("div");
  div.className = "repeatable-item experience-item";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="this.parentElement.remove(); renderPreview();">✕ remove</button>
    <input class="exp-title" type="text" placeholder="Job Title" oninput="renderPreview()" />
    <input class="exp-company" type="text" placeholder="Company" oninput="renderPreview()" />
    <input class="exp-duration" type="text" placeholder="Duration (e.g. Jun 2025 - Aug 2025)" oninput="renderPreview()" />
    <label style="margin-top:4px;">
      Description
      <button type="button" class="ai-btn" data-target="${uid}" data-type="experience">✨ AI Improve</button>
    </label>
    <textarea id="${uid}" class="exp-description" rows="2" placeholder="What did you do?" oninput="renderPreview()"></textarea>
    <div id="${uid}-ai-diff" class="ai-diff-box" style="display:none;"></div>
  `;
  container.appendChild(div);
  attachAiButtonHandlers(div);
}

function addProject() {
  const container = document.getElementById("projects-list");
  const uid = `proj-desc-${itemCounter++}`;
  const div = document.createElement("div");
  div.className = "repeatable-item project-item";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="this.parentElement.remove(); renderPreview();">✕ remove</button>
    <input class="proj-title" type="text" placeholder="Project Title" oninput="renderPreview()" />
    <input class="proj-link" type="text" placeholder="Link (optional)" oninput="renderPreview()" />
    <label style="margin-top:4px;">
      Description
      <button type="button" class="ai-btn" data-target="${uid}" data-type="experience">✨ AI Improve</button>
    </label>
    <textarea id="${uid}" class="proj-description" rows="2" placeholder="What does it do?" oninput="renderPreview()"></textarea>
    <div id="${uid}-ai-diff" class="ai-diff-box" style="display:none;"></div>
  `;
  container.appendChild(div);
  attachAiButtonHandlers(div);
}

// Wires up AI Improve buttons inside a given container (used for dynamically
// added experience/project items, since they don't exist at page-load time
// when the static querySelectorAll('.ai-btn') binding below runs).
function attachAiButtonHandlers(container) {
  container.querySelectorAll(".ai-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      requestAiSuggestion(btn.dataset.target, btn.dataset.type);
    });
  });
}

function addEducation() {
  const container = document.getElementById("education-list");
  const div = document.createElement("div");
  div.className = "repeatable-item education-item";
  div.innerHTML = `
    <button type="button" class="remove-btn" onclick="this.parentElement.remove(); renderPreview();">✕ remove</button>
    <input class="edu-degree" type="text" placeholder="Degree (e.g. B.Tech CSE)" oninput="renderPreview()" />
    <input class="edu-institution" type="text" placeholder="Institution" oninput="renderPreview()" />
    <input class="edu-duration" type="text" placeholder="Duration (e.g. 2024 - 2028)" oninput="renderPreview()" />
  `;
  container.appendChild(div);
}

// ---------- Collect form data into the shape the API expects ----------

function collectFormData() {
  const experience = Array.from(document.querySelectorAll(".experience-item")).map(el => ({
    title: el.querySelector(".exp-title").value,
    company: el.querySelector(".exp-company").value,
    duration: el.querySelector(".exp-duration").value,
    description: el.querySelector(".exp-description").value,
  }));

  const projects = Array.from(document.querySelectorAll(".project-item")).map(el => ({
    title: el.querySelector(".proj-title").value,
    description: el.querySelector(".proj-description").value,
    link: el.querySelector(".proj-link").value || null,
  }));

  const education = Array.from(document.querySelectorAll(".education-item")).map(el => ({
    degree: el.querySelector(".edu-degree").value,
    institution: el.querySelector(".edu-institution").value,
    duration: el.querySelector(".edu-duration").value,
  }));

  const skillsRaw = document.getElementById("skills").value;
  const skills = skillsRaw.split(",").map(s => s.trim()).filter(Boolean);

  return {
    full_name: document.getElementById("full_name").value,
    email: document.getElementById("email").value,
    phone: document.getElementById("phone").value,
    location: document.getElementById("location").value,
    linkedin: document.getElementById("linkedin").value,
    github: document.getElementById("github").value,
    summary: document.getElementById("summary").value,
    skills,
    experience,
    projects,
    education,
  };
}

// ---------- Live preview ----------

function renderPreview() {
  const data = collectFormData();
  const preview = document.getElementById("preview");

  if (!data.full_name && !data.summary && data.experience.length === 0) {
    preview.innerHTML = `<p class="placeholder">Fill the form to see your resume preview here.</p>`;
    return;
  }

  let html = `<h3 class="r-name">${escapeHtml(data.full_name || "Your Name")}</h3>`;

  const contactBits = [data.email, data.phone, data.location, data.linkedin, data.github].filter(Boolean);
  html += `<div class="r-contact">${contactBits.map(escapeHtml).join(" &nbsp;|&nbsp; ")}</div>`;

  if (data.summary) {
    html += `<div class="r-section-title">Professional Summary</div><p>${escapeHtml(data.summary)}</p>`;
  }

  if (data.skills.length) {
    html += `<div class="r-section-title">Skills</div><p>${data.skills.map(escapeHtml).join(" • ")}</p>`;
  }

  if (data.experience.length) {
    html += `<div class="r-section-title">Experience</div>`;
    data.experience.forEach(e => {
      html += `<div class="r-item-title">${escapeHtml(e.title)} — ${escapeHtml(e.company)}</div>`;
      if (e.duration) html += `<div class="r-item-meta">${escapeHtml(e.duration)}</div>`;
      if (e.description) html += `<p>${escapeHtml(e.description)}</p>`;
    });
  }

  if (data.projects.length) {
    html += `<div class="r-section-title">Projects</div>`;
    data.projects.forEach(p => {
      const titleLine = p.link ? `${escapeHtml(p.title)} (${escapeHtml(p.link)})` : escapeHtml(p.title);
      html += `<div class="r-item-title">${titleLine}</div>`;
      if (p.description) html += `<p>${escapeHtml(p.description)}</p>`;
    });
  }

  if (data.education.length) {
    html += `<div class="r-section-title">Education</div>`;
    data.education.forEach(ed => {
      html += `<div class="r-item-title">${escapeHtml(ed.degree)} — ${escapeHtml(ed.institution)}</div>`;
      if (ed.duration) html += `<div class="r-item-meta">${escapeHtml(ed.duration)}</div>`;
    });
  }

  preview.innerHTML = html;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.innerText = str ?? "";
  return div.innerHTML;
}

// Wire up live preview on the top-level fields too
["full_name", "email", "phone", "location", "linkedin", "github", "summary", "skills"]
  .forEach(id => document.getElementById(id).addEventListener("input", renderPreview));

// ---------- API calls ----------

async function saveResume() {
  const statusEl = document.getElementById("status-msg");
  const data = collectFormData();

  try {
    const url = currentResumeId
      ? `${API_BASE}/resumes/${currentResumeId}`
      : `${API_BASE}/resumes`;
    const method = currentResumeId ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error(`Server responded ${res.status}`);

    const saved = await res.json();
    currentResumeId = saved.id;
    document.getElementById("pdf-btn").disabled = false;
    document.getElementById("jd-match-btn").disabled = false;
    statusEl.textContent = `Saved (resume #${saved.id}).`;
  } catch (err) {
    statusEl.textContent = `Save failed: ${err.message}. Is the backend running?`;
    statusEl.style.color = "#b3261e";
  }
}

async function downloadPdf() {
  if (!currentResumeId) return;
  const res = await fetch(`${API_BASE}/resumes/${currentResumeId}/pdf`);
  if (!res.ok) {
    alert("Could not generate PDF.");
    return;
  }
  const blob = await res.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "resume.pdf";
  link.click();
}

// Simple word-level diff (LCS-based). Good enough for short resume text,
// not meant to be a general-purpose diff library.
function wordDiff(oldText, newText) {
  const oldWords = oldText.split(/(\s+)/);
  const newWords = newText.split(/(\s+)/);

  const m = oldWords.length, n = newWords.length;
  const lcs = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      lcs[i][j] = oldWords[i] === newWords[j]
        ? lcs[i + 1][j + 1] + 1
        : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }

  let i = 0, j = 0;
  const parts = [];
  while (i < m && j < n) {
    if (oldWords[i] === newWords[j]) {
      parts.push({ type: "same", text: oldWords[i] });
      i++; j++;
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      parts.push({ type: "removed", text: oldWords[i] });
      i++;
    } else {
      parts.push({ type: "added", text: newWords[j] });
      j++;
    }
  }
  while (i < m) { parts.push({ type: "removed", text: oldWords[i] }); i++; }
  while (j < n) { parts.push({ type: "added", text: newWords[j] }); j++; }

  return parts;
}

function renderDiffHtml(parts) {
  return parts.map(p => {
    const escaped = escapeHtml(p.text);
    if (p.type === "added") return `<span class="diff-added">${escaped}</span>`;
    if (p.type === "removed") return `<span class="diff-removed">${escaped}</span>`;
    return escaped;
  }).join("");
}

async function requestAiSuggestion(targetId, fieldType) {
  const textarea = document.getElementById(targetId);
  const original = textarea.value;
  const diffBox = document.getElementById(`${targetId}-ai-diff`);
  if (!original.trim()) return;

  const button = document.querySelector(`.ai-btn[data-target="${targetId}"]`);
  const originalLabel = button.textContent;
  button.textContent = "Thinking...";
  button.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/ai/suggest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: original, field_type: fieldType }),
    });
    const result = await res.json();

    if (diffBox) {
      diffBox.style.display = "block";

      if (result.suggestion && result.suggestion !== original) {
        // Real change — show the diff, apply it, flash the textarea green
        const parts = wordDiff(original, result.suggestion);
        diffBox.className = "ai-diff-box";
        diffBox.innerHTML = `<span class="diff-label">AI change applied</span>${renderDiffHtml(parts)}`;

        textarea.value = result.suggestion;
        textarea.classList.remove("ai-updated-flash");
        void textarea.offsetWidth; // restart animation
        textarea.classList.add("ai-updated-flash");
        renderPreview();
      } else {
        // No change — likely no API key configured, or the model returned identical text
        diffBox.className = "ai-diff-box no-change";
        diffBox.innerHTML = `<span class="diff-label">No change made</span>Text was returned unchanged — check that GEMINI_API_KEY is set on the backend.`;
      }
    }
  } catch (err) {
    if (diffBox) {
      diffBox.style.display = "block";
      diffBox.className = "ai-diff-box no-change";
      diffBox.innerHTML = `<span class="diff-label">Request failed</span>Could not reach the AI endpoint — check the backend is running.`;
    }
  } finally {
    button.textContent = originalLabel;
    button.disabled = false;
  }
}

document.querySelectorAll(".ai-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    requestAiSuggestion(btn.dataset.target, btn.dataset.type);
  });
});

// ---------- Job Description matching ----------

async function matchJobDescription() {
  if (!currentResumeId) return;
  const jdText = document.getElementById("jd-text").value.trim();
  const resultBox = document.getElementById("jd-result");
  const button = document.getElementById("jd-match-btn");

  if (!jdText) {
    alert("Paste a job description first.");
    return;
  }

  const originalLabel = button.textContent;
  button.textContent = "Analyzing...";
  button.disabled = true;
  resultBox.style.display = "block";
  resultBox.innerHTML = `<p class="placeholder">Analyzing against the job description...</p>`;

  try {
    const res = await fetch(`${API_BASE}/ai/match-jd`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_id: currentResumeId, job_description: jdText }),
    });
    const result = await res.json();
    renderJdResult(result);
  } catch (err) {
    resultBox.innerHTML = `<p class="placeholder">Request failed — check the backend is running.</p>`;
  } finally {
    button.textContent = originalLabel;
    button.disabled = false;
  }
}

function renderJdResult(result) {
  const resultBox = document.getElementById("jd-result");
  const score = result.match_score ?? 0;

  let scoreColor = "#b3261e"; // red
  if (score >= 75) scoreColor = "#2a7a2a"; // green
  else if (score >= 45) scoreColor = "#a67c1e"; // amber

  let html = `
    <div class="jd-score" style="color:${scoreColor};">${score}<span style="font-size:14px;">/100 match</span></div>
  `;

  if (result.matched_keywords && result.matched_keywords.length) {
    html += `<div class="jd-section-title">Matched</div>`;
    html += `<div class="jd-tags">${result.matched_keywords.map(k => `<span class="tag tag-good">${escapeHtml(k)}</span>`).join("")}</div>`;
  }

  if (result.missing_keywords && result.missing_keywords.length) {
    html += `<div class="jd-section-title">Missing</div>`;
    html += `<div class="jd-tags">${result.missing_keywords.map(k => `<span class="tag tag-missing">${escapeHtml(k)}</span>`).join("")}</div>`;
  }

  if (result.suggestions && result.suggestions.length) {
    html += `<div class="jd-section-title">Suggestions</div>`;
    html += `<ul class="jd-suggestions">${result.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul>`;
  }

  resultBox.innerHTML = html;
}
