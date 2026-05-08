/* Campaign Analysis — UI interactions */

// ── Accordion ──────────────────────────────────────────────────────────────
document.querySelectorAll('.accordion-trigger').forEach(trigger => {
  trigger.addEventListener('click', () => {
    const body = trigger.nextElementSibling;
    const isOpen = trigger.classList.contains('open');

    // Close all in same accordion group
    const group = trigger.closest('.accordion');
    if (group) {
      group.querySelectorAll('.accordion-trigger').forEach(t => t.classList.remove('open'));
      group.querySelectorAll('.accordion-body').forEach(b => b.classList.remove('open'));
    }

    // Toggle clicked
    if (!isOpen) {
      trigger.classList.add('open');
      body.classList.add('open');
    }
  });
});

// Open first accordion item in each group by default
document.querySelectorAll('.accordion').forEach(group => {
  const first = group.querySelector('.accordion-trigger');
  const firstBody = group.querySelector('.accordion-body');
  if (first && firstBody) {
    first.classList.add('open');
    firstBody.classList.add('open');
  }
});

// ── Chart Lightbox ────────────────────────────────────────────────────────
const overlay = document.getElementById('lightbox-overlay');
const overlayImg = document.getElementById('lightbox-img');

document.querySelectorAll('.chart-block img').forEach(img => {
  img.addEventListener('click', () => {
    overlayImg.src = img.src;
    overlay.classList.add('active');
  });
});

overlay.addEventListener('click', () => overlay.classList.remove('active'));

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') overlay.classList.remove('active');
});

// ── Smooth scroll offset for sticky nav ──────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', e => {
    const target = document.querySelector(link.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - 72;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});

// ── Number formatting helper ──────────────────────────────────────────────
function formatEur(value) {
  if (value === null || value === undefined) return 'N/A';
  if (Math.abs(value) >= 1e6) return `€${(value / 1e6).toFixed(1)}M`;
  if (Math.abs(value) >= 1e3) return `€${(value / 1e3).toFixed(0)}K`;
  return `€${value.toFixed(0)}`;
}
