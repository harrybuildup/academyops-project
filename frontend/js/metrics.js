// frontend/js/metrics.js

import { state } from './app.js';

// DOM elements for KPIs
const kpiAvgEnrollDays = document.getElementById('kpi-avg-enroll-days');
const kpiStaleLeads = document.getElementById('kpi-stale-leads');
const kpiLeadGrowth = document.getElementById('kpi-lead-growth');

// Chart instances
let inflowChartInstance = null;
let agingChartInstance = null;

/**
 * Initialize metrics tab event listeners (if any)
 */
export function initMetrics() {
  // Currently read-only dashboard, so no inputs to bind
}

/**
 * Recalculate metrics and redraw charts
 */
export function refreshMetrics() {
  if (!state.leads || state.leads.length === 0) {
    clearKPIs();
    return;
  }

  // 1. Calculate and update KPIs
  calculateKPIs();

  // 2. Draw Lead Inflow Velocity Line Chart
  drawInflowChart();

  // 3. Draw Lead Aging Polar Area Chart
  drawAgingChart();
}

/**
 * Reset KPI elements when no data is loaded
 */
function clearKPIs() {
  kpiAvgEnrollDays.textContent = '-';
  kpiStaleLeads.textContent = '-';
  kpiLeadGrowth.textContent = '-';
}

/**
 * Calculate CRM operational KPIs
 */
function calculateKPIs() {
  const now = new Date();

  // --- KPI 1: Average Days to Enroll ---
  const enrolledLeads = state.leads.filter(l => l.stage === 'Enrolled');
  if (enrolledLeads.length > 0) {
    let totalDays = 0;
    enrolledLeads.forEach(lead => {
      const created = new Date(lead.created_at);
      const updated = new Date(lead.updated_at);
      const diffTime = Math.max(0, updated - created);
      const diffDays = diffTime / (1000 * 60 * 60 * 24);
      totalDays += diffDays;
    });
    const avg = (totalDays / enrolledLeads.length).toFixed(1);
    kpiAvgEnrollDays.textContent = `${avg} Days`;
  } else {
    kpiAvgEnrollDays.textContent = 'N/A';
  }

  // --- KPI 2: Stale Leads (> 7 Days since last update) ---
  const activeLeads = state.leads.filter(l => !['Enrolled', 'Lost'].includes(l.stage));
  let staleCount = 0;
  activeLeads.forEach(lead => {
    const lastUpdate = new Date(lead.updated_at || lead.created_at);
    const diffTime = now - lastUpdate;
    const diffDays = diffTime / (1000 * 60 * 60 * 24);
    if (diffDays > 7) {
      staleCount++;
    }
  });
  kpiStaleLeads.textContent = staleCount.toLocaleString();

  // --- KPI 3: Lead Growth (New Leads in last 30 Days) ---
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  const newLeadsLast30Days = state.leads.filter(l => new Date(l.created_at) >= thirtyDaysAgo).length;
  kpiLeadGrowth.textContent = `+${newLeadsLast30Days.toLocaleString()}`;
}

/**
 * Draw Lead Inflow Velocity (Cumulative Growth over time)
 */
function drawInflowChart() {
  const ctx = document.getElementById('leadInflowChart').getContext('2d');
  if (inflowChartInstance) {
    inflowChartInstance.destroy();
  }

  // Group leads by date (YYYY-MM-DD)
  const dateCounts = {};
  state.leads.forEach(lead => {
    const dateStr = lead.created_at.split('T')[0];
    dateCounts[dateStr] = (dateCounts[dateStr] || 0) + 1;
  });

  // Sort dates chronologically
  const sortedDates = Object.keys(dateCounts).sort();
  
  // Calculate cumulative counts
  let cumulative = 0;
  const cumulativeData = sortedDates.map(date => {
    cumulative += dateCounts[date];
    return cumulative;
  });

  const isLight = state.theme === 'light';
  const textColor = isLight ? '#1e293b' : '#f8fafc';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.05)';

  inflowChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: sortedDates.map(d => {
        const date = new Date(d);
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      }),
      datasets: [{
        label: 'Total Leads Cumulative',
        data: cumulativeData,
        fill: true,
        backgroundColor: 'rgba(59, 130, 246, 0.15)', // Light blue fill
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        tension: 0.3,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isLight ? '#ffffff' : '#1e293b',
          titleColor: isLight ? '#1e293b' : '#ffffff',
          bodyColor: isLight ? '#475569' : '#cbd5e1',
          borderColor: 'rgba(59, 130, 246, 0.3)',
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, maxRotation: 45, minRotation: 45 }
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, stepSize: 10 }
        }
      }
    }
  });
}

/**
 * Draw Lead Aging per Stage (Polar Area Chart of active leads duration)
 */
function drawAgingChart() {
  const ctx = document.getElementById('leadAgingChart').getContext('2d');
  if (agingChartInstance) {
    agingChartInstance.destroy();
  }

  const activeStages = ['New', 'Contacted', 'Qualified', 'Demo'];
  const now = new Date();

  // Group active leads and calculate average age in days
  const stageAges = activeStages.map(stage => {
    const stageLeads = state.leads.filter(l => l.stage === stage);
    if (stageLeads.length === 0) return 0;

    let totalAge = 0;
    stageLeads.forEach(lead => {
      const created = new Date(lead.created_at);
      const ageInDays = (now - created) / (1000 * 60 * 60 * 24);
      totalAge += ageInDays;
    });

    return parseFloat((totalAge / stageLeads.length).toFixed(1));
  });

  const isLight = state.theme === 'light';
  const textColor = isLight ? '#1e293b' : '#f8fafc';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

  agingChartInstance = new Chart(ctx, {
    type: 'polarArea',
    data: {
      labels: activeStages,
      datasets: [{
        label: 'Average Age (Days)',
        data: stageAges,
        backgroundColor: [
          'rgba(59, 130, 246, 0.65)',  // New - blue
          'rgba(168, 85, 247, 0.65)',  // Contacted - purple
          'rgba(249, 115, 22, 0.65)',  // Qualified - orange
          'rgba(234, 179, 8, 0.65)'    // Demo - yellow
        ],
        borderColor: isLight ? '#ffffff' : 'rgba(20, 26, 42, 0.8)',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: textColor }
        },
        tooltip: {
          backgroundColor: isLight ? '#ffffff' : '#1e293b',
          titleColor: isLight ? '#1e293b' : '#ffffff',
          bodyColor: isLight ? '#475569' : '#cbd5e1',
          borderColor: 'rgba(168, 85, 247, 0.3)',
          borderWidth: 1
        }
      },
      scales: {
        r: {
          grid: { color: gridColor },
          angleLines: { color: gridColor },
          pointLabels: {
            color: textColor,
            font: { size: 11 }
          },
          ticks: {
            backdropColor: 'transparent',
            color: textColor
          }
        }
      }
    }
  });
}
