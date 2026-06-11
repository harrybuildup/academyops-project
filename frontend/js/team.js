// frontend/js/team.js

import { API } from './api.js';
import { showToast, registerTab } from './shared.js';

const addOperatorModal = document.getElementById('add-operator-modal');
const addOperatorBtn = document.getElementById('add-operator-btn');
const closeOperatorModalBtn = document.getElementById('close-operator-modal-btn');
const cancelOperatorModalBtn = document.getElementById('cancel-operator-modal-btn');
const addOperatorForm = document.getElementById('add-operator-form');
const teamTableBody = document.getElementById('team-table-body');

/**
 * Helper to decode token payload and get details
 */
export function getTokenPayload() {
  const token = localStorage.getItem('auth_token');
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    return JSON.parse(atob(parts[1]));
  } catch (e) {
    console.error('Error decoding auth token:', e);
    return null;
  }
}

/**
 * Initialize Team Panel events
 */
export function initTeam() {
  registerTab('settings-tab', refreshTeam);
  const payload = getTokenPayload();
  if (!payload || payload.role !== 'Admin') return;

  // Open modal
  if (addOperatorBtn) {
    addOperatorBtn.addEventListener('click', () => {
      addOperatorForm.reset();
      addOperatorModal.classList.remove('hidden');
    });
  }

  // Close modal
  const closeModal = () => {
    if (addOperatorModal) addOperatorModal.classList.add('hidden');
  };

  if (closeOperatorModalBtn) closeOperatorModalBtn.addEventListener('click', closeModal);
  if (cancelOperatorModalBtn) cancelOperatorModalBtn.addEventListener('click', closeModal);

  // Handle operator form submit
  if (addOperatorForm) {
    addOperatorForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const username = document.getElementById('operator-username').value.trim();
      const email = document.getElementById('operator-email').value.trim();
      const password = document.getElementById('operator-password').value;
      const role = document.getElementById('operator-role').value;

      try {
        await API.createUser({ username, email, password, role });
        showToast(`Operator "${username}" created successfully!`, 'success');
        closeModal();
        refreshTeam();
      } catch (err) {
        console.error(err);
        showToast(err.message || 'Failed to create operator account.', 'error');
      }
    });
  }
}

/**
 * Fetch and render all operators
 */
export async function refreshTeam() {
  const payload = getTokenPayload();
  if (!payload || payload.role !== 'Admin') return;

  const currentUsername = payload.sub;

  try {
    const users = await API.getUsers();
    if (!teamTableBody) return;
    
    teamTableBody.innerHTML = '';

    if (users.length === 0) {
      teamTableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); font-style: italic; padding: 20px;">
            No users registered
          </td>
        </tr>
      `;
      return;
    }

    users.forEach(user => {
      const isSelf = user.username === currentUsername;
      const createdDate = new Date(user.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      const tr = document.createElement('tr');
      tr.className = 'user-row';

      // Status pill badge HTML
      const statusPill = user.is_active 
        ? `<span class="badge badge-success" style="background-color: var(--success-bg); color: var(--success);">Active</span>`
        : `<span class="badge badge-danger" style="background-color: var(--danger-bg); color: var(--danger);">Deactivated</span>`;

      // Role Select Dropdown HTML
      let roleSelect = '';
      if (isSelf) {
        roleSelect = `<span class="badge badge-source" style="font-size: 11px;">${user.role}</span>`;
      } else {
        roleSelect = `
          <select class="form-control role-update-select" data-id="${user.id}" style="width: 110px; padding: 4px 8px; font-size: 12px; height: 28px; margin: 0;">
            <option value="Viewer" ${user.role === 'Viewer' ? 'selected' : ''}>Viewer</option>
            <option value="Editor" ${user.role === 'Editor' ? 'selected' : ''}>Editor</option>
            <option value="Admin" ${user.role === 'Admin' ? 'selected' : ''}>Admin</option>
          </select>
        `;
      }

      // Deactivate / Activate Button HTML
      let actionBtn = '';
      if (isSelf) {
        actionBtn = `<span style="font-size: 11.5px; color: var(--text-muted); font-style: italic;">Current User</span>`;
      } else {
        const btnClass = user.is_active ? 'btn-danger' : 'btn-primary';
        const btnText = user.is_active ? 'Deactivate' : 'Activate';
        const btnIcon = user.is_active ? 'fa-user-slash' : 'fa-user-check';
        actionBtn = `
          <button class="btn ${btnClass} btn-xs toggle-status-btn" data-id="${user.id}" data-active="${user.is_active}">
            <i class="fa-solid ${btnIcon}"></i>
            <span>${btnText}</span>
          </button>
        `;
      }

      tr.innerHTML = `
        <td style="font-weight: 600; color: var(--text-primary);"><i class="fa-solid fa-user" style="margin-right: 8px; color: var(--text-muted);"></i> ${user.username}</td>
        <td>${user.email}</td>
        <td>${roleSelect}</td>
        <td>${statusPill}</td>
        <td style="font-size: 12px; color: var(--text-muted);">${createdDate}</td>
        <td>${actionBtn}</td>
      `;

      // Event listeners for role update
      if (!isSelf) {
        const select = tr.querySelector('.role-update-select');
        select.addEventListener('change', async (e) => {
          const newRole = e.target.value;
          try {
            await API.updateUser(user.id, { role: newRole });
            showToast(`Role updated to "${newRole}" for user ${user.username}`, 'success');
            refreshTeam();
          } catch (err) {
            console.error(err);
            showToast(err.message || 'Failed to update user role.', 'error');
            e.target.value = user.role; // Revert change
          }
        });

        const toggleBtn = tr.querySelector('.toggle-status-btn');
        toggleBtn.addEventListener('click', async () => {
          const makeActive = !user.is_active;
          const confirmMsg = makeActive 
            ? `Are you sure you want to activate operator account "${user.username}"?`
            : `Are you sure you want to deactivate operator account "${user.username}"?`;

          if (confirm(confirmMsg)) {
            try {
              await API.updateUser(user.id, { is_active: makeActive });
              showToast(`User "${user.username}" is now ${makeActive ? 'active' : 'deactivated'}.`, 'success');
              refreshTeam();
            } catch (err) {
              console.error(err);
              showToast(err.message || 'Failed to update user status.', 'error');
            }
          }
        });
      }

      teamTableBody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load users list:', err);
    showToast('Failed to load operators list.', 'error');
  }
}
