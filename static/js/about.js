// Mobile menu toggle
const menuBtn = document.getElementById('menuBtn');
const mobileMenu = document.getElementById('mobileMenu');

menuBtn.onclick = () => {
    mobileMenu.classList.toggle("hidden");
};

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    if (!menuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
        mobileMenu.classList.add("hidden");
    }
});

// Animated counter for stats
function animateCounter() {
    const counters = document.querySelectorAll('.animated-number');
    const speed = 200; // The lower the slower

    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute('data-target');
            const count = +counter.innerText;

            // Lower inc to slow and higher to slow
            const inc = target / speed;

            // Check if target is reached
            if (count < target) {
                // Add inc to count and output in counter
                counter.innerText = Math.ceil(count + inc);
                // Call function every ms
                setTimeout(updateCount, 1);
            } else {
                counter.innerText = target;
            }
        };

        updateCount();
    });
}

// Intersection Observer for counter animation
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounter();
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

// Observe the stats section
const statsSection = document.querySelector('.bg-miu-light');
if (statsSection) {
    observer.observe(statsSection);
}

// Accordion functionality
const accordionHeaders = document.querySelectorAll('.accordion-header');

accordionHeaders.forEach(header => {
    header.addEventListener('click', () => {
        const accordionId = header.getAttribute('data-accordion');
        const content = document.getElementById(accordionId);

        // Toggle active class on header
        header.classList.toggle('active');

        // Toggle open class on content
        content.classList.toggle('open');

        // Close other accordions
        accordionHeaders.forEach(otherHeader => {
            if (otherHeader !== header) {
                otherHeader.classList.remove('active');
                const otherContentId = otherHeader.getAttribute('data-accordion');
                const otherContent = document.getElementById(otherContentId);
                otherContent.classList.remove('open');
            }
        });
    });
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        if (targetId === '#') return;

        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });

            // Close mobile menu after clicking a link
            mobileMenu.classList.add('hidden');
        }
    });
});

// Form submission
const contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.onsubmit = (e) => {
        e.preventDefault();
        alert("Thank you for your message! We'll contact you soon.");
        contactForm.reset();
    };
}

// Initialize first accordion as open
if (accordionHeaders.length > 0) {
    accordionHeaders[0].classList.add('active');
    const firstContentId = accordionHeaders[0].getAttribute('data-accordion');
    const firstContent = document.getElementById(firstContentId);
    firstContent.classList.add('open');
}