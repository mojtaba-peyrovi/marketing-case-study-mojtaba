/* Marketing Performance Diagnostic — Chart.js wiring
   Reads window.DASHBOARD (embedded JSON from server) and renders three charts:
   1. Efficiency gap (indexed line)
   2. Meta deep dive (bar + line dual-axis)
   3. Q4 cost-vs-quality quadrant scatter (bubble)
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
            title: {
              display: true,
              text: 'Index (January 2024 = 100)',
              color: '#7A7068',
              font: { size: 11, weight: '600', family: "'Inter', sans-serif" }
            },
            ticks: {
              callback: function(v) { return v; }
            }
          },
          x: { grid: { display: false } }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(ctx) {
                return ctx.dataset.label + ': ' + ctx.parsed.y + ' (Jan = 100)';
              }
            }
          }
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

  // ── Q4 quadrant scatter: cost vs quality ─────────────────────────────────
  const quadCtx = document.getElementById('quadrantChart');
  if (quadCtx && D.q4_quadrant) {
    const Q = D.q4_quadrant;

    // Quadrant palette (lavender-on-good, coral-on-bad).
    const QUADRANT_FILL = {
      efficient_high_quality: '#7C5CB8', // deep lavender — best
      premium:                '#B9A3E0', // light lavender
      cheap_moderate:         '#C9BBA8', // muted neutral
      wasted_spend:           '#FF4A1F', // coral — worst
    };
    const QUADRANT_BG = {
      efficient_high_quality: 'rgba(124, 92, 184, 0.08)',
      premium:                'rgba(185, 163, 224, 0.10)',
      cheap_moderate:         'rgba(201, 187, 168, 0.12)',
      wasted_spend:           'rgba(255, 74, 31, 0.07)',
    };
    const QUADRANT_TITLE = {
      efficient_high_quality: 'Efficient + High Quality',
      premium:                'Premium — quality at a price',
      cheap_moderate:         'Cheap entry, moderate quality',
      wasted_spend:           'Wasted spend',
    };

    // Axis ranges — fixed so reference lines and labels stay in known positions.
    const X_MIN = 0, X_MAX = 80;
    const Y_MIN = 15, Y_MAX = 35;

    // Bubble radius: sqrt-scaled by spend (so a 100x spend gap reads as 10x area, not 100x).
    const maxSpend = Math.max(...Q.points.map(p => p.spend));
    const R_MIN = 9, R_MAX = 40;
    const radius = (spend) =>
      R_MIN + (R_MAX - R_MIN) * Math.sqrt(Math.max(spend, 1) / maxSpend);

    const scatterData = Q.points.map(p => ({
      x: p.cac,
      y: p.t2p_pct,
      r: radius(p.spend),
      _channel: p.channel,
      _spend: p.spend,
      _share: p.spend_share_pct,
      _quadrant: p.quadrant,
    }));

    // Plugin · paint quadrant backgrounds + median reference lines + corner labels.
    const quadrantBackdrop = {
      id: 'quadrantBackdrop',
      beforeDatasetsDraw(chart) {
        const { ctx, chartArea, scales: { x, y } } = chart;
        if (!chartArea) return;
        const xMid = x.getPixelForValue(Q.median_cac);
        const yMid = y.getPixelForValue(Q.median_t2p_pct);

        ctx.save();
        // 4 quadrant background fills
        ctx.fillStyle = QUADRANT_BG.efficient_high_quality;
        ctx.fillRect(chartArea.left, chartArea.top, xMid - chartArea.left, yMid - chartArea.top);
        ctx.fillStyle = QUADRANT_BG.premium;
        ctx.fillRect(xMid, chartArea.top, chartArea.right - xMid, yMid - chartArea.top);
        ctx.fillStyle = QUADRANT_BG.cheap_moderate;
        ctx.fillRect(chartArea.left, yMid, xMid - chartArea.left, chartArea.bottom - yMid);
        ctx.fillStyle = QUADRANT_BG.wasted_spend;
        ctx.fillRect(xMid, yMid, chartArea.right - xMid, chartArea.bottom - yMid);

        // Median reference lines
        ctx.strokeStyle = '#7A7068';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(xMid, chartArea.top);
        ctx.lineTo(xMid, chartArea.bottom);
        ctx.moveTo(chartArea.left, yMid);
        ctx.lineTo(chartArea.right, yMid);
        ctx.stroke();
        ctx.setLineDash([]);

        // Corner labels
        ctx.font = "600 11px 'Inter', sans-serif";
        ctx.fillStyle = '#7A7068';
        const pad = 8;
        ctx.textBaseline = 'top';
        ctx.textAlign = 'left';
        ctx.fillText(QUADRANT_TITLE.efficient_high_quality, chartArea.left + pad, chartArea.top + pad);
        ctx.textAlign = 'right';
        ctx.fillText(QUADRANT_TITLE.premium, chartArea.right - pad, chartArea.top + pad);
        ctx.textBaseline = 'bottom';
        ctx.textAlign = 'left';
        ctx.fillText(QUADRANT_TITLE.cheap_moderate, chartArea.left + pad, chartArea.bottom - pad);
        ctx.textAlign = 'right';
        ctx.fillStyle = '#FF4A1F';
        ctx.fillText(QUADRANT_TITLE.wasted_spend, chartArea.right - pad, chartArea.bottom - pad);

        // Median tick label on the dashed lines
        ctx.fillStyle = '#7A7068';
        ctx.font = "500 10px 'Inter', sans-serif";
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('median CAC €' + Q.median_cac.toFixed(2),
                     xMid + 4, chartArea.bottom - 14);
        ctx.fillText('median t2p ' + Q.median_t2p_pct + '%',
                     chartArea.left + 4, yMid - 14);

        ctx.restore();
      }
    };

    // Plugin · channel name labels next to each bubble.
    const channelLabels = {
      id: 'channelLabels',
      afterDatasetsDraw(chart) {
        const { ctx } = chart;
        const meta = chart.getDatasetMeta(0);
        ctx.save();
        ctx.font = "600 11px 'Inter', sans-serif";
        ctx.fillStyle = '#1A1714';
        ctx.textBaseline = 'middle';
        meta.data.forEach((point, i) => {
          const d = scatterData[i];
          const r = d.r;
          // Place label to the right of the bubble, except for FB/Insta
          // which is far right — put its label to the left.
          const isFarRight = d.x > 60;
          ctx.textAlign = isFarRight ? 'right' : 'left';
          const tx = isFarRight ? point.x - r - 6 : point.x + r + 6;
          ctx.fillText(d._channel, tx, point.y);
        });
        ctx.restore();
      }
    };

    new Chart(quadCtx, {
      type: 'bubble',
      data: {
        datasets: [{
          label: 'Paid channel',
          data: scatterData,
          backgroundColor: scatterData.map(d => QUADRANT_FILL[d._quadrant] + 'CC'), // ~80% alpha
          borderColor:     scatterData.map(d => QUADRANT_FILL[d._quadrant]),
          borderWidth: 1.5,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 8, right: 12, bottom: 8, left: 8 } },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: items => items[0].raw._channel,
              label: ctx => {
                const d = ctx.raw;
                return [
                  'CAC: €' + d.x.toFixed(2),
                  'Trial-to-paid: ' + d.y.toFixed(1) + '%',
                  'Spend: €' + d._spend.toLocaleString('en-US', {maximumFractionDigits: 0}) + ' (' + d._share.toFixed(2) + '% of paid)',
                  'Quadrant: ' + QUADRANT_TITLE[d._quadrant],
                ];
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            min: X_MIN, max: X_MAX,
            grid: { color: '#E6DCD0', drawBorder: false },
            title: { display: true, text: 'CAC (€) — cost to acquire one paying subscriber',
                     color: '#7A7068', font: { size: 11, weight: '600' } },
            ticks: { callback: v => '€' + v }
          },
          y: {
            min: Y_MIN, max: Y_MAX,
            grid: { color: '#E6DCD0', drawBorder: false },
            title: { display: true, text: 'Trial-to-paid (%) — share of yearly trials that convert',
                     color: '#7A7068', font: { size: 11, weight: '600' } },
            ticks: { callback: v => v + '%' }
          }
        }
      },
      plugins: [quadrantBackdrop, channelLabels]
    });
  }
})();
