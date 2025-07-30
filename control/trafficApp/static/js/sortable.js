document.addEventListener('DOMContentLoaded', () => {
  const form       = document.getElementById('searchForm');
  const input      = document.getElementById('searchInput');
  const clearBtn   = document.getElementById('clearBtn');

  clearBtn.addEventListener('click', () => {
    input.value = '';      // 1) Clear the text box
    form.submit();         // 2) Submit the form (runs the GET without any q parameter)
  });
});

function makeTableSortable(table) {
  const ths = table.tHead.rows[0].cells;
  for (let i = 0; i < ths.length; i++) {
    ths[i].addEventListener('click', () => {
      sortTableByColumn(table, i);
    });
  }
}

function sortTableByColumn(table, columnIndex) {
  const dir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
  table.dataset.sortDir = dir;
  const multiplier = dir === 'asc' ? 1 : -1;
  const tbody = table.tBodies[0];
  Array.from(tbody.querySelectorAll('tr'))
    .sort((a, b) => {
      const aText = a.cells[columnIndex].innerText.trim();
      const bText = b.cells[columnIndex].innerText.trim();
      const aVal = isNaN(aText) ? aText : parseFloat(aText);
      const bVal = isNaN(bText) ? bText : parseFloat(bText);
      return aVal > bVal ? (1 * multiplier) : (-1 * multiplier);
    })
    .forEach(row => tbody.appendChild(row));
}

function initSortable() {
  document.querySelectorAll('table.sortable').forEach(makeTableSortable);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSortable);
} else {
  initSortable();  // DOM already parsed
}