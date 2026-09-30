// frontend/js/crud.js


import { API } from './api.js';
import { state, reloadStateCache, showToast, registerTab } from './shared.js';

const searchInput = document.getElementById('lead-search-input');
const addLeadBtn = document.getElementById('add-lead-btn');
const addLeadModal = document.getElementById('add-lead-modal');
const closeDecimalModalBtn = document.getElementById('close-modal-btn');
const cancelModalBtn = document.getElementById('cancel-modal-btn');
const addLeadForm = document.getElementById('add-lead-form');

const crudLeadsTbody = document.getElementById('crud-leads-tbody');
const paginationInfo = document.getElementById('pagination-info');
const prevPageBtn = document.getElementById('prev-page-btn');
const nextPageBtn = document.getElementById('next-page-btn');
const currentPageNumText = document.getElementById('current-page-num');

const noLeadSelectedCard = document.getElementById('no-lead-selected');
const leadInspectorCard = document.getElementById('lead-inspector-card');
const inspectorAvatarText = document.getElementById('inspector-avatar-text');
const inspectorName = document.getElementById('inspector-name');
const inspectorCreatedAt = document.getElementById('inspector-created-at');
const inspectorPhone = document.getElementById('inspector-phone');
const inspectorSource = document.getElementById('inspector-source');
const inspectorStageSelect = document.getElementById('inspector-stage-select');
const inspectorNotesText = document.getElementById('inspector-notes-text');
const inspectorDeleteBtn = document.getElementById('inspector-delete-btn');
const inspectorEditBtn = document.getElementById('inspector-edit-btn');

const editLeadModal = document.getElementById('edit-lead-modal');
const editCloseModalBtn = document.getElementById('edit-close-modal-btn');
const editCancelModalBtn = document.getElementById('edit-cancel-modal-btn');
const editLeadForm = document.getElementById('edit-lead-form');

// Local pagination state
let currentPage = 1;
const ITEMS_PER_PAGE = 10;
let filteredList = [];
let customFieldDefs = []; // cached active custom field definitions

/**
 * Register CRUD event listeners
 */
export function initCRUD() {
  registerTab('leads-tab', refreshCRUD);
  // Search listener
  searchInput.addEventListener('input', () => {
    currentPage = 1;
    applySearchAndFilter();
  });

  // Modal open/close
  addLeadBtn.addEventListener('click', () => {
    addLeadForm.reset();
    renderCustomFieldsInForm('custom-fields-add', null);
    addLeadModal.classList.remove('hidden');
  });
  
  const closeModal = () => addLeadModal.classList.add('hidden');
  closeDecimalModalBtn.addEventListener('click', closeModal);
  cancelModalBtn.addEventListener('click', closeModal);
  
  // Form submission
  addLeadForm.addEventListener('submit', handleAddLeadSubmit);

  // Pagination buttons
  prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      renderCRUDTable();
    }
  });

  nextPageBtn.addEventListener('click', () => {
    const totalPages = Math.ceil(filteredList.length / ITEMS_PER_PAGE);
    if (currentPage < totalPages) {
      currentPage++;
      renderCRUDTable();
    }
  });

  // Stage modification listener
  inspectorStageSelect.addEventListener('change', handleStageChange);

  // Lead delete record button
  inspectorDeleteBtn.addEventListener('click', handleDeleteLead);
  // Edit modal bindings
  inspectorEditBtn.addEventListener('click', () => {
    if (!state.selectedLeadId) return;
    const lead = state.leads.find(l => l.id === state.selectedLeadId);
    if (!lead) return;

    // Prefill form
    document.getElementById('edit-lead-name').value = lead.name;
    document.getElementById('edit-lead-phone').value = lead.phone;
    document.getElementById('edit-lead-source-select').value = lead.source || 'Direct';
    document.getElementById('edit-lead-stage-select').value = lead.stage;
    document.getElementById('edit-lead-notes').value = lead.notes || '';

    renderCustomFieldsInForm('custom-fields-edit', lead.custom_fields);
    editLeadModal.classList.remove('hidden');
  });
  const closeEditModal = () => editLeadModal.classList.add('hidden');
  editCloseModalBtn.addEventListener('click', closeEditModal);
  editCancelModalBtn.addEventListener('click', closeEditModal);
  editLeadForm.addEventListener('submit', handleEditLeadSubmit);
}

/**
 * Refreshes data and redrafts components
 */
export function refreshCRUD() {
  applySearchAndFilter();
  updateInspector();
}

/**
 * Filter leads cache by search text
 */
function applySearchAndFilter() {
  const query = searchInput.value.toLowerCase().trim();
  
  if (!query) {
    filteredList = [...state.leads];
  } else {
    filteredList = state.leads.filter(l => 
      l.name.toLowerCase().includes(query) || 
      l.phone.includes(query)
    );
  }

  // Sort by created date descending
  filteredList.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  // Handle page out-of-bounds safety
  const maxPage = Math.max(1, Math.ceil(filteredList.length / ITEMS_PER_PAGE));
  if (currentPage > maxPage) {
    currentPage = maxPage;
  }

  renderCRUDTable();
}

/**
 * Renders the leads rows for the current page
 */
function renderCRUDTable() {
  crudLeadsTbody.innerHTML = '';
  
  const totalItems = filteredList.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / ITEMS_PER_PAGE));
  currentPageNumText.textContent = currentPage;

  // Pagination info text
  const startIdx = totalItems === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1;
  const endIdx = Math.min(currentPage * ITEMS_PER_PAGE, totalItems);
  paginationInfo.textContent = `Showing ${startIdx}-${endIdx} of ${totalItems}`;

  // Button disabled states
  prevPageBtn.disabled = currentPage === 1;
  nextPageBtn.disabled = currentPage === totalPages;

  if (totalItems === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="4" style="text-align:center; color:var(--text-muted); padding: 24px;">No leads found.</td>';
    crudLeadsTbody.appendChild(tr);
    return;
  }

  // Segment leads for the active page
  const pageLeads = filteredList.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  pageLeads.forEach(lead => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-id', lead.id);
    if (state.selectedLeadId === lead.id) {
      tr.classList.add('selected');
    }

    tr.innerHTML = `
      <td><strong>${escapeHtml(lead.name)}</strong></td>
      <td>${escapeHtml(lead.phone)}</td>
      <td>${escapeHtml(lead.source || 'Unknown')}</td>
      <td><span class="badge badge-${lead.stage.toLowerCase()}">${lead.stage}</span></td>
    `;

    tr.addEventListener('click', () => {
      // Toggle selection
      const rows = crudLeadsTbody.querySelectorAll('tr');
      rows.forEach(r => r.classList.remove('selected'));
      
      if (state.selectedLeadId === lead.id) {
        state.selectedLeadId = null;
      } else {
        state.selectedLeadId = lead.id;
        tr.classList.add('selected');
      }
      updateInspector();
    });

    crudLeadsTbody.appendChild(tr);
  });
}

/**
 * Details inspector card synchronization
 */
function updateInspector() {
  if (!state.selectedLeadId) {
    noLeadSelectedCard.classList.remove('hidden');
    leadInspectorCard.classList.add('hidden');
    return;
  }

  const lead = state.leads.find(l => l.id === state.selectedLeadId);
  if (!lead) {
    state.selectedLeadId = null;
    noLeadSelectedCard.classList.remove('hidden');
    leadInspectorCard.classList.add('hidden');
    return;
  }

  // Populate details
  noLeadSelectedCard.classList.add('hidden');
  leadInspectorCard.classList.remove('hidden');

  // Avatar text (initials)
  const initials = lead.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  inspectorAvatarText.textContent = initials || '?';
  
  inspectorName.textContent = lead.name;
  
  const createdDate = new Date(lead.created_at).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  inspectorCreatedAt.textContent = `Created on ${createdDate}`;
  inspectorPhone.textContent = lead.phone;
  inspectorSource.textContent = lead.source || 'Unknown';
  inspectorStageSelect.value = lead.stage;
  inspectorNotesText.textContent = lead.notes || 'No notes recorded.';

  // Render custom fields in inspector
  renderCustomFieldsInInspector(lead.custom_fields);
}

/**
 * Handle new lead record creation form submission
 */
async function handleAddLeadSubmit(event) {
  event.preventDefault();
  
  const name = document.getElementById('lead-name').value.trim();
  const phone = document.getElementById('lead-phone').value.trim();
  const source = document.getElementById('lead-source-select').value;
  const stage = document.getElementById('lead-stage-select').value;
  const notes = document.getElementById('lead-notes').value.trim();
  const custom_fields = gatherCustomFieldValues('custom-fields-add');

  try {
    const newLead = await API.createLead({ name, phone, source, stage, notes, custom_fields });
    
    // Close modal, reload state cache, notify and select the new record
    addLeadModal.classList.add('hidden');
    addLeadForm.reset();
    
    showToast(`Lead "${newLead.name}" created successfully!`, 'success');
    
    await reloadStateCache();
    state.selectedLeadId = newLead.id;
    applySearchAndFilter();
    updateInspector();
  } catch (error) {
    console.error('Error creating lead:', error);
    showToast(error.message || 'Failed to create lead. Check logs.', 'error');
  }
}

/**
 * Handle edit lead record form submission
 */
async function handleEditLeadSubmit(event) {
  event.preventDefault();
  if (!state.selectedLeadId) return;

  const name = document.getElementById('edit-lead-name').value.trim();
  const phone = document.getElementById('edit-lead-phone').value.trim();
  const source = document.getElementById('edit-lead-source-select').value;
  const stage = document.getElementById('edit-lead-stage-select').value;
  const notes = document.getElementById('edit-lead-notes').value.trim();
  const custom_fields = gatherCustomFieldValues('custom-fields-edit');

  try {
    const updated = await API.updateLead(state.selectedLeadId, { name, phone, source, stage, notes, custom_fields });
    
    editLeadModal.classList.add('hidden');
    showToast(`Lead "${updated.name}" updated successfully!`, 'success');
    
    await reloadStateCache();
    applySearchAndFilter();
    updateInspector();
  } catch (error) {
    console.error('Error editing lead:', error);
    showToast(error.message || 'Failed to update lead. Check logs.', 'error');
  }
}

/**
 * Handle stage update select action
 */
async function handleStageChange() {
  if (!state.selectedLeadId) return;
  const newStage = inspectorStageSelect.value;
  
  try {
    const updated = await API.updateLeadStage(state.selectedLeadId, newStage);
    showToast(`Stage updated to "${updated.stage}" for ${updated.name}`, 'success');
    
    await reloadStateCache();
    applySearchAndFilter();
    updateInspector();
  } catch (error) {
    console.error('Error updating stage:', error);
    showToast(error.message || 'Failed to update stage.', 'error');
    
    // Reset select indicator value back
    const lead = state.leads.find(l => l.id === state.selectedLeadId);
    if (lead) inspectorStageSelect.value = lead.stage;
  }
}

/**
 * Handle lead deletion confirmation & API trigger
 */
async function handleDeleteLead() {
  if (!state.selectedLeadId) return;
  
  const lead = state.leads.find(l => l.id === state.selectedLeadId);
  if (!lead) return;
  
  if (confirm(`Are you absolutely sure you want to permanently delete lead record "${lead.name}"?`)) {
    try {
      await API.deleteLead(state.selectedLeadId);
      showToast(`Lead "${lead.name}" deleted successfully.`, 'success');
      
      state.selectedLeadId = null;
      await reloadStateCache();
      applySearchAndFilter();
      updateInspector();
    } catch (error) {
      console.error('Error deleting lead:', error);
      showToast(error.message || 'Failed to delete lead record.', 'error');
    }
  }
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

// ── Custom Field Helpers ─────────────────────────────────────────────────

/**
 * Load active custom field definitions from API
 */
export async function loadCustomFieldDefs() {
  try {
    customFieldDefs = await API.getActiveCustomFields();
  } catch (e) {
    console.warn('Could not load custom field definitions:', e);
    customFieldDefs = [];
  }
}

/**
 * Render dynamic custom field inputs inside a container
 * @param {string} containerId - DOM id of the container div
 * @param {object|null} values - existing values to prefill (for edit modal)
 */
function renderCustomFieldsInForm(containerId, values) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  if (!customFieldDefs || customFieldDefs.length === 0) {
    container.innerHTML = '';
    return;
  }

  const vals = values || {};
  
  container.innerHTML = `
    <div class="custom-fields-section-label">
      <i class="fa-solid fa-sliders"></i> Custom Fields
    </div>
    <div class="form-grid">
      ${customFieldDefs.map(f => {
        const key = f.field_key;
        const val = vals[key] ?? '';
        const req = f.is_required ? 'required' : '';
        const reqMark = f.is_required ? ' *' : '';
        const inputId = `${containerId}-${key}`;
        
        let input = '';
        switch (f.field_type) {
          case 'text':
            input = `<input type="text" id="${inputId}" class="form-control" data-field-key="${key}" value="${escapeHtml(String(val))}" ${req}>`;
            break;
          case 'number':
            input = `<input type="number" id="${inputId}" class="form-control" data-field-key="${key}" value="${val}" ${req}>`;
            break;
          case 'date':
            input = `<input type="date" id="${inputId}" class="form-control" data-field-key="${key}" value="${val}" ${req}>`;
            break;
          case 'select':
            const opts = (f.options || []).map(o => 
              `<option value="${escapeHtml(o)}" ${val === o ? 'selected' : ''}>${escapeHtml(o)}</option>`
            ).join('');
            input = `<select id="${inputId}" class="form-control" data-field-key="${key}" ${req}>
              <option value="">-- Select --</option>${opts}
            </select>`;
            break;
          case 'checkbox':
            input = `<label class="cf-checkbox-label">
              <input type="checkbox" id="${inputId}" data-field-key="${key}" ${val ? 'checked' : ''}>
              Yes
            </label>`;
            break;
          default:
            input = `<input type="text" id="${inputId}" class="form-control" data-field-key="${key}" value="${escapeHtml(String(val))}" ${req}>`;
        }
        
        return `<div class="form-group">
          <label for="${inputId}">${escapeHtml(f.name)}${reqMark}</label>
          ${input}
        </div>`;
      }).join('')}
    </div>`;
}

/**
 * Gather custom field values from a form container
 * @param {string} containerId - DOM id of the container div
 * @returns {object} key-value pairs of custom field values
 */
function gatherCustomFieldValues(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return {};
  
  const result = {};
  customFieldDefs.forEach(f => {
    const el = container.querySelector(`[data-field-key="${f.field_key}"]`);
    if (!el) return;
    
    if (f.field_type === 'checkbox') {
      result[f.field_key] = el.checked;
    } else if (f.field_type === 'number') {
      result[f.field_key] = el.value ? Number(el.value) : null;
    } else {
      result[f.field_key] = el.value || '';
    }
  });
  return result;
}

/**
 * Render custom field values in the inspector panel
 * @param {object|null} values - custom field values from the lead
 */
function renderCustomFieldsInInspector(values) {
  const container = document.getElementById('inspector-custom-fields');
  if (!container) return;
  
  if (!customFieldDefs || customFieldDefs.length === 0 || !values || Object.keys(values).length === 0) {
    container.innerHTML = '';
    return;
  }

  const rows = customFieldDefs
    .filter(f => values[f.field_key] !== undefined && values[f.field_key] !== '' && values[f.field_key] !== null)
    .map(f => {
      let displayVal = values[f.field_key];
      if (f.field_type === 'checkbox') displayVal = displayVal ? 'Yes' : 'No';
      if (f.field_type === 'date' && displayVal) {
        displayVal = new Date(displayVal).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
      }
      return `<div class="detail-row">
        <span class="detail-label"><i class="fa-solid fa-tag"></i> ${escapeHtml(f.name)}</span>
        <span class="detail-value">${escapeHtml(String(displayVal))}</span>
      </div>`;
    }).join('');

  if (rows) {
    container.innerHTML = `
      <div class="inspector-custom-section">
        <h4><i class="fa-solid fa-sliders"></i> Custom Fields</h4>
        <div class="inspector-details-grid">${rows}</div>
      </div>`;
  } else {
    container.innerHTML = '';
  }
}
