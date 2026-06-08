// frontend/js/dashboard.js

import { state } from './app.js';
import { API } from './api.js';

// DOM elements
const filterSource = document.getElementById('filter-source');
const filterDateStart = document.getElementById('filter-date-start');
const filterDateEnd = document.getElementById('filter-date-end');

const kpiTotalLeads = document.getElementById('kpi-total-leads');
const kpiConversionRate = document.getElementById('kpi-conversion-rate');
const kpiActiveLeads = document.getElementById('kpi-active-leads');
const recentLeadsTbody = document.getElementById('recent-leads-tbody');
const downloadCsvBtn = document.getElementById('download-csv-btn');

// Chart.js Chart Instances
let funnelChartInstance = null;
let sourceChartInstance = null;

const STAGE_ORDER = ["New", "Contacted", "Qualified", "Demo", "Enrolled"];

/**
 * Initialize Dashboard DOM event listeners and default filter settings
 */
export function initDashboard() {
  // Setup filter event listeners
  filterSource.addEventListener('change', renderDashboardData);
  filterDateStart.addEventListener('change', renderDashboardData);
  filterDateEnd.addEventListener('change', renderDashboardData);

  // Setup CSV download listener
  downloadCsvBtn.addEventListener('click', downloadFilteredCSV);
}

/**
 * Invoked on tab activation to ensure cache is loaded and drop-downs populated
 */
export async function refreshDashboard() {
  populateSourceDropdown();
  populateDateDefaults();
  renderDashboardData();
}

/**
 * Extracts unique lead sources from state cache and populates the filter list
 */
function populateSourceDropdown() {
  const currentVal = filterSource.value;
  filterSource.innerHTML = '<option value="All">All Sources</option>';

  const sources = [...new Set(state.leads.map(lead => lead.source).filter(Boolean))].sort();
  sources.forEach(src => {
    const opt = document.createElement('option');
    opt.value = src;
    opt.textContent = src;
    filterSource.appendChild(opt);
  });

  // Keep user selection if it still exists
  if (sources.includes(currentVal)) {
    filterSource.value = currentVal;
  }
}

/**
 * Automatically calculates default start and end dates based on lead records
 */
function populateDateDefaults() {
  if (state.leads.length === 0) return;

  const timestamps = state.leads.map(l => new Date(l.created_at).getTime());
  const minTime = Math.min(...timestamps);
  const maxTime = Math.max(...timestamps);

  // Format to YYYY-MM-DD
  const formatDate = (dateObj) => {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Only pre-fill if date inputs are empty
  if (!filterDateStart.value) {
    filterDateStart.value = formatDate(new Date(minTime));
  }
  if (!filterDateEnd.value) {
    // Add one day to end range limit for filter safety
    const endPlusOne = new Date(maxTime);
    filterDateEnd.value = formatDate(endPlusOne);
  }
}

/**
 * Return leads matching active dropdown and date-range filters
 */
function getFilteredLeads() {
  let filtered = [...state.leads];

  // 1. Source Filter
  const src = filterSource.value;
  if (src && src !== 'All') {
    filtered = filtered.filter(l => l.source === src);
  }

  // 2. Date Filters
  const startVal = filterDateStart.value;
  const endVal = filterDateEnd.value;

  if (startVal) {
    const startDate = new Date(startVal);
    startDate.setHours(0, 0, 0, 0);
    filtered = filtered.filter(l => new Date(l.created_at) >= startDate);
  }

  if (endVal) {
    const endDate = new Date(endVal);
    endDate.setHours(23, 59, 59, 999);
    filtered = filtered.filter(l => new Date(l.created_at) <= endDate);
  }

  return filtered;
}

/**
 * Re-computes and redraws all analytics panels, KPIs, and charts
 */
function renderDashboardData() {
  const filtered = getFilteredLeads();

  // 1. Calculate KPIs
  const total = filtered.length;
  const enrolledCount = filtered.filter(l => l.stage === 'Enrolled').length;
  const conversionRate = total > 0 ? ((enrolledCount / total) * 100).toFixed(1) : '0.0';
  const activeCount = filtered.filter(l => !['Enrolled', 'Lost'].includes(l.stage)).length;

  kpiTotalLeads.textContent = total.toLocaleString();
  kpiConversionRate.textContent = `${conversionRate}%`;
  kpiActiveLeads.textContent = activeCount.toLocaleString();

  // 2. Render Charts
  drawFunnelChart(filtered);
  drawSourceConversionChart(filtered);

  // 3. Render recent table
  renderRecentLeadsTable(filtered);
}

/**
 * Renders the conversion stages funnel
 */
function drawFunnelChart(leads) {
  // Count leads per stage in STAGE_ORDER
  const stageCounts = STAGE_ORDER.map(stage => {
    return leads.filter(l => l.stage === stage).length;
  });

  const ctx = document.getElementById('funnelChart').getContext('2d');
  
  if (funnelChartInstance) {
    funnelChartInstance.destroy();
  }

  const isLight = state.theme === 'light';
  const textColor = isLight ? '#1e293b' : '#f8fafc';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.05)';

  funnelChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: STAGE_ORDER,
      datasets: [{
        label: 'Leads',
        data: stageCounts,
        backgroundColor: [
          'rgba(59, 130, 246, 0.75)',  // New - blue
          'rgba(168, 85, 247, 0.75)',  // Contacted - purple
          'rgba(249, 115, 22, 0.75)',  // Qualified - orange
          'rgba(234, 179, 8, 0.75)',   // Demo - yellow
          'rgba(22, 163, 74, 0.75)'    // Enrolled - green
        ],
        borderColor: isLight ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isLight ? '#ffffff' : '#1e293b',
          titleColor: isLight ? '#1e293b' : '#ffffff',
          bodyColor: isLight ? '#475569' : '#cbd5e1',
          borderColor: 'rgba(139, 92, 246, 0.3)',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, stepSize: 1 }
        },
        y: {
          grid: { display: false },
          ticks: { color: textColor }
        }
      }
    }
  });
}

/**
 * Calculates conversion rates per source channel and draws chart
 */
function drawSourceConversionChart(leads) {
  // Get all unique sources
  const sources = [...new Set(leads.map(l => l.source).filter(Boolean))];
  
  const sourceStats = sources.map(src => {
    const srcLeads = leads.filter(l => l.source === src);
    const total = srcLeads.length;
    const enrolled = srcLeads.filter(l => l.stage === 'Enrolled').length;
    const pct = total > 0 ? parseFloat(((enrolled / total) * 100).toFixed(1)) : 0;
    return { source: src, rate: pct, total };
  }).sort((a, b) => b.rate - a.rate); // Sort highest conversion rate first

  const labels = sourceStats.map(s => `${s.source} (N=${s.total})`);
  const rates = sourceStats.map(s => s.rate);

  const ctx = document.getElementById('sourceChart').getContext('2d');

  if (sourceChartInstance) {
    sourceChartInstance.destroy();
  }

  const isLight = state.theme === 'light';
  const textColor = isLight ? '#1e293b' : '#f8fafc';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.05)';

  sourceChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Conversion Rate (%)',
        data: rates,
        backgroundColor: 'rgba(139, 92, 246, 0.75)', // Indigo glow theme color
        borderColor: 'rgba(139, 92, 246, 1)',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `Enrollment Rate: ${context.parsed.y}%`
          },
          backgroundColor: isLight ? '#ffffff' : '#1e293b',
          titleColor: isLight ? '#1e293b' : '#ffffff',
          bodyColor: isLight ? '#475569' : '#cbd5e1',
          borderColor: 'rgba(139, 92, 246, 0.3)',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textColor }
        },
        y: {
          max: 100,
          grid: { color: gridColor },
          ticks: { 
            color: textColor,
            callback: (val) => `${val}%`
          }
        }
      }
    }
  });
}

/**
 * Fills the recent leads preview table
 */
function renderRecentLeadsTable(leads) {
  recentLeadsTbody.innerHTML = '';

  if (leads.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="5" style="text-align:center; color:var(--text-muted);">No leads match the filters.</td>';
    recentLeadsTbody.appendChild(tr);
    return;
  }

  // Sort by created_at descending and get top 10
  const recent = [...leads]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 10);

  recent.forEach(lead => {
    const dateStr = new Date(lead.created_at).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${escapeHtml(lead.name)}</strong></td>
      <td>${escapeHtml(lead.phone)}</td>
      <td>${escapeHtml(lead.source || 'Unknown')}</td>
      <td><span class="badge badge-${lead.stage.toLowerCase()}">${lead.stage}</span></td>
      <td>${dateStr}</td>
    `;
    recentLeadsTbody.appendChild(tr);
  });
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

/**
 * Constructs filtered records and downloads them as a local CSV file
 */
function downloadFilteredCSV() {
  const filtered = getFilteredLeads();
  if (filtered.length === 0) {
    alert('No data to export.');
    return;
  }

  // Define headers
  const headers = ['id', 'name', 'phone', 'source', 'stage', 'notes', 'created_at', 'updated_at'];
  
  // Build rows
  const csvRows = [headers.join(',')];
  for (const lead of filtered) {
    const values = headers.map(header => {
      let val = lead[header];
      if (val === null || val === undefined) {
        val = '';
      } else {
        val = String(val).replace(/"/g, '""'); // Escape inner double quotes
      }
      return `"${val}"`; // wrap cell in quotes
    });
    csvRows.push(values.join(','));
  }

  // Trigger browser download link
  const csvContent = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvRows.join('\n'));
  const link = document.createElement('a');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  link.setAttribute('href', csvContent);
  link.setAttribute('download', `academyops_leads_${timestamp}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
