
// frontend/js/triage.js

import { state, reloadStateCache, showToast, registerTab } from './shared.js';
import { API } from './api.js';

// DOM elements
const leadsListContainer = document.getElementById('triage-leads-list-container');
const noTriageLeadSelected = document.getElementById('no-triage-lead-selected');
const triageActiveContainer = document.getElementById('triage-active-container');

const triageLeadName = document.getElementById('triage-lead-name');
const triageLeadStageBadge = document.getElementById('triage-lead-stage-badge');
const triageMessageInput = document.getElementById('triage-message-input');
const triageClassifyBtn = document.getElementById('triage-classify-btn');

const triageResultsCard = document.getElementById('triage-results-card');
const triageResultIntent = document.getElementById('triage-result-intent');
const triageResultStage = document.getElementById('triage-result-stage');
const triageApplyStageBtn = document.getElementById('triage-apply-stage-btn');
const triageResultReply = document.getElementById('triage-result-reply');
const triageCopyReplyBtn = document.getElementById('triage-copy-reply-btn');

// Local storage for classification result
let latestClassification = null;

// Suggestion messages that users can click to pre-fill
const PREFILL_SUGGESTIONS = [
  "I'm ready to enroll in the program. What are the next steps to start classes?",
  "I'm interested in EasySkill but I have a few questions about job placement assistance.",
  "Can we reschedule our meeting? Let's do a Demo call next Wednesday afternoon.",
  "Please stop sending me emails. Unsubscribe me from your leads database."
];

/**
 * Initialize Triage tab elements
 */
export function initTriage() {
  registerTab('triage-tab', refreshTriage);
  triageClassifyBtn.addEventListener('click', handleClassifyClick);
  triageCopyReplyBtn.addEventListener('click', handleCopyReplyClick);
  triageApplyStageBtn.addEventListener('click', handleApplyStageClick);
}

/**
 * Invoked on tab activation to load data list
 */
export function refreshTriage() {
  renderLeadsList();
  syncActiveLeadPanel();
}

/**
 * Renders the leads picker menu
 */
function renderLeadsList() {
  leadsListContainer.innerHTML = '';
  
  if (state.leads.length === 0) {
    leadsListContainer.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:12px;">No leads available.</div>';
    return;
  }

  // Sort by name
  const sortedLeads = [...state.leads].sort((a, b) => a.name.localeCompare(b.name));

  sortedLeads.forEach(lead => {
    const item = document.createElement('div');
    item.className = `triage-lead-item ${state.triageLeadId === lead.id ? 'active' : ''}`;
    item.innerHTML = `
      <span class="lead-name">${escapeHtml(lead.name)}</span>
      <span class="badge badge-${lead.stage.toLowerCase()}">${lead.stage}</span>
    `;

    item.addEventListener('click', () => {
      state.triageLeadId = lead.id;
      
      // Clear previous inputs/results
      triageMessageInput.value = '';
      triageResultsCard.classList.add('hidden');
      latestClassification = null;

      // Add prefill link/pills dynamically underneath text box
      triageMessageInput.value = PREFILL_SUGGESTIONS[Math.floor(Math.random() * PREFILL_SUGGESTIONS.length)];
      
      renderLeadsList(); // Refresh active highlights
      syncActiveLeadPanel();
    });

    leadsListContainer.appendChild(item);
  });
}

/**
 * Synchronizes details of the selected triage prospect
 */
function syncActiveLeadPanel() {
  if (!state.triageLeadId) {
    noTriageLeadSelected.classList.remove('hidden');
    triageActiveContainer.classList.add('hidden');
    return;
  }

  const lead = state.leads.find(l => l.id === state.triageLeadId);
  if (!lead) {
    state.triageLeadId = null;
    noTriageLeadSelected.classList.remove('hidden');
    triageActiveContainer.classList.add('hidden');
    return;
  }

  noTriageLeadSelected.classList.add('hidden');
  triageActiveContainer.classList.remove('hidden');

  triageLeadName.textContent = lead.name;
  triageLeadStageBadge.textContent = lead.stage;
  triageLeadStageBadge.className = `badge badge-${lead.stage.toLowerCase()}`;
}

/**
 * Triggers API call to classify inbound text message
 */
async function handleClassifyClick() {
  if (!state.triageLeadId) return;
  const message = triageMessageInput.value.trim();
  
  if (!message) {
    showToast('Please enter a message to classify.', 'error');
    return;
  }

  triageClassifyBtn.disabled = true;
  const originalText = triageClassifyBtn.innerHTML;
  triageClassifyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Classifying...';

  try {
    const result = await API.classifyMessage(state.triageLeadId, message);
    latestClassification = result;
    
    triageResultsCard.classList.remove('hidden');
    triageResultIntent.textContent = formatIntent(result.intent);
    triageResultStage.textContent = result.suggested_stage;
    triageResultReply.textContent = result.reply;

    showToast('Message analyzed successfully.', 'success');
  } catch (error) {
    console.error('Classification error:', error);
    showToast(error.message || 'Failed to classify message.', 'error');
    triageResultsCard.classList.add('hidden');
  } finally {
    triageClassifyBtn.disabled = false;
    triageClassifyBtn.innerHTML = originalText;
  }
}

/**
 * Copies suggested response template to user clipboard
 */
async function handleCopyReplyClick() {
  if (!latestClassification || !latestClassification.reply) return;
  
  try {
    await navigator.clipboard.writeText(latestClassification.reply);
    showToast('Reply template copied to clipboard!', 'success');
  } catch (err) {
    console.error('Clipboard copy failed:', err);
    showToast('Failed to copy to clipboard.', 'error');
  }
}

/**
 * Auto-promotes/demotes lead stage according to classifier recommendation
 */
async function handleApplyStageClick() {
  if (!state.triageLeadId || !latestClassification) return;
  const recommendedStage = latestClassification.suggested_stage;
  
  try {
    const updated = await API.updateLeadStage(state.triageLeadId, recommendedStage);
    showToast(`Stage updated to "${updated.stage}" for ${updated.name}`, 'success');
    
    await reloadStateCache();
    renderLeadsList();
    syncActiveLeadPanel();
    
    // Hide results panel since the stage is now applied
    triageResultsCard.classList.add('hidden');
    triageMessageInput.value = '';
    latestClassification = null;
  } catch (error) {
    console.error('Error applying recommended stage:', error);
    showToast(error.message || 'Failed to apply stage.', 'error');
  }
}

/**
 * Formats machine intent text to human readable display
 */
function formatIntent(intent) {
  if (!intent) return '-';
  // Capitalize and replace underscores
  return intent
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Simple HTML sanitizer
 */
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
