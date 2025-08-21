// static/js/pendingDeletions.js
(function () {
  function getCookie(name) {
    const row = document.cookie.split('; ').find(r => r.startsWith(name + '='));
    return row ? decodeURIComponent(row.split('=')[1]) : null;
  }
  const csrftoken = getCookie('csrftoken');

  async function postJson(url) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json'
      },
      credentials: 'same-origin',
    });

    const text = await resp.text(); // robust against server HTML error pages
    let data = null;
    if (text) {
      try { data = JSON.parse(text); }
      catch (e) {
        console.error('Non-JSON response:', text);
      }
    }
    return { status: resp.status, data };
  }

  document.addEventListener('click', async function (ev) {
    const a = ev.target.closest && ev.target.closest('.js-cancel-delete');
    if (!a) return;
    ev.preventDefault();

    const pk = a.dataset.pk;
    if (!pk) return;

    if (!confirm('Undo delete? This will restore the boat to the main list.')) return;

    // UX: disable while processing
    const tr = a.closest('tr');
    const orig = a.textContent;
    a.textContent = 'Undoing…';
    a.style.pointerEvents = 'none';
    a.setAttribute('aria-busy', 'true');

    const url = `/pending_deletions/${pk}/cancel_delete/`;  // ← your urls.py
    try {
      const { status, data } = await postJson(url);
      if (status >= 200 && status < 300 && data && data.ok) {
        // success → remove row from Pending Deletions
        tr && tr.remove();
      } else {
        const msg = (data && data.error) ? data.error : 'Undo failed (server error).';
        alert(msg);
        a.textContent = orig;
        a.style.pointerEvents = '';
        a.removeAttribute('aria-busy');
      }
    } catch (err) {
      console.error(err);
      alert('Network error while undoing delete.');
      a.textContent = orig;
      a.style.pointerEvents = '';
      a.removeAttribute('aria-busy');
    }
  });
})();
