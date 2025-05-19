function attachAutocomplete(input) {
    const ul = input.parentElement.querySelector('.suggestion-list');
    let debounceTimer;

    // Input event listener
    input.addEventListener('input', function() {
        // ...existing input event code...
    });

    // Click event for suggestions
    ul.addEventListener('click', function(e) {
        const item = e.target.closest('.list-group-item');
        if (!item) return;

        const row = input.closest('tr');
        if (!row) return;

        // Fill in the suggestion data
        input.value = item.textContent;
        
        // Get other form inputs in the row
        const accountSelect = row.querySelector('[data-field="account_id"]');
        const categorySelect = row.querySelector('[data-field="category_id"]');
        const amountInput = row.querySelector('[data-field="amount"]');

        // Set the values
        if (accountSelect) {
            accountSelect.value = item.dataset.account;
            accountSelect.dispatchEvent(new Event('change'));
        }

        if (categorySelect) {
            categorySelect.value = item.dataset.category;
            categorySelect.dispatchEvent(new Event('change'));
        }

        if (amountInput) {
            amountInput.value = item.dataset.amount;
            amountInput.dispatchEvent(new Event('input'));
        }

        // Hide suggestion list
        ul.classList.add('d-none');
        ul.innerHTML = '';

        // Focus on the next input
        const nextInput = row.querySelector('[data-field="amount"]');
        if (nextInput) {
            nextInput.focus();
        }
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !ul.contains(e.target)) {
            ul.classList.add('d-none');
            ul.innerHTML = '';
        }
    });
}