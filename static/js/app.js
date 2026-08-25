/**
 * Loan Approval ML Prediction UI JavaScript
 * Synchronizes inputs, preset loader, API prediction calls, and risk gauge visual updates.
 */

let riskGaugeChart = null;

document.addEventListener('DOMContentLoaded', () => {
  initFormControls();
  fetchSampleProfiles();
  initRiskGaugeChart(85); // Default display initialization
  
  // Submit handler
  const form = document.getElementById('loanForm');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    handlePrediction();
  });

  // Run initial prediction
  handlePrediction();
});

/** Synchronize Sliders & Text Inputs */
function initFormControls() {
  const syncPairs = [
    { input: 'age', slider: 'age_slider' },
    { input: 'person_income', slider: 'person_income_slider' },
    { input: 'loan_amount', slider: 'loan_amount_slider' },
    { input: 'loan_interest_rate', slider: 'loan_interest_rate_slider' },
    { input: 'credit_history', slider: 'credit_history_slider' },
    { input: 'credit_score', slider: 'credit_score_slider' }
  ];

  syncPairs.forEach(pair => {
    const inputEl = document.getElementById(pair.input);
    const sliderEl = document.getElementById(pair.slider);

    if (inputEl && sliderEl) {
      sliderEl.addEventListener('input', () => {
        inputEl.value = sliderEl.value;
        updateCalculatedRatio();
        updateLabelValues();
      });

      inputEl.addEventListener('input', () => {
        sliderEl.value = inputEl.value;
        updateCalculatedRatio();
        updateLabelValues();
      });
    }
  });

  const currencySelect = document.getElementById('currency');
  if (currencySelect) {
    currencySelect.addEventListener('change', () => {
      updateLabelValues();
      updateCalculatedRatio();
    });
  }

  updateLabelValues();
  updateCalculatedRatio();
}

/** Update Live Input Labels */
function updateLabelValues() {
  const currency = document.getElementById('currency')?.value || 'INR';
  const symbol = currency === 'INR' ? '₹' : '$';

  const incomeVal = parseFloat(document.getElementById('person_income')?.value || 0);
  const loanVal = parseFloat(document.getElementById('loan_amount')?.value || 0);

  const lblIncome = document.getElementById('lbl_person_income');
  const lblLoan = document.getElementById('lbl_loan_amount');

  if (lblIncome) lblIncome.textContent = `${symbol}${incomeVal.toLocaleString()}`;
  if (lblLoan) lblLoan.textContent = `${symbol}${loanVal.toLocaleString()}`;

  const lblAge = document.getElementById('lbl_age');
  const lblRate = document.getElementById('lbl_loan_interest_rate');
  const lblHistory = document.getElementById('lbl_credit_history');
  const lblScore = document.getElementById('lbl_credit_score');

  if (lblAge) lblAge.textContent = `${document.getElementById('age')?.value || 30} yrs`;
  if (lblRate) lblRate.textContent = `${document.getElementById('loan_interest_rate')?.value || 10}%`;
  if (lblHistory) lblHistory.textContent = `${document.getElementById('credit_history')?.value || 5} yrs`;
  if (lblScore) lblScore.textContent = `${document.getElementById('credit_score')?.value || 650} pts`;
}

/** Calculate Loan-to-Income Ratio dynamically */
function updateCalculatedRatio() {
  const income = parseFloat(document.getElementById('person_income')?.value || 1);
  const loan = parseFloat(document.getElementById('loan_amount')?.value || 0);

  const ratio = income > 0 ? (loan / income) * 100 : 0;
  const ratioEl = document.getElementById('calculated_ratio');
  const ratioBar = document.getElementById('calculated_ratio_bar');

  if (ratioEl) {
    ratioEl.textContent = `${ratio.toFixed(1)}%`;
  }
  if (ratioBar) {
    ratioBar.style.width = `${Math.min(ratio, 100)}%`;
    if (ratio > 30) {
      ratioBar.style.background = 'var(--accent-rose)';
    } else if (ratio > 15) {
      ratioBar.style.background = 'var(--accent-amber)';
    } else {
      ratioBar.style.background = 'var(--accent-emerald)';
    }
  }
}

/** Fetch Sample Presets from API */
async function fetchSampleProfiles() {
  try {
    const res = await fetch('/api/sample-data');
    const data = await res.json();

    if (data.status === 'success' && data.samples) {
      const container = document.getElementById('presetButtonsContainer');
      if (!container) return;

      container.innerHTML = '';
      data.samples.forEach(sample => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-preset';
        btn.innerHTML = `
          <strong>${sample.name}</strong>
          <span class="preset-tag">${sample.tag}</span>
        `;

        btn.addEventListener('click', () => {
          fillFormPreset(sample);
          handlePrediction();
        });

        container.appendChild(btn);
      });
    }
  } catch (err) {
    console.error('Error fetching sample profiles:', err);
  }
}

/** Fill form with preset data */
function fillFormPreset(sample) {
  document.getElementById('age').value = sample.age;
  document.getElementById('age_slider').value = sample.age;
  document.getElementById('gender').value = sample.gender;

  document.getElementById('person_income').value = sample.person_income;
  document.getElementById('person_income_slider').value = sample.person_income;

  document.getElementById('home_ownership').value = sample.home_ownership;

  document.getElementById('loan_amount').value = sample.loan_amount;
  document.getElementById('loan_amount_slider').value = sample.loan_amount;

  document.getElementById('loan_interest_rate').value = sample.loan_interest_rate;
  document.getElementById('loan_interest_rate_slider').value = sample.loan_interest_rate;

  document.getElementById('credit_history').value = sample.credit_history;
  document.getElementById('credit_history_slider').value = sample.credit_history;

  document.getElementById('credit_score').value = sample.credit_score;
  document.getElementById('credit_score_slider').value = sample.credit_score;

  document.getElementById('previous_loan').value = sample.previous_loan;

  updateLabelValues();
  updateCalculatedRatio();
}

/** Handle Prediction Form Submission */
async function handlePrediction() {
  const btnPredict = document.getElementById('btnPredict');
  const btnText = document.getElementById('btnPredictText');

  if (btnText) btnText.textContent = 'Evaluating Risk...';
  if (btnPredict) btnPredict.disabled = true;

  const payload = {
    age: parseFloat(document.getElementById('age').value),
    gender: document.getElementById('gender').value,
    person_income: parseFloat(document.getElementById('person_income').value),
    currency: document.getElementById('currency').value,
    home_ownership: document.getElementById('home_ownership').value,
    loan_amount: parseFloat(document.getElementById('loan_amount').value),
    loan_interest_rate: parseFloat(document.getElementById('loan_interest_rate').value),
    credit_history: parseFloat(document.getElementById('credit_history').value),
    credit_score: parseFloat(document.getElementById('credit_score').value),
    previous_loan: document.getElementById('previous_loan').value
  };

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.status === 'success' && data.prediction) {
      renderPredictionResults(data.prediction);
    } else {
      alert('Prediction Error: ' + (data.message || 'Unknown error'));
    }
  } catch (err) {
    console.error('API Error:', err);
  } finally {
    if (btnText) btnText.textContent = 'Predict Loan Approval';
    if (btnPredict) btnPredict.disabled = false;
  }
}

/** Render Prediction Outputs on UI */
function renderPredictionResults(pred) {
  const prob = pred.approval_probability;
  updateRiskGauge(prob, pred.status_color);

  // Score text
  const scoreEl = document.getElementById('gaugeScoreText');
  if (scoreEl) {
    scoreEl.textContent = `${prob.toFixed(1)}%`;
    scoreEl.style.color = pred.status_color === 'emerald' ? 'var(--accent-emerald)' : 
                          pred.status_color === 'amber' ? 'var(--accent-amber)' : 'var(--accent-rose)';
  }

  // Status badge
  const badgeEl = document.getElementById('statusBadge');
  if (badgeEl) {
    badgeEl.textContent = `${pred.status_badge} (${pred.risk_tier})`;
    badgeEl.className = `status-badge-lg badge-${pred.status_color}`;
  }

  // Description
  const descEl = document.getElementById('resultDescription');
  if (descEl) {
    descEl.textContent = pred.risk_description;
  }

  // Breakdown probabilities
  const txtApproved = document.getElementById('txtProbApproved');
  const txtRejected = document.getElementById('txtProbRejected');
  if (txtApproved) txtApproved.textContent = `${pred.approval_probability.toFixed(1)}%`;
  if (txtRejected) txtRejected.textContent = `${pred.rejection_probability.toFixed(1)}%`;

  // Render Key Risk Drivers
  const driversContainer = document.getElementById('keyDriversList');
  if (driversContainer && pred.key_drivers) {
    driversContainer.innerHTML = '';
    pred.key_drivers.forEach(driver => {
      const isPos = driver.impact === 'Positive';
      const item = document.createElement('div');
      item.className = 'driver-item';
      item.innerHTML = `
        <div class="driver-icon ${isPos ? 'positive' : 'negative'}">
          ${isPos ? '✓' : '✕'}
        </div>
        <div class="driver-text">
          <div class="driver-name">${driver.feature}</div>
          <div>${driver.desc}</div>
        </div>
      `;
      driversContainer.appendChild(item);
    });
  }
}

/** Chart.js Risk Gauge */
function initRiskGaugeChart(scoreVal) {
  const ctx = document.getElementById('riskGaugeCanvas');
  if (!ctx) return;

  const color = scoreVal >= 75 ? '#10b981' : scoreVal >= 45 ? '#f59e0b' : '#f43f5e';

  riskGaugeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [scoreVal, 100 - scoreVal],
        backgroundColor: [color, 'rgba(255, 255, 255, 0.06)'],
        borderWidth: 0,
        circumference: 240,
        rotation: 240
      }]
    },
    options: {
      cutout: '82%',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: { enabled: false }
      }
    }
  });
}

function updateRiskGauge(scoreVal, colorName) {
  if (!riskGaugeChart) {
    initRiskGaugeChart(scoreVal);
    return;
  }

  const hexColor = colorName === 'emerald' ? '#10b981' : colorName === 'amber' ? '#f59e0b' : '#f43f5e';

  riskGaugeChart.data.datasets[0].data = [scoreVal, 100 - scoreVal];
  riskGaugeChart.data.datasets[0].backgroundColor = [hexColor, 'rgba(255, 255, 255, 0.06)'];
  riskGaugeChart.update();
}
