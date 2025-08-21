// static/js/boatDelete.js
(function () {
  const dialog = document.getElementById('boatDeleteDialog');
  const form   = document.getElementById('boatDeleteForm');
  const msg    = document.getElementById('boatDeleteMessage');
  const pkInput = document.getElementById('boatDeletePk');
  const btnNo  = document.getElementById('boatDeleteNo');

  if (!dialog || !form) return;

  // helper: read csrftoken from cookie
  function getCookie(name) {
    const v = document.cookie.split('; ').find(row => row.startsWith(name + '='));
    return v ? decodeURIComponent(v.split('=')[1]) : null;
  }
  const csrftoken = getCookie('csrftoken');

  // open dialog with data from the clicked row
  document.addEventListener('click', function (ev) {
    const el = ev.target.closest && ev.target.closest('.js-boat-delete');
    if (!el) return;
    ev.preventDefault();

    const pk = el.dataset.boatId;
    const tr = el.closest('tr');          // 'el' is the clicked .js-boat-delete element
    dialog._rowToDelete = tr;
    const type = el.dataset.boatType || '';
    const name = el.dataset.boatName || '';
    const berth = el.dataset.boatBerth || '';


    console.log(type, name, berth);
    pkInput.value = pk;
    msg.textContent = `Are you sure you want to delete '${type}' '${name}' at '${berth}'?`;

    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', 'open');

    // focus Yes button
    const yes = document.getElementById('boatDeleteYes');
    if (yes) yes.focus();
  });

  // No button closes the dialog
  btnNo?.addEventListener('click', function (e) {
    e.preventDefault();
    if (typeof dialog.close === 'function') dialog.close();
    else dialog.removeAttribute('open');
  });

  // Submit handler: do AJAX POST to soft-delete endpoint
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const pk = pkInput.value;
    if (!pk) return;

    const url = `/boats/${pk}/soft-delete/`;
    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json',
      },
      credentials: 'same-origin',
    })
    .then(resp => resp.json().then(data => ({status: resp.status, ok: resp.ok, data})))
    .then(({status, ok, data}) => {
      if (status >= 200 && status < 300 && data.ok) {
        // Update UI: remove row or mark as deleted
        console.log('-1');
        const tr = dialog._rowToDelete;
        if (tr) {
          // Option A: remove row
          console.log('0');
          tr.remove();
          dialog._rowToDelete = null;

//          // Option B: mark row visually as deleted and disable actions
//          tr.classList.add('deleted');
//          const deleteLinks = tr.querySelectorAll('.js-boat-delete');
//          deleteLinks.forEach(a => a.remove());
//          // optionally add a badge
//          const cell = tr.querySelector('td:last-child') || tr;
//          const span = document.createElement('span');
//          span.textContent = 'Deleted';
//          span.className = 'badge badge-danger';
//          cell.appendChild(span);
        }
        console.log('1');
        if (typeof dialog.close === 'function') dialog.close();

      } else {
        // show error
        console.log('2');
        alert(data?.error || 'Delete failed');
      }
    })
    .catch(err => {
      console.error(err);
      alert('Network error');
    });
  });
})();
