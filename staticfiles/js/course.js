// Tab functionality for application form
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const submitBtn = document.getElementById('submitBtn');

let currentTab = 0;
const tabs = ['personal', 'academic', 'documents', 'review'];

function showTab(index) {
    // Update tab buttons
    tabButtons.forEach((btn, i) => {
        if (i === index) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update tab contents
    tabContents.forEach((content, i) => {
        if (i === index) {
            content.classList.remove('hidden');
        } else {
            content.classList.add('hidden');
        }
    });

    // Update navigation buttons
    prevBtn.classList.toggle('hidden', index === 0);
    nextBtn.classList.toggle('hidden', index === tabs.length - 1);
    submitBtn.classList.toggle('hidden', index !== tabs.length - 1);

    currentTab = index;
}

// Initialize first tab
showTab(0);

// Tab button click events
tabButtons.forEach((button, index) => {
    button.addEventListener('click', () => {
        showTab(index);
    });
});

// Navigation buttons
nextBtn.addEventListener('click', () => {
    if (currentTab < tabs.length - 1) {
        showTab(currentTab + 1);
    }
});

prevBtn.addEventListener('click', () => {
    if (currentTab > 0) {
        showTab(currentTab - 1);
    }
});

// Submit button
submitBtn.addEventListener('click', (e) => {
    e.preventDefault();
    if (confirm('Are you ready to submit your application? You cannot make changes after submission.')) {
        // In a real implementation, this would submit the form data
        alert('Application submitted successfully! You will receive a confirmation email shortly.');
        // Reset form and go to first tab
        showTab(0);
        document.querySelectorAll('input, select, textarea').forEach(input => {
            if (input.type !== 'submit' && input.type !== 'button') {
                input.value = '';
            }
        });
    }
});

// Document upload functionality
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadedFiles = document.getElementById('uploadedFiles');

uploadArea.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        uploadedFiles.classList.remove('hidden');
        const filesList = uploadedFiles.querySelector('.space-y-2');
        filesList.innerHTML = '';

        files.forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between bg-gray-50 p-3 rounded';
            fileElement.innerHTML = `
          <div class="flex items-center">
            <span class="text-lg mr-3">📄</span>
            <div>
              <div class="font-medium">${file.name}</div>
              <div class="text-sm text-gray-500">${(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
          </div>
          <button class="text-red-500 hover:text-red-700 remove-file">×</button>
        `;
            filesList.appendChild(fileElement);
        });

        // Add remove file functionality
        document.querySelectorAll('.remove-file').forEach(button => {
            button.addEventListener('click', function () {
                this.parentElement.remove();
                if (filesList.children.length === 0) {
                    uploadedFiles.classList.add('hidden');
                }
            });
        });
    }
});

// Drag and drop functionality
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    uploadArea.addEventListener(eventName, () => {
        uploadArea.classList.add('dragover');
    });
});

['dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, () => {
        uploadArea.classList.remove('dragover');
    });
});

uploadArea.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    fileInput.files = files;
    fileInput.dispatchEvent(new Event('change'));
});

// Checklist functionality
const checklistItems = document.querySelectorAll('.application-checklist input');
checklistItems.forEach(item => {
    item.addEventListener('change', function () {
        const checkmark = this.nextElementSibling.querySelector('.checkmark');
        const text = this.nextElementSibling.nextElementSibling;

        if (this.checked) {
            checkmark.classList.remove('hidden');
            text.classList.add('line-through', 'text-gray-400');
        } else {
            checkmark.classList.add('hidden');
            text.classList.remove('line-through', 'text-gray-400');
        }
    });

    // Trigger change event on label click
    const label = item.parentElement;
    label.addEventListener('click', () => {
        item.checked = !item.checked;
        item.dispatchEvent(new Event('change'));
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

// Mobile menu functionality (simplified)
document.getElementById('menuBtn').addEventListener('click', () => {
    alert('Mobile menu would open here. In the full implementation, this would toggle the mobile menu.');
});

// Open first FAQ by default
window.addEventListener('load', () => {
    const firstFaq = document.querySelector('.faq-answer');
    if (firstFaq) {
        firstFaq.style.maxHeight = firstFaq.scrollHeight + 'px';
        document.querySelector('.faq-question span:last-child').textContent = '−';
    }
});