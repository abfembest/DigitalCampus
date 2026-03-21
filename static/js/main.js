// ─── Lucide Icons — safe init ───────────────────────────────────────────────
function initLucide() {
    if (window.lucide) {
        lucide.createIcons();
    }
}

document.addEventListener('DOMContentLoaded', initLucide);
window.addEventListener('load', initLucide);

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

function closeMobileMenu() {
    if (!mobileMenu || !mobileMenuBtn) return;
    mobileMenu.style.maxHeight = '0px';
    mobileMenu.style.overflowY = 'hidden';
    mobileMenu.setAttribute('aria-hidden', 'true');
    mobileMenuBtn.setAttribute('aria-expanded', 'false');
    const icon = document.getElementById('menuIcon');
    if (icon) {
        icon.setAttribute('data-lucide', 'menu');
        initLucide();
    }
}

if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        const isOpen = mobileMenu.style.maxHeight && mobileMenu.style.maxHeight !== '0px';
        if (isOpen) {
            closeMobileMenu();
        } else {
            const inner = mobileMenu.querySelector('.py-3');
            const fullHeight = inner ? inner.scrollHeight + 32 : mobileMenu.scrollHeight;
            const maxAllowed = Math.floor(window.innerHeight * 0.82);
            mobileMenu.style.maxHeight = Math.min(fullHeight, maxAllowed) + 'px';
            mobileMenu.style.overflowY = 'auto';
            mobileMenu.setAttribute('aria-hidden', 'false');
            mobileMenuBtn.setAttribute('aria-expanded', 'true');
            const icon = document.getElementById('menuIcon');
            if (icon) {
                icon.setAttribute('data-lucide', 'x');
                initLucide();
            }
        }
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
        if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
            closeMobileMenu();
        }
    });
}

// ─── Mobile Accordion Handlers ──────────────────────────────────────────────
function setupMobileDropdown(btnId, menuId, chevronId) {
    const btn     = document.getElementById(btnId);
    const menu    = document.getElementById(menuId);
    const chevron = document.getElementById(chevronId);
    if (!btn || !menu) return;

    btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const isOpen = menu.style.maxHeight && menu.style.maxHeight !== '0px';

        // Toggle this accordion
        menu.style.maxHeight = isOpen ? '0px' : menu.scrollHeight + 'px';
        btn.setAttribute('aria-expanded', String(!isOpen));
        if (chevron) chevron.style.transform = isOpen ? '' : 'rotate(180deg)';
        if (!isOpen) initLucide();

        // After transition, let outer menu scroll freely to fit all content
        // instead of capping — so nothing gets clipped
        setTimeout(() => {
            if (mobileMenu && mobileMenu.style.overflowY === 'auto') {
                // Set to the actual full inner content height, not a viewport cap
                const inner = mobileMenu.querySelector('.py-3');
                if (inner) {
                    const fullHeight = inner.scrollHeight + 32; // 32px padding buffer
                    const maxAllowed = Math.floor(window.innerHeight * 0.82);
                    // Use whichever is smaller: content or 82vh
                    mobileMenu.style.maxHeight = Math.min(fullHeight, maxAllowed) + 'px';
                }
            }
        }, 320);
    });
}

setupMobileDropdown('mobileFacultiesBtn', 'mobileFacultiesMenu', 'facultiesChevron');
setupMobileDropdown('mobileProgramsBtn',  'mobileProgramsMenu',  'programsChevron');

// ─── Desktop Dropdown Handlers ──────────────────────────────────────────────
document.querySelectorAll('.relative.group').forEach(dropdown => {
    const button = dropdown.querySelector('button[aria-haspopup="menu"]');
    const menu   = dropdown.querySelector('[role="menu"]');

    if (button && menu) {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            const isVisible = menu.classList.contains('opacity-100') && menu.classList.contains('visible');

            document.querySelectorAll('[role="menu"]').forEach(m => {
                if (m !== menu) {
                    m.classList.remove('opacity-100', 'visible');
                    m.classList.add('opacity-0', 'invisible');
                }
            });
            document.querySelectorAll('.relative.group button[aria-haspopup="menu"]').forEach(btn => {
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
                initLucide();
            }
        });

        if (window.matchMedia('(min-width: 1024px)').matches) {
            dropdown.addEventListener('mouseenter', function () {
                menu.classList.remove('opacity-0', 'invisible');
                menu.classList.add('opacity-100', 'visible');
                button.setAttribute('aria-expanded', 'true');
                initLucide();
            });
            dropdown.addEventListener('mouseleave', function () {
                menu.classList.remove('opacity-100', 'visible');
                menu.classList.add('opacity-0', 'invisible');
                button.setAttribute('aria-expanded', 'false');
            });
        }
    }
});

// Close dropdowns on outside click
document.addEventListener('click', function (e) {
    if (!e.target.closest('.relative.group')) {
        document.querySelectorAll('[role="menu"]').forEach(m => {
            m.classList.remove('opacity-100', 'visible');
            m.classList.add('opacity-0', 'invisible');
        });
        document.querySelectorAll('.relative.group button[aria-haspopup="menu"]').forEach(btn => {
            btn.setAttribute('aria-expanded', 'false');
        });
    }
});

// Close dropdowns on Escape
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('[role="menu"]').forEach(m => {
            m.classList.remove('opacity-100', 'visible');
            m.classList.add('opacity-0', 'invisible');
        });
        document.querySelectorAll('.relative.group button[aria-haspopup="menu"]').forEach(btn => {
            btn.setAttribute('aria-expanded', 'false');
        });
        closeMobileMenu();
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
                closeMobileMenu();
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