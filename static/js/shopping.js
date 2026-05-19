// shopping.js — moved from template to avoid template parsing issues
(function(){
  const TOTAL = parseInt(document.getElementById('shopping-context')?.dataset?.total || 0, 10);
  let checkedCount = 0;

  function updateProgress() {
    const pct = TOTAL === 0 ? 0 : checkedCount / TOTAL;
    const offset = 283 - (pct * 283);
    const ringFill = document.getElementById('ring-fill');
    if (ringFill) ringFill.style.strokeDashoffset = offset;
    const ringNum = document.getElementById('ring-num');
    if (ringNum) ringNum.textContent = checkedCount;
    const progressSub = document.getElementById('progress-sub');
    if (progressSub) progressSub.textContent = `${checkedCount} of ${TOTAL} collected`;
  }

  function handleCheck(checkbox) {
    const row = checkbox.closest('.shop-item');
    if (checkbox.checked) {
      row.classList.add('bought');
      checkedCount++;
    } else {
      row.classList.remove('bought');
      checkedCount--;
    }
    updateProgress();
  }

  async function addToPantry(itemName, qtyId, unitId, btnId, row) {
    const qty  = parseFloat(document.getElementById(qtyId).value) || 1;
    const unit = document.getElementById(unitId).value;
    const btn  = document.getElementById(btnId);

    if (!btn) return;

    btn.disabled = true;
    btn.textContent = 'Adding...';

    try {
      const res  = await fetch('/pantry/add_from_shopping', {
        method:  'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ item_name: itemName, quantity: qty, unit: unit })
      });

      // handle non-JSON or auth redirects
      if (!res.ok) {
        let text = await res.text();
        throw new Error(`Server responded ${res.status}: ${text.slice(0,200)}`);
      }

      const data = await res.json();

      if (data && data.status === 'ok') {
        btn.outerHTML = `<span class="added-tick">✓ Added</span>`;
        if (row) {
          const cb = row.querySelector('.shop-checkbox');
          if (cb) cb.checked = true;
          row.classList.add('bought');
        }

        // Update progress
        checkedCount = document.querySelectorAll('.shop-item.bought').length;
        updateProgress();

        if (typeof showToast === 'function') showToast('✅ ' + data.message);
      } else {
        btn.disabled = false;
        btn.textContent = '+ Add to Pantry';
        if (typeof showToast === 'function') showToast('❌ ' + data.message);
      }
    } catch (err) {
      btn.disabled = false;
      btn.textContent = '+ Add to Pantry';
      if (typeof showToast === 'function') showToast('❌ Connection error. Try again.');
    }
  }

  function downloadTxt() {
    const text = document.getElementById('list-data').innerText;
    const blob = new Blob([text], { type: 'text/plain' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = 'shopping_list.txt';
    a.click();
  }

  function copyList() {
    const text = document.getElementById('list-data').innerText;
    navigator.clipboard.writeText(text)
      .then(() => { if (typeof showToast === 'function') showToast('✅ Copied to clipboard!'); });
  }

  // Public bindings for inline handlers
  window.handleCheck = function(checkbox) { handleCheck(checkbox); };

  // Attach click handlers for Add buttons using data-attributes
  function attachHandlers() {
    document.querySelectorAll('.add-to-pantry-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const itemName = btn.dataset.itemName;
        const qtyId = btn.dataset.qtyId;
        const unitId = btn.dataset.unitId;
        const btnId = btn.dataset.btnId;
        const row = btn.closest('.shop-item');
        addToPantry(itemName, qtyId, unitId, btnId, row);
      });
    });

    // Checkbox handlers
    document.querySelectorAll('.shop-checkbox').forEach(cb => {
      cb.addEventListener('change', (e) => {
        handleCheck(cb);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    // initialize checkedCount from already-bought items
    checkedCount = document.querySelectorAll('.shop-item.bought').length;
    attachHandlers();
    updateProgress();

    // expose some functions for debugging
    window.downloadShoppingTxt = downloadTxt;
    window.copyShoppingList = copyList;
  });
})();
