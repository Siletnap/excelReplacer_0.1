(function(){
const trigger = document.getElementById('js-day-jump');
const dialog  = document.getElementById('dayPickerDialog');
if (!trigger || !dialog) return;

function openPicker() {
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', 'open'); // very old fallback
  // Focus the date input when opened
  const input = dialog.querySelector('#dayPickerInput');
  if (input) setTimeout(() => input.focus(), 0);
}
function closePicker() {
  if (typeof dialog.close === 'function') dialog.close();
  else dialog.removeAttribute('open');
}

trigger.addEventListener('click', openPicker);
trigger.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openPicker(); }
});

dialog.addEventListener('cancel', (e) => { e.preventDefault(); closePicker(); });
const cancelBtn = dialog.querySelector('#dayPickerCancel');
if (cancelBtn) cancelBtn.addEventListener('click', closePicker);
})();
