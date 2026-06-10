// frontend/js/kanban.js

import { API } from './api.js';
import { state, showToast, reloadStateCache } from './app.js';

/**
 * Initialize Kanban board listeners
 */
export function initKanban() {
  const columns = document.querySelectorAll('.kanban-column');
  
  columns.forEach(column => {
    const listContainer = column.querySelector('.kanban-cards-list');
    const stage = column.getAttribute('data-stage');
    
    // Drag and drop event listeners on the drop zones
    listContainer.addEventListener('dragover', (e) => {
      e.preventDefault();
    });
    
    listContainer.addEventListener('dragenter', (e) => {
      e.preventDefault();
      column.classList.add('drag-over');
    });
    
    listContainer.addEventListener('dragleave', () => {
      column.classList.remove('drag-over');
    });
    
    listContainer.addEventListener('drop', async (e) => {
      e.preventDefault();
      column.classList.remove('drag-over');
      
      const leadIdStr = e.dataTransfer.getData('text/plain');
      if (!leadIdStr) return;
      
      const leadId = parseInt(leadIdStr, 10);
      const lead = state.leads.find(l => l.id === leadId);
      
      if (!lead) return;
      
      // If the stage hasn't changed, ignore
      if (lead.stage === stage) return;
      
      // Optimistic UI Update: change stage locally & redraw card in the new column
      const oldStage = lead.stage;
      lead.stage = stage;
      
      // Quick local re-render to make it feel instantaneous
      refreshKanban();
      
      try {
        const updated = await API.updateLeadStage(leadId, stage);
        showToast(`Moved ${updated.name} to ${stage}`, 'success');
        
        // Fully refresh the cached state to sync other components
        await reloadStateCache();
      } catch (error) {
        console.error('Failed to update lead stage via drag-and-drop:', error);
        showToast(error.message || 'Failed to update lead stage.', 'error');
        
        // Revert stage change on error
        lead.stage = oldStage;
        refreshKanban();
      }
    });
  });
}

/**
 * Redraw all cards in their respective columns
 */
export function refreshKanban() {
  const stages = ['New', 'Contacted', 'Qualified', 'Demo', 'Enrolled', 'Lost'];
  
  // Group leads by stage
  const grouped = {};
  stages.forEach(s => {
    grouped[s] = [];
    // Reset column counts
    const countEl = document.getElementById(`count-${s}`);
    if (countEl) countEl.textContent = '0';
    
    // Clear list container
    const listEl = document.querySelector(`.kanban-cards-list[data-stage="${s}"]`);
    if (listEl) listEl.innerHTML = '';
  });
  
  state.leads.forEach(lead => {
    if (grouped[lead.stage]) {
      grouped[lead.stage].push(lead);
    }
  });
  
  // Render leads in each column
  stages.forEach(stage => {
    const listEl = document.querySelector(`.kanban-cards-list[data-stage="${stage}"]`);
    const countEl = document.getElementById(`count-${stage}`);
    const leadsInStage = grouped[stage];
    
    if (countEl) {
      countEl.textContent = leadsInStage.length;
    }
    
    if (!listEl) return;
    
    if (leadsInStage.length === 0) {
      listEl.innerHTML = `
        <div class="kanban-empty-state">
          <span>No leads</span>
        </div>
      `;
      return;
    }
    
    leadsInStage.forEach(lead => {
      const card = document.createElement('div');
      card.className = 'kanban-card glass-card';
      card.setAttribute('draggable', 'true');
      card.setAttribute('data-id', lead.id);
      
      // Course & Source labels
      const sourceBadge = lead.source ? `<span class="badge badge-source">${lead.source}</span>` : '';
      const notesSnippet = lead.notes ? `<p class="kanban-card-notes">${lead.notes.substring(0, 50)}${lead.notes.length > 50 ? '...' : ''}</p>` : '<p class="kanban-card-notes empty-notes">No notes logged</p>';
      
      card.innerHTML = `
        <div class="kanban-card-header">
          <span class="kanban-card-name">${lead.name}</span>
          <button class="kanban-card-edit-btn" title="Edit Lead Details">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
        </div>
        <div class="kanban-card-body">
          <div class="kanban-card-contact">
            <i class="fa-solid fa-phone"></i> <span>${lead.phone}</span>
          </div>
          ${notesSnippet}
        </div>
        <div class="kanban-card-footer">
          ${sourceBadge}
          <span class="kanban-card-date">${formatCardDate(lead.created_at)}</span>
        </div>
      `;
      
      // Edit button handler
      const editBtn = card.querySelector('.kanban-card-edit-btn');
      editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        openEditFromKanban(lead.id);
      });
      
      // Drag events on the card
      card.addEventListener('dragstart', (e) => {
        card.classList.add('dragging');
        e.dataTransfer.setData('text/plain', lead.id);
        e.dataTransfer.effectAllowed = 'move';
      });
      
      card.addEventListener('dragend', () => {
        card.classList.remove('dragging');
      });
      
      listEl.appendChild(card);
    });
  });
}

/**
 * Format timestamp nicely for cards
 */
function formatCardDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

/**
 * Set selected lead and open global edit modal
 */
function openEditFromKanban(leadId) {
  state.selectedLeadId = leadId;
  const lead = state.leads.find(l => l.id === leadId);
  if (!lead) return;
  
  // Prefill Edit modal form inputs
  document.getElementById('edit-lead-name').value = lead.name;
  document.getElementById('edit-lead-phone').value = lead.phone;
  document.getElementById('edit-lead-source-select').value = lead.source || 'Direct';
  document.getElementById('edit-lead-stage-select').value = lead.stage;
  document.getElementById('edit-lead-notes').value = lead.notes || '';
  
  // Show edit modal
  const editLeadModal = document.getElementById('edit-lead-modal');
  if (editLeadModal) {
    editLeadModal.classList.remove('hidden');
  }
}
