  (function () {
    const form = document.getElementById('traffic-controls');
    if (!form) return;

    const modeRadios = form.querySelectorAll('input[name="mode"]');
    const perInput   = form.querySelector('input[name="per"]');
    const invertBtn  = document.getElementById('invert-btn');
    const dirInput   = document.getElementById('dir');
    const sortSelect = document.getElementById('sort');

    function updatePerDisabled() {
      const mode = [...modeRadios].find(r => r.checked)?.value;
      perInput.disabled = (mode !== 'per');
    }
    modeRadios.forEach(r => r.addEventListener('change', () => {
      updatePerDisabled();
      // When changing mode, reset to page 1 by removing any ?page= from URL on submit.
      form.querySelectorAll('input[name="page"]').forEach(x => x.remove());
      form.submit();
    }));
    updatePerDisabled();

    invertBtn?.addEventListener('click', () => {
      dirInput.value = (dirInput.value === 'asc') ? 'desc' : 'asc';
      // Reset to page 1 on sort change
      form.querySelectorAll('input[name="page"]').forEach(x => x.remove());
      form.submit();
    });

    sortSelect?.addEventListener('change', () => {
      // Reset to page 1 when sort key changes
      form.querySelectorAll('input[name="page"]').forEach(x => x.remove());
      form.submit();
    });
  })();