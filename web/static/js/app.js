/* Marketing Performance Diagnostic — Chart.js wiring
   Reads window.DASHBOARD (embedded JSON from server) and renders three charts:
   1. Efficiency gap (indexed line)
   2. Meta deep dive (bar + line dual-axis)
   3. Trial-to-paid by channel (horizontal bar)
*/

(function () {
  if (!window.DASHBOARD) return;
  const D = window.DASHBOARD;

  // ── Global Chart.js style ──────────────────────────────────────────────
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 11;
  Chart.defaults.color = '#7A7068';
  Chart.defaults.plugins.legend.position = 'bottom';
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.legend.labels.font = { size: 12, family: "'Inter', sans-serif" };
  Chart.defaults.plugins.tooltip.backgroundColor = '#1A1714';
  Chart.defaults.plugins.tooltip.padding = 12;
  Chart.defaults.plugins.tooltip.titleFont = { weight: 'bold', size: 13 };
  Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
  Chart.defaults.plugins.tooltip.cornerRadius = 8;

  const months = D.efficiency.months;

  // ── Efficiency gap chart ───────────────────────────────────────────────
  const efCtx = document.getElementById('efficiencyChart');
  if (efCtx) {
    new Chart(efCtx, {
      type: 'line',
      data: {
        labels: months,
        datasets: [
          {
            label: 'Marketing Spend',
            data: D.efficiency.spend_idx,
            borderColor: '#FF4A1F',
            backgroundColor: 'rgba(255, 74, 31, 0.06)',
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#FF4A1F',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
          },
          {
            label: 'Paid Conversions',
            data: D.efficiency.conv_idx,
            borderColor: '#B9A3E0',
            backgroundColor: 'rgba(185, 163, 224, 0.08)',
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#B9A3E0',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#E6DCD0', drawBorder: false },
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // ── Meta deep-dive chart ───────────────────────────────────────────────
  const metaCtx = document.getElementById('metaChart');
  if (metaCtx) {
    new Chart(metaCtx, {
      data: {
        labels: D.meta.months,
        datasets: [
          {
            type: 'bar',
            label: 'Meta Spend (€)',
            data: D.meta.spend_series,
            backgroundColor: 'rgba(185, 163, 224, 0.85)',
            borderRadius: 4,
            yAxisID: 'y',
            order: 2
          },
          {
            type: 'line',
            label: 'Meta CAC (€)',
            data: D.meta.cac_series,
            borderColor: '#FF4A1F',
            backgroundColor: '#FF4A1F',
            borderWidth: 3.5,
            tension: 0.3,
            pointBackgroundColor: '#FF4A1F',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 5,
            yAxisID: 'y1',
            order: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: {
            position: 'left',
            beginAtZero: true,
            grid: { color: '#E6DCD0', drawBorder: false },
            ticks: { callback: v => '€' + (v / 1000).toFixed(0) + 'k' },
            title: { display: true, text: 'Spend', color: '#7A7068', font: { size: 11 } }
          },
          y1: {
            position: 'right',
            beginAtZero: true,
            max: 100,
            grid: { display: false },
            ticks: { callback: v => '€' + v, color: '#FF4A1F' },
            title: { display: true, text: 'CAC', color: '#FF4A1F', font: { size: 11 } }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // ── Trial-to-paid horizontal bar ───────────────────────────────────────
  const t2pCtx = document.getElementById('t2pChart');
  if (t2pCtx) {
    const colorMap = {
      paid_good: '#1F7A4D',
      paid:      '#FF4A1F',
      paid_warn: '#C25A00',
      organic:   '#B9A3E0',
    };
    const data = D.trial_to_paid;
    new Chart(t2pCtx, {
      type: 'bar',
      data: {
        labels: data.map(d => d.channel),
        datasets: [{
          label: 'Trial-to-Paid %',
          data: data.map(d => d.t2p_pct),
          backgroundColor: data.map(d => colorMap[d.category] || '#B9A3E0'),
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => ctx.parsed.x.toFixed(1) + '%' } }
        },
        scales: {
          x: {
            beginAtZero: true,
            max: 35,
            ticks: { callback: v => v + '%' },
            grid: { color: '#E6DCD0', drawBorder: false }
          },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } }
        }
      }
    });
  }
})();
