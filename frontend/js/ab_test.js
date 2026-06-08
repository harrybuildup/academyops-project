// frontend/js/ab_test.js

import { state, showToast } from './app.js';

// DOM elements
const abSource1 = document.getElementById('ab-source-1');
const abSource2 = document.getElementById('ab-source-2');
const abAlpha = document.getElementById('ab-alpha');
const abRunBtn = document.getElementById('ab-run-btn');

const abResultsContainer = document.getElementById('ab-results-container');
const abSignificanceBadge = document.getElementById('ab-significance-badge');

const abSource1Name = document.getElementById('ab-source-1-name');
const abN1 = document.getElementById('ab-n1');
const abEnrolled1 = document.getElementById('ab-enrolled1');
const abRate1 = document.getElementById('ab-rate1');

const abSource2Name = document.getElementById('ab-source-2-name');
const abN2 = document.getElementById('ab-n2');
const abEnrolled2 = document.getElementById('ab-enrolled2');
const abRate2 = document.getElementById('ab-rate2');

const abZScore = document.getElementById('ab-z-score');
const abPValue = document.getElementById('ab-p-value');
const abAlphaVal = document.getElementById('ab-alpha-val');

const abConclusionBox = document.getElementById('ab-conclusion-box');
const abConclusionText = document.getElementById('ab-conclusion-text');

/**
 * Initialize A/B Testing event listeners
 */
export function initABTest() {
  abRunBtn.addEventListener('click', runHypothesisTest);
}

/**
 * Invoked on tab activation to load selections
 */
export function refreshABTest() {
  populateABSourceDropdowns();
}

/**
 * Populates Source A and Source B selection lists based on active lead data
 */
function populateABSourceDropdowns() {
  const currentVal1 = abSource1.value;
  const currentVal2 = abSource2.value;

  abSource1.innerHTML = '';
  abSource2.innerHTML = '';

  const sources = [...new Set(state.leads.map(lead => lead.source).filter(Boolean))].sort();

  if (sources.length === 0) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'No Sources Found';
    abSource1.appendChild(opt.cloneNode(true));
    abSource2.appendChild(opt.cloneNode(true));
    return;
  }

  sources.forEach(src => {
    const opt = document.createElement('option');
    opt.value = src;
    opt.textContent = src;
    abSource1.appendChild(opt.cloneNode(true));
    abSource2.appendChild(opt.cloneNode(true));
  });

  // Restore previous selections or choose sensible defaults
  if (sources.includes(currentVal1)) {
    abSource1.value = currentVal1;
  } else {
    abSource1.value = sources[0] || '';
  }

  if (sources.includes(currentVal2)) {
    abSource2.value = currentVal2;
  } else {
    // Select second item if possible
    abSource2.value = sources[1] || sources[0] || '';
  }
}

/**
 * Approximates cumulative density function (CDF) for the standard normal distribution
 * Uses Abramowitz & Stegun formula 26.2.17
 */
function standardNormalCDF(x) {
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989422804; // 1 / sqrt(2 * pi)
  const p = d * Math.exp(-0.5 * x * x);
  const c = p * t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  return x >= 0 ? 1 - c : c;
}

/**
 * Performs a two-proportion z-test and renders results
 */
function runHypothesisTest() {
  const source1 = abSource1.value;
  const source2 = abSource2.value;
  const alpha = parseFloat(abAlpha.value);

  if (!source1 || !source2) {
    showToast('Please select two valid lead sources to test.', 'error');
    return;
  }

  if (source1 === source2) {
    showToast('Please select two different sources for comparison.', 'error');
    return;
  }

  // 1. Gather counts
  const leads1 = state.leads.filter(l => l.source === source1);
  const leads2 = state.leads.filter(l => l.source === source2);

  const n1 = leads1.length;
  const n2 = leads2.length;

  const k1 = leads1.filter(l => l.stage === 'Enrolled').length;
  const k2 = leads2.filter(l => l.stage === 'Enrolled').length;

  if (n1 === 0 || n2 === 0) {
    showToast(`Test failed: One of the sources has 0 leads (${source1}: ${n1}, ${source2}: ${n2})`, 'error');
    return;
  }

  // 2. Perform z-test calculations
  const p1 = k1 / n1;
  const p2 = k2 / n2;

  const pPool = (k1 + k2) / (n1 + n2);
  const se = Math.sqrt(pPool * (1 - pPool) * (1 / n1 + 1 / n2));

  let z = 0.0;
  if (se > 0) {
    z = (p1 - p2) / se;
  }

  const pValue = 2 * (1 - standardNormalCDF(Math.abs(z)));
  const isSignificant = pValue < alpha;

  // 3. Render UI details
  abResultsContainer.classList.remove('hidden');

  if (isSignificant) {
    abSignificanceBadge.className = 'badge badge-success';
    abSignificanceBadge.textContent = 'Significant Difference';
    abConclusionBox.className = 'ab-conclusion-box';
    abConclusionBox.querySelector('i').className = 'fa-solid fa-circle-check';
  } else {
    abSignificanceBadge.className = 'badge badge-secondary';
    abSignificanceBadge.textContent = 'No Significant Difference';
    abConclusionBox.className = 'ab-conclusion-box not-significant';
    abConclusionBox.querySelector('i').className = 'fa-solid fa-circle-info';
  }

  // Source A stats
  abSource1Name.textContent = source1;
  abN1.textContent = n1.toLocaleString();
  abEnrolled1.textContent = k1.toLocaleString();
  abRate1.textContent = `${(p1 * 100).toFixed(1)}%`;

  // Source B stats
  abSource2Name.textContent = source2;
  abN2.textContent = n2.toLocaleString();
  abEnrolled2.textContent = k2.toLocaleString();
  abRate2.textContent = `${(p2 * 100).toFixed(1)}%`;

  // Math variables
  abZScore.textContent = z.toFixed(4);
  abPValue.textContent = pValue.toFixed(4);
  abAlphaVal.textContent = alpha.toFixed(2);

  // Conclusion statement
  const rateDiff = (p1 * 100).toFixed(1) + '% vs ' + (p2 * 100).toFixed(1) + '%';
  if (isSignificant) {
    abConclusionText.innerHTML = `
      <strong>Statistically Significant Result:</strong> There IS a statistically significant difference in enrollment rates between 
      <strong>${escapeHtml(source1)}</strong> (${(p1*100).toFixed(1)}%) and <strong>${escapeHtml(source2)}</strong> (${(p2*100).toFixed(1)}%) 
      at a significance level of &alpha;=${alpha} (z=${z.toFixed(2)}, p=${pValue.toFixed(4)} &lt; &alpha;).
    `;
  } else {
    abConclusionText.innerHTML = `
      <strong>No Statistically Significant Result:</strong> There is NO statistically significant difference in enrollment rates between 
      <strong>${escapeHtml(source1)}</strong> (${(p1*100).toFixed(1)}%) and <strong>${escapeHtml(source2)}</strong> (${(p2*100).toFixed(1)}%) 
      at a significance level of &alpha;=${alpha} (z=${z.toFixed(2)}, p=${pValue.toFixed(4)} &ge; &alpha;). This suggests any observed difference could be due to random variation.
    `;
  }

  showToast('Hypothesis test computed.', 'success');
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
