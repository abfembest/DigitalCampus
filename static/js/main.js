// ─── Lucide Icons — safe init ───────────────────────────────────────────────
// unpkg CDN loads asynchronously. If it hasn't finished by DOMContentLoaded,
// createIcons() would fail silently and NO icons appear on the page.
// We try on DOMContentLoaded first, then fall back to window.load.
function initLucide() {
    if (window.lucide) {
        lucide.createIcons();
    }
}

document.addEventListener('DOMContentLoaded', initLucide);
window.addEventListener('load', initLucide); // catches CDN late-load

// ─── SweetAlert2 Toast ──────────────────────────────────────────────────────
const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 6000,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer);
        toast.addEventListener('mouseleave', Swal.resumeTimer);
    },
    customClass: {
        popup: 'rounded-xl shadow-2xl border-l-4',
        title: 'text-sm font-semibold',
        timerProgressBar: 'bg-gradient-to-r from-primary-950 to-purple-700'
    },
    iconColor: '#840384',
    background: '#ffffff'
});

window.showToast = function (type, message) {
    Toast.fire({ icon: type, title: message });
};

// ─── Mobile Menu Toggle ─────────────────────────────────────────────────────
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu    = document.getElementById('mobileMenu');
const menuIcon      = document.getElementById('menuIcon');

if (mobileMenuBtn && mobileMenu && menuIcon) {
    mobileMenuBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        const isHidden = mobileMenu.classList.contains('hidden');

        if (isHidden) {
            mobileMenu.classList.remove('hidden');
            mobileMenuBtn.setAttribute('aria-expanded', 'true');
            menuIcon.outerHTML = '<i data-lucide="x" class="w-6 h-6 text-primary-950" id="menuIcon"></i>';
        } else {
            mobileMenu.classList.add('hidden');
            mobileMenuBtn.setAttribute('aria-expanded', 'false');
            menuIcon.outerHTML = '<i data-lucide="menu" class="w-6 h-6 text-primary-950" id="menuIcon"></i>';
        }
        initLucide();
    });

    document.addEventListener('click', function (e) {
        if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
            if (!mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
                mobileMenuBtn.setAttribute('aria-expanded', 'false');
                const currentIcon = document.getElementById('menuIcon');
                if (currentIcon) {
                    currentIcon.outerHTML = '<i data-lucide="menu" class="w-6 h-6 text-primary-950" id="menuIcon"></i>';
                    initLucide();
                }
            }
        }
    });
}

// ─── Mobile Dropdown Handlers ───────────────────────────────────────────────
function setupMobileDropdown(btnId, menuId, chevronId) {
    const btn     = document.getElementById(btnId);
    const menu    = document.getElementById(menuId);
    const chevron = document.getElementById(chevronId);

    if (btn && menu && chevron) {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = !menu.classList.contains('hidden');

            if (isOpen) {
                menu.classList.add('hidden');
                chevron.classList.remove('rotate-180');
                btn.setAttribute('aria-expanded', 'false');
            } else {
                menu.classList.remove('hidden');
                chevron.classList.add('rotate-180');
                btn.setAttribute('aria-expanded', 'true');
                initLucide(); // re-run after revealing hidden icons
            }
        });
    }
}

setupMobileDropdown('mobileFacultiesBtn', 'mobileFacultiesMenu', 'facultiesChevron');
setupMobileDropdown('mobileProgramsBtn',  'mobileProgramsMenu',  'programsChevron');
setupMobileDropdown('mobileMoreBtn',      'mobileMoreMenu',      'moreChevron');

// ─── Desktop Dropdown Handlers ──────────────────────────────────────────────
document.querySelectorAll('.relative.group').forEach(dropdown => {
    const button = dropdown.querySelector('button[aria-haspopup="true"]');
    const menu   = dropdown.querySelector('[role="menu"]');

    if (button && menu) {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const isVisible = menu.classList.contains('opacity-100') && menu.classList.contains('visible');

            // Close all other open menus first
            document.querySelectorAll('[role="menu"]').forEach(m => {
                if (m !== menu) {
                    m.classList.remove('opacity-100', 'visible');
                    m.classList.add('opacity-0', 'invisible');
                }
            });
            document.querySelectorAll('.relative.group button[aria-haspopup="true"]').forEach(btn => {
                if (btn !== button) btn.setAttribute('aria-expanded', 'false');
            });

            if (isVisible) {
                menu.classList.remove('opacity-100', 'visible');
                menu.classList.add('opacity-0', 'invisible');
                button.setAttribute('aria-expanded', 'false');
            } else {
                menu.classList.remove('opacity-0', 'invisible');
                menu.classList.add('opacity-100', 'visible');
                button.setAttribute('aria-expanded', 'true');
                initLucide(); // re-run after revealing dropdown icons
            }
        });

        if (window.matchMedia('(min-width: 1024px)').matches) {
            dropdown.addEventListener('mouseenter', function () {
                menu.classList.remove('opacity-0', 'invisible');
                menu.classList.add('opacity-100', 'visible');
                button.setAttribute('aria-expanded', 'true');
                initLucide(); // re-run on hover reveal
            });

            dropdown.addEventListener('mouseleave', function () {
                menu.classList.remove('opacity-100', 'visible');
                menu.classList.add('opacity-0', 'invisible');
                button.setAttribute('aria-expanded', 'false');
            });
        }
    }
});

// Close all dropdowns on outside click
document.addEventListener('click', function (e) {
    if (!e.target.closest('.relative.group')) {
        document.querySelectorAll('[role="menu"]').forEach(menu => {
            menu.classList.remove('opacity-100', 'visible');
            menu.classList.add('opacity-0', 'invisible');
        });
        document.querySelectorAll('.relative.group button[aria-haspopup="true"]').forEach(btn => {
            btn.setAttribute('aria-expanded', 'false');
        });
    }
});

// Close all dropdowns on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('[role="menu"]').forEach(menu => {
            menu.classList.remove('opacity-100', 'visible');
            menu.classList.add('opacity-0', 'invisible');
        });
        document.querySelectorAll('.relative.group button[aria-haspopup="true"]').forEach(btn => {
            btn.setAttribute('aria-expanded', 'false');
        });
    }
});

// ─── Smooth Scroll ──────────────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href.length > 1) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                    mobileMenuBtn.setAttribute('aria-expanded', 'false');
                    const currentIcon = document.getElementById('menuIcon');
                    if (currentIcon) {
                        currentIcon.outerHTML = '<i data-lucide="menu" class="w-6 h-6 text-primary-950" id="menuIcon"></i>';
                        initLucide();
                    }
                }
            }
        }
    });
});

// ─── Header Scroll Shadow ───────────────────────────────────────────────────
const header = document.querySelector('header');
if (header) {
    window.addEventListener('scroll', function () {
        if (window.pageYOffset > 50) {
            header.classList.add('shadow-xl');
        } else {
            header.classList.remove('shadow-xl');
        }
    });
}