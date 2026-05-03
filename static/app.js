const counters = document.querySelectorAll('[data-count]');

counters.forEach((counter) => {
  const target = Number(counter.dataset.count || 0);
  counter.textContent = '0';

  const step = () => {
    const current = Number(counter.textContent || 0);
    const next = Math.min(target, current + Math.ceil(target / 24));
    counter.textContent = String(next);

    if (next < target) {
      window.requestAnimationFrame(step);
    }
  };

  window.requestAnimationFrame(step);
});
