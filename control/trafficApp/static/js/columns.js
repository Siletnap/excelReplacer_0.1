document.addEventListener('DOMContentLoaded', () => {
  const STORAGE_KEY = 'visibleColumns';
  const table       = document.querySelector('table.boats');
  const checkboxes  = document.querySelectorAll('.col-toggle');
  const applyBtn    = document.getElementById('apply-columns');
  const clearBtn    = document.getElementById('clearBtn');

  // On load, restore saved or default all-visible
  const saved       = JSON.parse(localStorage.getItem(STORAGE_KEY));
  const defaultCols = Array.from(checkboxes)
                            .map(cb => Number(cb.dataset.colIndex));
  const initialCols = Array.isArray(saved) ? saved : defaultCols;
  applyVisibility(initialCols);

  // On Apply click: compute visible indices, apply & persist
  applyBtn.addEventListener('click', () => {
    const visible = Array.from(checkboxes)
                         .filter(cb => cb.checked)
                         .map(cb => Number(cb.dataset.colIndex));
    applyVisibility(visible);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(visible));  // :contentReference[oaicite:4]{index=4}
  });

  clearBtn.addEventListener('click', () => {
    const allcb = Array.from(checkboxes).map(cb => Number(cb.dataset.colIndex));
    allcb.forEach(cb => {
        cb.checked = true;
    });
    applyVisibility(allcb);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(allcb));  // :contentReference[oaicite:4]{index=4}
  });

  // The function from above
  function applyVisibility(indices) {
    checkboxes.forEach(cb => {
      const idx  = Number(cb.dataset.colIndex);
      const show = indices.includes(idx);
      const th   = table.querySelector(`th[data-col-index="${idx}"]`);
      th.style.display = show ? '' : 'none';
      table.querySelectorAll(`td[data-col-index="${idx}"]`)
           .forEach(td => td.style.display = show ? '' : 'none');
    });
    checkboxes.forEach(cb => {
      cb.checked = indices.includes(Number(cb.dataset.colIndex));
    });
  }
});
