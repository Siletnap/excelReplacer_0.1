// static/js/trafficSubmitForm.js
// Open + prefill the "New Traffic Entry" dialog from the clicked row,
// make some fields non-editable-but-submittable, then AJAX-submit with CSRF.
//
// Key behaviours:
// - Prefill Type/Name/Berth from the clicked row (data-* preferred, fallback to cells).
// - Make Name/Berth readonly (readonly fields are submitted).
// - Make Type non-interactive via CSS class (pointer-events:none) but keep it enabled so it submits.
// - Prefill date/time to now (format YYYY-MM-DD and HH:MM).
// - Prefill direction: if current state === 'in' => default 'out', else 'in'.
// - Submit with fetch() + FormData and X-CSRFToken header; show validation errors from server.

(function () {
  // ---- CSRF helper (Django docs pattern) ----
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(c.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  // ---- DOM handles ----
  const dlg  = document.getElementById('trafficDialog');
  const form = document.getElementById('trafficForm');
  const err  = document.getElementById('trafficErrors');

  // Helper: produce current date/time strings for input values.
  function nowForInputs() {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm   = String(d.getMonth() + 1).padStart(2, '0');
    const dd   = String(d.getDate()).padStart(2, '0');
    const hh   = String(d.getHours()).padStart(2, '0');
    const mi   = String(d.getMinutes()).padStart(2, '0');
    return { date: `${yyyy}-${mm}-${dd}`, time: `${hh}:${mi}` };
  }

  // Helper: read row values from the clicked link (prefer data-attrs).
  function readRowValues(linkEl) {
    let boatId   = linkEl.dataset.boatId    || '';
    let boatType = linkEl.dataset.boatType  || '';
    let name     = linkEl.dataset.boatName  || '';
    let berth    = linkEl.dataset.berth     || '';
    let state    = (linkEl.dataset.state    || '').toLowerCase();

    // fallback: read table cells if dataset values missing
    if (!boatType || !name || !berth || !state) {
      const row = linkEl.closest('tr');
      if (row) {
        const cells = Array.from(row.querySelectorAll('td'));
        boatType = boatType || (cells[0]?.textContent.trim() || '');
        name     = name     || (cells[1]?.textContent.trim() || '');
        berth    = berth    || (cells[2]?.textContent.trim() || '');
        state    = state    || (cells[3]?.textContent.trim().toLowerCase() || '');
      }
    }
    return {boatId, boatType, name, berth, state };
  }

  // Main: open/prefill dialog when Traffic link clicked
  document.addEventListener('click', (e) => {
    const link = e.target.closest('.js-traffic');
    if (!link) return;            // not a traffic click => ignore

    // stops page from jumping to # (href = '#')
    e.preventDefault();

    // 1) get data from row
    const { boatId, boatType: bt, name: nm, berth: br, state: st } = readRowValues(link);

    const hidBoatId = form.querySelector('#traffic_boat_id');
    if (hidBoatId) hidBoatId.value = boatId || '';

    // 2) element references inside dialog
    const selBoatType = form.querySelector('[name="boatType"]'); // select
    const inName      = form.querySelector('[name="name"]');     // text input
    const inBerth     = form.querySelector('[name="berth"]');    // text input
    const inDate      = form.querySelector('[name="trDate"]');   // date input
    const inTime      = form.querySelector('[name="trTime"]');   // time input
    const selDir      = form.querySelector('[name="direction"]');// select or input

    // 3) Prefill and lock boatType/name/berth
    if (selBoatType) {
      selBoatType.value = bt || '';

      // make the select non-interactive for pointer/ mouse; keep it enabled so its value is submitted
      selBoatType.classList.add('is-locked-pe');   // CSS class should set pointer-events:none
      selBoatType.setAttribute('tabindex', '-1');  // skip in tab order
      selBoatType.setAttribute('aria-disabled', 'true');
    }

    if (inName) {
      inName.value = nm || '';
      inName.readOnly = true;          // readonly fields are still submitted
      inName.classList.add('is-locked-text');
    }

    if (inBerth) {
      inBerth.value = br || '';
      inBerth.readOnly = true;
      inBerth.classList.add('is-locked-text');
    }

    // 4) Prefill date/time to now if empty (user can change)
    const now = nowForInputs();
    if (inDate && !inDate.value) inDate.value = now.date;   // format YYYY-MM-DD for date inputs
    if (inTime && !inTime.value) inTime.value = now.time;   // format HH:MM for time inputs

    // 5) Prefill direction: if 'in' => 'out', else 'in'
    if (selDir) selDir.value = (st === 'in') ? 'out' : 'in';

    // 6) blank other optional fields (passengers, purpose, edr, etr, etc.)
    const ids = ['id_passengers', 'id_purpose', 'id_edr', 'id_etr', 'id_trComments'];

    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) el.value = '';           // legal assignment (no optional chain on LHS)
    }

    // 7) clear errors and show dialog
    if (err) err.textContent = '';
    dlg?.showModal();
  });

  // Cancel button closes dialog
  document.getElementById('trafficCancel')?.addEventListener('click', () => dlg?.close());

  // AJAX submit (CreateView returns JSON for XHR)
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (err) err.textContent = '';

    try {
      const action = form.getAttribute('action');
      const formData = new FormData(form); // includes the CSRF hidden input rendered by Django

      const res = await fetch(action, {
        method: 'POST',
        body: formData,
        headers: {'X-Requested-With': 'XMLHttpRequest'},
        credentials: 'same-origin' // ensure cookies (if needed) are sent
      });

      if (res.ok) {
        dlg?.close();
        location.reload();
        return;
      }

      const data = await res.json().catch(() => ({}));
      if (data && data.errors) {
        err.innerHTML = Object.entries(data.errors)
          .map(([f, msgs]) => `${f}: ${msgs.join(', ')}`).join('<br>');
      } else {
        err.textContent = 'Could not save. Please try again.';
      }
    } catch (errFetch) {
      if (err) err.textContent = 'Network error. Please try again.';
      // optional: console.error(errFetch);
    }
  });
})();
