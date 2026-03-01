// Tab functionality
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons
        tabButtons.forEach(btn => {
            btn.classList.remove('active', 'border-miu-primary', 'text-miu-primary');
            btn.classList.add('border-transparent');
        });

        // Add active class to clicked button
        button.classList.add('active', 'border-miu-primary', 'text-miu-primary');
        button.classList.remove('border-transparent');

        // Hide all tab contents
        tabContents.forEach(content => {
            content.classList.add('hidden');
        });

        // Show selected tab content
        const tabId = button.getAttribute('data-tab') + 'Tab';
        document.getElementById(tabId).classList.remove('hidden');
    });
});

// Syllabus accordion functionality
const syllabusHeaders = document.querySelectorAll('.syllabus-accordion-header');

syllabusHeaders.forEach(header => {
    header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        const icon = header.querySelector('span:last-child');

        if (content.style.maxHeight && content.style.maxHeight !== '0px') {
            content.style.maxHeight = '0';
            icon.textContent = '+';
        } else {
            // Close other open accordions
            document.querySelectorAll('.syllabus-accordion-content').forEach(item => {
                item.style.maxHeight = '0';
            });
            document.querySelectorAll('.syllabus-accordion-header span:last-child').forEach(item => {
                item.textContent = '+';
            });

            // Open this accordion
            content.style.maxHeight = content.scrollHeight + 'px';
            icon.textContent = '−';
        }
    });
});

// FAQ accordion functionality
const faqQuestions = document.querySelectorAll('.faq-question');

faqQuestions.forEach(question => {
    question.addEventListener('click', () => {
        const answer = question.nextElementSibling;
        const icon = question.querySelector('span:last-child');

        if (answer.style.maxHeight && answer.style.maxHeight !== '0px') {
            answer.style.maxHeight = '0';
            icon.textContent = '+';
        } else {
            // Close other open FAQs
            document.querySelectorAll('.faq-answer').forEach(item => {
                item.style.maxHeight = '0';
            });
            document.querySelectorAll('.faq-question span:last-child').forEach(item => {
                item.textContent = '+';
            });

            // Open this FAQ
            answer.style.maxHeight = answer.scrollHeight + 'px';
            icon.textContent = '−';
        }
    });
});

// Enroll button functionality
document.getElementById('enrollBtn').addEventListener('click', () => {
    alert('Redirecting to enrollment page...');
    // In a real implementation, this would redirect to enrollment/checkout
    // window.location.href = 'enrollment.html';
});

// Mobile menu toggle (simplified version)
document.getElementById('menuBtn').addEventListener('click', () => {
    alert('Mobile menu would open here. This is a simplified version.');
});

// Initialize first accordion as open
window.addEventListener('load', () => {
    // Open first FAQ by default
    const firstFaq = document.querySelector('.faq-answer');
    if (firstFaq) {
        firstFaq.style.maxHeight = firstFaq.scrollHeight + 'px';
        document.querySelector('.faq-question span:last-child').textContent = '−';
    }
});