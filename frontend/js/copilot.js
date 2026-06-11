// frontend/js/copilot.js

import { API } from './api.js';
import { state, showToast, registerTab } from './shared.js';

// ── DOM References ─────────────────────────────────────────────────────────

const leadSearchInput   = document.getElementById('copilot-lead-search');
const leadListContainer = document.getElementById('copilot-lead-list');
const selectedLeadInfo  = document.getElementById('copilot-selected-lead');
const noLeadPlaceholder = document.getElementById('copilot-no-lead');
const toolsPanel        = document.getElementById('copilot-tools-panel');

// Suggest Action
const suggestBtn    = document.getElementById('copilot-suggest-btn');
const suggestResult = document.getElementById('copilot-suggest-result');
const suggestLoader = document.getElementById('copilot-suggest-loader');

// Draft Message
const draftToneSelect = document.getElementById('copilot-draft-tone');
const draftBtn        = document.getElementById('copilot-draft-btn');
const draftResult     = document.getElementById('copilot-draft-result');
const draftLoader     = document.getElementById('copilot-draft-loader');
const draftCopyBtn    = document.getElementById('copilot-draft-copy-btn');

// Score Leads
const scoreBtn    = document.getElementById('copilot-score-btn');
const scoreResult = document.getElementById('copilot-score-result');
const scoreLoader = document.getElementById('copilot-score-loader');
const scoreTbody  = document.getElementById('copilot-score-tbody');

let selectedCopilotLeadId = null;

// ── Lead List Rendering ────────────────────────────────────────────────────

function renderLeadList(filter = '') {
  if (!leadListContainer) return;
  const filtered = state.leads.filter(l =>
    l.name.toLowerCase().includes(filter.toLowerCase()) ||
    l.phone.includes(filter)
  );

  if (filtered.length === 0) {
    leadListContainer.innerHTML = `
      <div class="copilot-empty-list">
        <i class="fa-solid fa-search"></i>
        <p>No leads found</p>
      </div>`;
    return;
  }

  leadListContainer.innerHTML = filtered.map(lead => `
    <div class="copilot-lead-item ${lead.id === selectedCopilotLeadId ? 'active' : ''}"
         data-id="${lead.id}">
      <div class="copilot-lead-name">${lead.name}</div>
      <div class="copilot-lead-meta">
        <span class="badge badge-${lead.stage.toLowerCase()}">${lead.stage}</span>
        <span class="copilot-lead-source">${lead.source || 'N/A'}</span>
      </div>
    </div>
  `).join('');

  // Attach click handlers
  leadListContainer.querySelectorAll('.copilot-lead-item').forEach(item => {
    item.addEventListener('click', () => {
      const id = parseInt(item.dataset.id, 10);
      selectLead(id);
    });
  });
}

function selectLead(leadId) {
  selectedCopilotLeadId = leadId;
  const lead = state.leads.find(l => l.id === leadId);
  if (!lead) return;

  // Show tools, hide placeholder
  if (noLeadPlaceholder) noLeadPlaceholder.style.display = 'none';
  if (toolsPanel) toolsPanel.style.display = 'block';

  // Update selected lead info
  if (selectedLeadInfo) {
    const age = Math.floor((Date.now() - new Date(lead.created_at).getTime()) / 86400000);
    selectedLeadInfo.innerHTML = `
      <div class="copilot-lead-detail">
        <h4>${lead.name}</h4>
        <div class="copilot-lead-tags">
          <span class="badge badge-${lead.stage.toLowerCase()}">${lead.stage}</span>
          <span class="badge badge-info">${lead.source || 'N/A'}</span>
          <span class="badge badge-default">${age}d old</span>
        </div>
        ${lead.notes ? `<p class="copilot-lead-notes">${lead.notes}</p>` : ''}
      </div>`;
    selectedLeadInfo.style.display = 'block';
  }

  // Clear previous results
  clearResults();
  renderLeadList(leadSearchInput?.value || '');
}

function clearResults() {
  if (suggestResult) { suggestResult.style.display = 'none'; suggestResult.innerHTML = ''; }
  if (draftResult) { draftResult.style.display = 'none'; draftResult.innerHTML = ''; }
  if (draftCopyBtn) draftCopyBtn.style.display = 'none';
}

// ── Suggest Next Action ────────────────────────────────────────────────────

async function handleSuggestAction() {
  if (!selectedCopilotLeadId) {
    showToast('Please select a lead first', 'warning');
    return;
  }

  suggestBtn.disabled = true;
  suggestLoader.style.display = 'flex';
  suggestResult.style.display = 'none';

  try {
    const res = await API.suggestAction(selectedCopilotLeadId);

    const urgencyColors = {
      high: 'var(--danger)',
      medium: 'var(--warning)',
      low: 'var(--success)'
    };
    const urgencyIcons = {
      high: 'fa-circle-exclamation',
      medium: 'fa-clock',
      low: 'fa-circle-check'
    };

    suggestResult.innerHTML = `
      <div class="copilot-action-card">
        <div class="copilot-urgency" style="color: ${urgencyColors[res.urgency] || 'var(--text-secondary)'}">
          <i class="fa-solid ${urgencyIcons[res.urgency] || 'fa-circle'}"></i>
          <span>${(res.urgency || 'medium').toUpperCase()} PRIORITY</span>
        </div>
        <div class="copilot-action-text">
          <strong>Recommended Action:</strong>
          <p>${res.action}</p>
        </div>
        <div class="copilot-reasoning">
          <strong>Reasoning:</strong>
          <p>${res.reasoning}</p>
        </div>
      </div>`;
    suggestResult.style.display = 'block';
  } catch (err) {
    showToast(`Copilot error: ${err.message}`, 'error');
  } finally {
    suggestBtn.disabled = false;
    suggestLoader.style.display = 'none';
  }
}

// ── Draft Message ──────────────────────────────────────────────────────────

async function handleDraftMessage() {
  if (!selectedCopilotLeadId) {
    showToast('Please select a lead first', 'warning');
    return;
  }

  const tone = draftToneSelect?.value || 'professional';
  draftBtn.disabled = true;
  draftLoader.style.display = 'flex';
  draftResult.style.display = 'none';
  draftCopyBtn.style.display = 'none';

  try {
    const res = await API.draftMessage(selectedCopilotLeadId, tone);

    draftResult.innerHTML = `
      <div class="copilot-draft-card">
        <div class="copilot-draft-subject">
          <strong>Subject:</strong> ${res.subject}
        </div>
        <div class="copilot-draft-body">${res.body}</div>
        <div class="copilot-draft-tone-label">
          <i class="fa-solid fa-palette"></i> Tone: ${res.tone_used}
        </div>
      </div>`;
    draftResult.style.display = 'block';
    draftCopyBtn.style.display = 'inline-flex';
  } catch (err) {
    showToast(`Copilot error: ${err.message}`, 'error');
  } finally {
    draftBtn.disabled = false;
    draftLoader.style.display = 'none';
  }
}

function handleCopyDraft() {
  const bodyEl = draftResult?.querySelector('.copilot-draft-body');
  if (bodyEl) {
    navigator.clipboard.writeText(bodyEl.textContent)
      .then(() => showToast('Message copied to clipboard!', 'success'))
      .catch(() => showToast('Copy failed — try manually', 'warning'));
  }
}

// ── Score All Leads ────────────────────────────────────────────────────────

async function handleScoreLeads() {
  scoreBtn.disabled = true;
  scoreLoader.style.display = 'flex';
  scoreResult.style.display = 'none';

  try {
    const scores = await API.scoreLeads();

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    scoreTbody.innerHTML = scores.map((s, i) => {
      const barColor = s.score >= 70 ? 'var(--success)' :
                       s.score >= 40 ? 'var(--warning)' : 'var(--danger)';
      const isHot = s.score >= 70;
      return `
        <tr class="${isHot ? 'copilot-hot-lead' : ''}">
          <td>${i + 1}</td>
          <td>
            <span class="copilot-score-name">${s.name}</span>
            ${isHot ? '<i class="fa-solid fa-fire" style="color: var(--warning); margin-left: 6px;" title="Hot lead"></i>' : ''}
          </td>
          <td>
            <div class="copilot-score-bar-wrap">
              <div class="copilot-score-bar" style="width: ${s.score}%; background: ${barColor};"></div>
              <span class="copilot-score-value">${s.score}</span>
            </div>
          </td>
          <td>
            ${(s.risk_factors || []).map(r =>
              `<span class="copilot-risk-badge">${r}</span>`
            ).join(' ')}
          </td>
        </tr>`;
    }).join('');

    scoreResult.style.display = 'block';
  } catch (err) {
    showToast(`Copilot error: ${err.message}`, 'error');
  } finally {
    scoreBtn.disabled = false;
    scoreLoader.style.display = 'none';
  }
}

// ── Init & Refresh ─────────────────────────────────────────────────────────

export function initCopilot() {
  registerTab('copilot-tab', refreshCopilot);

  if (suggestBtn)    suggestBtn.addEventListener('click', handleSuggestAction);
  if (draftBtn)      draftBtn.addEventListener('click', handleDraftMessage);
  if (draftCopyBtn)  draftCopyBtn.addEventListener('click', handleCopyDraft);
  if (scoreBtn)      scoreBtn.addEventListener('click', handleScoreLeads);

  if (leadSearchInput) {
    leadSearchInput.addEventListener('input', (e) => {
      renderLeadList(e.target.value);
    });
  }
}

export function refreshCopilot() {
  renderLeadList(leadSearchInput?.value || '');
}
