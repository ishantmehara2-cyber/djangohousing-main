/* Global Navigation & User Menu JavaScript */

document.addEventListener('DOMContentLoaded', function () {
    // User Profile Dropdown Toggle
    const userMenuBtn = document.getElementById('user-menu-btn');
    const userDropdownPanel = document.getElementById('user-dropdown-panel');

    if (userMenuBtn && userDropdownPanel) {
        userMenuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isExpanded = userMenuBtn.getAttribute('aria-expanded') === 'true';
            userMenuBtn.setAttribute('aria-expanded', !isExpanded);
            userDropdownPanel.classList.toggle('show');
        });

        document.addEventListener('click', function (e) {
            if (!userDropdownPanel.contains(e.target) && !userMenuBtn.contains(e.target)) {
                userDropdownPanel.classList.remove('show');
                userMenuBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Mobile Hamburger Navigation Drawer
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileDrawer = document.getElementById('mobile-menu-drawer');
    const mobileBackdrop = document.getElementById('mobile-menu-backdrop');
    const mobileCloseBtn = document.getElementById('mobile-menu-close');

    function openMobileMenu() {
        if (mobileDrawer) mobileDrawer.classList.add('open');
        if (mobileBackdrop) mobileBackdrop.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileMenu() {
        if (mobileDrawer) mobileDrawer.classList.remove('open');
        if (mobileBackdrop) mobileBackdrop.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (mobileMenuBtn) mobileMenuBtn.addEventListener('click', openMobileMenu);
    if (mobileCloseBtn) mobileCloseBtn.addEventListener('click', closeMobileMenu);
    if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobileMenu);

    // Close on Escape Key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (userDropdownPanel) {
                userDropdownPanel.classList.remove('show');
                if (userMenuBtn) userMenuBtn.setAttribute('aria-expanded', 'false');
            }
            closeMobileMenu();
        }
    });
});
