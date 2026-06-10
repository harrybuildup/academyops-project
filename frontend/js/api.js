// frontend/js/api.js

const API_BASE = window.location.origin.includes('localhost:8000') 
  ? '/api/v1' 
  : 'http://localhost:8000/api/v1';

/**
 * Custom wrapper for standard fetch including authorization bearer token
 */
async function request(endpoint, options = {}) {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    // Automatically log out on unauthorized response (401)
    if (response.status === 401 && !endpoint.includes('/auth/login')) {
      localStorage.removeItem('auth_token');
      window.location.reload();
    }
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || err.error || 'API request failed.');
  }

  if (response.status === 204) return true;
  return response.json();
}

export const API = {
  /**
   * Health Check (Public)
   */
  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      return response.ok;
    } catch {
      return false;
    }
  },

  /**
   * Login (Public)
   */
  async login(username, password) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  },

  /**
   * Register (Optional)
   */
  async register(username, email, password) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password })
    });
  },

  /**
   * Fetch paginated and filtered leads list
   */
  async getLeads(page = 1, limit = 100, stage = null, source = null) {
    const params = new URLSearchParams({ page, limit });
    if (stage && stage !== 'All') params.append('stage', stage);
    if (source && source !== 'All') params.append('source', source);

    return request(`/leads?${params.toString()}`);
  },

  /**
   * Fetch all leads by walking through pages
   */
  async getAllLeads() {
    let leads = [];
    let page = 1;
    const limit = 100;
    while (true) {
      const res = await this.getLeads(page, limit);
      const batch = res.data || [];
      if (batch.length === 0) break;
      leads.push(...batch);
      if (batch.length < limit) break;
      page++;
    }
    return leads;
  },

  /**
   * Fetch details of a single lead by ID
   */
  async getLead(id) {
    return request(`/leads/${id}`);
  },

  /**
   * Create a new lead record
   */
  async createLead(leadData) {
    return request('/leads', {
      method: 'POST',
      body: JSON.stringify(leadData)
    });
  },

  /**
   * Update the stage of an existing lead
   */
  async updateLeadStage(id, stage) {
    return request(`/leads/${id}/stage`, {
      method: 'PATCH',
      body: JSON.stringify({ stage })
    });
  },

  /**
   * Update all details of an existing lead
   */
  async updateLead(id, leadData) {
    return request(`/leads/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(leadData)
    });
  },

  /**
   * Delete a lead record
   */
  async deleteLead(id) {
    return request(`/leads/${id}`, {
      method: 'DELETE'
    });
  },

  /**
   * Classify an inbound message from a lead
   */
  async classifyMessage(id, message) {
    return request(`/leads/${id}/message`, {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  },

  /**
   * Fetch all registered operators (Admins only)
   */
  async getUsers() {
    return request('/users');
  },

  /**
   * Create a new operator account (Admins only)
   */
  async createUser(userData) {
    return request('/users', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  /**
   * Update operator attributes, e.g. role or active status (Admins only)
   */
  async updateUser(userId, userData) {
    return request(`/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(userData)
    });
  }
};
