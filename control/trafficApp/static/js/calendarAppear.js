document.addEventListener('DOMContentLoaded', () => {
    const typeInputs = document.querySelectorAll('input[name="booking_type"]');
    const dateDiv    = document.getElementById('date-fields');
    const timeDiv    = document.getElementById('time-fields');
    const cidInput   = document.getElementById('id_cid');

    function formatToday() {
        const today = new Date();
        const yyyy  = today.getFullYear();
        const mm    = String(today.getMonth() + 1).padStart(2, '0');
        const dd    = String(today.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;  // HTML date inputs use YYYY-MM-DD
    }

    function updateDateFields() {
        // Find the checked radio
        const selected = document.querySelector('input[name="booking_type"]:checked');
        if (selected && selected.value === 'daily_monthly') {
            dateDiv.style.display = 'block';
            document.getElementById('id_cid').removeAttribute('readonly');
            document.getElementById('id_ecod').removeAttribute('readonly');

            const today = formatToday();
            if (!cidInput.value)  cidInput.value  = today;

        } else {
            dateDiv.style.display = 'none';
        }
    }

    // 1) Attach change listeners
    typeInputs.forEach(radio =>
        radio.addEventListener('change', updateDateFields)
    );

    // 2) **Call once on load** to pick up the pre‑checked value
    updateDateFields();
});