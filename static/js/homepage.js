/* Homepage Hero Search Tabs & Interactive Handlers */

document.addEventListener('DOMContentLoaded', function () {
    const tabButtons = document.querySelectorAll('.search-tab-btn');
    const purposeInput = document.getElementById('search-purpose-input');

    if (tabButtons.length > 0 && purposeInput) {
        tabButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                // Remove active state from all tab buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));

                // Set active state on clicked button
                this.classList.add('active');

                // Update hidden listing_purpose form input
                const selectedPurpose = this.getAttribute('data-purpose');
                if (selectedPurpose !== null) {
                    purposeInput.value = selectedPurpose;
                }
            });
        });
    }
});
