// frontend/js/api.js

const API_BASE = window.location.origin.includes('localhost:8000') 
  ? '/api/v1' 
  : 'http://localhost:8000/api/v1';

export const API = {
  /**
   * Health Check
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
   * Fetch paginated and filtered leads list
   */
  async getLeads(page = 1, limit = 100, stage = null, source = null) {
    const params = new URLSearchParams({ page, limit });
    if (stage && stage !== 'All') params.append('stage', stage);
    if (source && source !== 'All') params.append('source', source);

    const response = await fetch(`${API_BASE}/leads?${params.toString()}`);
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Failed to fetch leads.');
    }
    return response.json();
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
    const response = await fetch(`${API_BASE}/leads/${id}`);
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || `Failed to fetch lead with ID ${id}.`);
    }
    return response.json();
  },

  /**
   * Create a new lead record
   */
  async createLead(leadData) {
    const response = await fetch(`${API_BASE}/leads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(leadData)
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Failed to create lead.');
    }
    return response.json();
  },

  /**
   * Update the stage of an existing lead
   */
  async updateLeadStage(id, stage) {
    const response = await fetch(`${API_BASE}/leads/${id}/stage`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage })
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Failed to update lead stage.');
    }
    return response.json();
  },

  /**
   * Delete a lead record
   */
  async deleteLead(id) {
    const response = await fetch(`${API_BASE}/leads/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      if (response.status === 204) return true;
      const err = await response.json();
      throw new Error(err.error || 'Failed to delete lead.');
    }
    return true;
  },

  /**
   * Classify an inbound message from a lead
   */
  async classifyMessage(id, message) {
    const response = await fetch(`${API_BASE}/leads/${id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Failed to classify message.');
    }
    return response.json();
  }
};
