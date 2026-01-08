// Global variables
let currentStep = 1;
const totalSteps = 5;
let academicEntryCount = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    const applicationForm = document.getElementById('applicationForm');
    if (applicationForm) {
        initializeForm();
    } else {
        console.error("Could not find element with ID 'applicationForm'. Check your form.html.");
    }
});

function initializeForm() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const addAcademicEntryBtn = document.getElementById('addAcademicEntryBtn');
    const progressSteps = document.querySelectorAll('.progress-step');

    // Navigation
    if (prevBtn) prevBtn.addEventListener('click', goToPrevStep);
    if (nextBtn) nextBtn.addEventListener('click', goToNextStep);
    
    // Academic entries
    if (addAcademicEntryBtn) {
        addAcademicEntryBtn.addEventListener('click', addAcademicEntry);
        // Only add first entry if the container is empty
        const container = document.getElementById('academicEntriesContainer');
        if (container && container.children.length === 0) {
            addAcademicEntry();
        }
    }

    // Progress step clicks
    if (progressSteps.length > 0) {
        progressSteps.forEach(step => {
            step.addEventListener('click', function () {
                const stepNum = parseInt(this.getAttribute('data-step'));
                if (stepNum <= currentStep) {
                    currentStep = stepNum;
                    updateStep();
                }
            });
        });
    }

    updateStep();
}

function goToPrevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateStep();
    }
}

function goToNextStep() {
    if (validateCurrentStep()) {
        if (currentStep < totalSteps) {
            currentStep++;
            updateStep();
        }
    }
}

function validateCurrentStep() {
    const activeStep = document.getElementById(`step${currentStep}`);
    if (!activeStep) return false;

    const requiredInputs = activeStep.querySelectorAll('[required]');
    let isValid = true;

    requiredInputs.forEach(input => {
        // Remove previous error styling
        input.classList.remove('border-red-500');
        const parent = input.parentNode;
        const existingError = parent.querySelector('.error-message');
        if (existingError) existingError.remove();

        // Validate based on input type
        let isFieldEmpty = false;
        if (input.type === 'checkbox') {
            isFieldEmpty = !input.checked;
        } else if (input.type === 'radio') {
            isFieldEmpty = !activeStep.querySelector(`[name="${input.name}"]:checked`);
        } else {
            isFieldEmpty = !input.value.trim();
        }

        if (isFieldEmpty) {
            isValid = false;
            input.classList.add('border-red-500');
            const errorDiv = document.createElement('p');
            errorDiv.className = 'error-message text-red-500 text-sm mt-1';
            errorDiv.textContent = 'This field is required';
            parent.appendChild(errorDiv);
        }
    });

    // Step 4 specific validation
    if (currentStep === 4) {
        const transcripts = document.querySelector('[name="transcripts_file"]');
        const statement = document.querySelector('[name="personal_statement_file"]');
        
        if ((transcripts && transcripts.files.length === 0) || (statement && statement.files.length === 0)) {
            alert('Please upload at least your academic transcripts and personal statement.');
            isValid = false;
        }
    }

    return isValid;
}

function updateStep() {
    const stepTitles = {
        1: "Personal Information",
        2: "Academic History",
        3: "Course Selection",
        4: "Documents",
        5: "Review & Submit"
    };

    // Update Titles
    const title = document.getElementById('stepTitle');
    const mobileTitle = document.getElementById('mobileStepTitle');
    if (title) title.textContent = stepTitles[currentStep];
    if (mobileTitle) mobileTitle.textContent = stepTitles[currentStep];

    // Update Step Visibility
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.toggle('active', step.id === `step${currentStep}`);
    });

    // Update Progress Indicators
    document.querySelectorAll('.progress-step').forEach(step => {
        const stepNum = parseInt(step.getAttribute('data-step'));
        step.classList.remove('active', 'completed');
        if (stepNum < currentStep) step.classList.add('completed');
        else if (stepNum === currentStep) step.classList.add('active');
    });

    // Button Visibility
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    if (prevBtn) prevBtn.classList.toggle('hidden', currentStep === 1);
    if (nextBtn) nextBtn.classList.toggle('hidden', currentStep === totalSteps);
    if (submitBtn) submitBtn.classList.toggle('hidden', currentStep !== totalSteps);

    // Review logic
    if (currentStep === 5) {
        updateReviewSection();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function addAcademicEntry() {
    academicEntryCount++;
    const container = document.getElementById('academicEntriesContainer');
    if (!container) return;

    const entryId = `academicEntry${academicEntryCount}`;
    const entryHTML = `
        <div class="academic-entry p-4 border rounded-lg mb-4 relative bg-gray-50" id="${entryId}">
            <button type="button" class="absolute top-2 right-2 text-red-500 font-bold" onclick="removeAcademicEntry('${entryId}')">×</button>
            <h4 class="font-bold text-md mb-4 text-miu-primary">Academic Entry #${academicEntryCount}</h4>
            
            <div class="grid gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Level of Education *</label>
                    <select name="educationLevel[]" required class="w-full p-2 border rounded">
                        <option value="">Select Level</option>
                        <option value="high-school">High School</option>
                        <option value="bachelor">Bachelor's</option>
                        <option value="master">Master's</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Institution *</label>
                    <input type="text" name="institution[]" required class="w-full p-2 border rounded">
                </div>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', entryHTML);
}

window.removeAcademicEntry = function (entryId) {
    const entry = document.getElementById(entryId);
    if (entry) {
        entry.remove();
        academicEntryCount--;
        if (academicEntryCount <= 0) {
            academicEntryCount = 0;
            addAcademicEntry();
        }
    }
};

function updateReviewSection() {
    const form = document.getElementById('applicationForm');
    const reviewSummary = document.getElementById('reviewSummary');
    if (!form || !reviewSummary) return;

    const getValue = (name) => {
        const el = form.querySelector(`[name="${name}"]`);
        if (!el) return 'N/A';
        if (el.type === 'radio') {
            const checked = form.querySelector(`[name="${name}"]:checked`);
            return checked ? checked.value : 'Not selected';
        }
        return el.value || 'N/A';
    };

    let summaryHTML = `
        <div class="grid md:grid-cols-2 gap-6">
            <div class="space-y-1">
                <h4 class="font-bold text-miu-primary border-b pb-1">Personal Details</h4>
                <p><strong>Name:</strong> ${getValue('first_name')} ${getValue('last_name')}</p>
                <p><strong>Email:</strong> ${getValue('email')}</p>
                <p><strong>Phone:</strong> ${getValue('phone')}</p>
            </div>
            <div class="space-y-1">
                <h4 class="font-bold text-miu-primary border-b pb-1">Program Details</h4>
                <p><strong>Program:</strong> ${getValue('program')}</p>
                <p><strong>Degree:</strong> ${getValue('degree_level')}</p>
                <p><strong>Intake:</strong> ${getValue('intake')}</p>
            </div>
        </div>
    `;
    reviewSummary.innerHTML = summaryHTML;
}