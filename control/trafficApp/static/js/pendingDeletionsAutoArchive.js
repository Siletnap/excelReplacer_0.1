// static/js/pendingDeletionsAutoArchive.js
(function () {
  // Configuration
  const AUTO_ARCHIVE_HOURS =  48 * 60 * 60 * 1000;       // hours until archive
  const CHECK_INTERVAL_MS = 1000;  // 5 * 60 * 1000; // 5 minutes
  const ARCHIVE_ENDPOINT_BASE = '/pending_deletions/'; // we'll POST to `${base}${pk}/archive/`

  // Helpers
  function getCookie(name) {
    const cookie = document.cookie.split('; ').find(c => c.trim().startsWith(name + '='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
  }
  const csrftoken = getCookie('csrftoken');

  function parseISO(s) {
    // new Date('2025-08-21T12:34:56+00:00') works in modern browsers
    const d = s ? new Date(s) : null;
    return (d && !isNaN(d.getTime())) ? d : null;
  }

  function formatHHMMSS(totalMs) {
    if (totalMs <= 0) return '00:00:00';
    const totalSec = Math.floor(totalMs / 1000);
    const hh = String(Math.floor(totalSec / 3600)).padStart(2, '0');
    const mm = String(Math.floor((totalSec % 3600) / 60)).padStart(2, '0');
    const ss = String(totalSec % 60).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  }

  // Queue to serialize archive requests (so we don't hammer the DB in parallel)
  const archiveQueue = [];
  let queueRunning = false;

  async function runArchiveQueue() {
    if (queueRunning) return;
    queueRunning = true;
    while (archiveQueue.length > 0) {
      const { pk, tr } = archiveQueue.shift();
      try {
        await archiveBoat(pk, tr);
      } catch (err) {
        console.error('Archive failed for pk', pk, err);
        // If archiving fails, don't block others — continue loop.
      }
    }
    queueRunning = false;
  }

  // Archive a single boat via POST and remove its row on success
  async function archiveBoat(pk, tr) {
    const url = `${ARCHIVE_ENDPOINT_BASE}${encodeURIComponent(pk)}/archive/`;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'Accept': 'application/json',
        },
        credentials: 'same-origin',
      });

      const text = await resp.text();
      let data = null;
      if (text) {
        try { data = JSON.parse(text); } catch (e) { /* ignore */ }
      }

      if (resp.ok && data && data.ok) {
        // success: remove row from DOM
        tr && tr.remove();
        console.info(`Archived boat ${pk}`);
        return true;
      } else {
        console.warn('Archive endpoint returned error', resp.status, data);
        return false;
      }
    } catch (err) {
      console.error('Network error archiving boat', pk, err);
      return false;
    }
  }

  // For each pending row, update remaining-time cell and schedule archive if expired
  function scanAndUpdate() {
    const rows = Array.from(document.querySelectorAll('tr[data-pk][data-deleted-at]'));
    if (!rows.length) return;

    const now = new Date();
    const deadlineMs = AUTO_ARCHIVE_HOURS;

    rows.forEach(row => {
      const pk = row.getAttribute('data-pk');
      const deletedAtStr = row.getAttribute('data-deleted-at');
      const tr = row;
      const remainingCell = row.querySelector('.remaining-time');

      const deletedAt = parseISO(deletedAtStr);
      if (!deletedAt) {
        if (remainingCell) remainingCell.textContent = '--:--:--';
        return;
      }

      const elapsed = now - deletedAt;
      const remainingMs = deadlineMs - elapsed;

      if (remainingCell) remainingCell.textContent = formatHHMMSS(remainingMs);

      if (remainingMs <= 0) {
        // row expired → queue archived action (but only if row still present)
        // Avoid enqueueing duplicates: mark a flag on the tr
        if (!tr.__archive_queued) {
          tr.__archive_queued = true;
          archiveQueue.push({ pk, tr });
          runArchiveQueue().catch(err => console.error(err));
        }
      }
    });
  }

  // Start: initial scan + periodic timer
  document.addEventListener('DOMContentLoaded', function () {
    // initial run
    scanAndUpdate();
    // periodic runs every CHECK_INTERVAL_MS
    setInterval(scanAndUpdate, CHECK_INTERVAL_MS);
  });

  // Also listen for Undo events (if your Undo JS removes the row, the scan will skip it naturally)
  // Optionally, you can listen for a custom event to cancel queued archives for that pk if needed.

})();
