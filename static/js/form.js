// ================= FIXED APPLICATION FORM JAVASCRIPT =================
document.addEventListener('DOMContentLoaded', function() {
    // Global State
    let currentStep = 1;
    const totalSteps = 5;
    
    // Step titles
    const stepTitles = {
        1: "Personal Information",
        2: "Academic History",
        3: "Course Selection",
        4: "Documents",
        5: "Review & Submit"
    };
    
    // DOM Elements
    const form = document.getElementById('applicationForm');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressSteps = document.querySelectorAll('.progress-step');
    const formSteps = document.querySelectorAll('.form-step');
    
    // Progress indicators
    const progressBar = document.getElementById('progressBar');
    const mobileProgressBar = document.getElementById('mobileProgressBar');
    const stepProgressBar = document.getElementById('stepProgressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const mobileProgressPercentage = document.getElementById('mobileProgressPercentage');
    const currentStepElement = document.getElementById('mobileCurrentStep');
    const stepTitleElement = document.getElementById('stepTitle');
    const mobileStepTitleElement = document.getElementById('mobileStepTitle');
    
    // ================= ACADEMIC ENTRIES =================
    let academicEntryCount = 0;

    function addAcademicEntry() {
        academicEntryCount++;
        const container = document.getElementById('academicEntriesContainer');
        if (!container) return;
        
        const entryHTML = `
            <div class="academic-entry border-2 border-gray-300 rounded-lg p-6 relative" data-entry="${academicEntryCount}">
                ${academicEntryCount > 1 ? `
                <button type="button" class="remove-entry absolute top-4 right-4 text-red-600 hover:text-red-800" onclick="window.removeAcademicEntry(${academicEntryCount})">
                    <i data-lucide="x-circle" class="w-6 h-6"></i>
                </button>
                ` : ''}
                
                <h4 class="font-semibold mb-4 text-gray-800">Academic Entry ${academicEntryCount}</h4>
                
                <div class="grid md:grid-cols-2 gap-6 mb-6">
                    <div>
                        <label class="block text-gray-700 font-medium mb-2">
                            Education Level <span class="text-red-500">*</span>
                        </label>
                        <select name="education_level_${academicEntryCount}" required class="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white">
                            <option value="">Select Level</option>
                            <option value="high-school">High School</option>
                            <option value="bachelor">Bachelor's Degree</option>
                            <option value="master">Master's Degree</option>
                            <option value="phd">PhD/Doctorate</option>
                        </select>
                        <div class="error-message text-red-500 text-sm mt-1"></div>
                    </div>
                    
                    <div>
                        <label class="block text-gray-700 font-medium mb-2">
                            Graduation Year <span class="text-red-500">*</span>
                        </label>
                        <input type="number" name="graduation_year_${academicEntryCount}" required min="1950" max="2030" placeholder="2023" class="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all">
                        <div class="error-message text-red-500 text-sm mt-1"></div>
                    </div>
                </div>
                
                <div class="mb-6">
                    <label class="block text-gray-700 font-medium mb-2">
                        Institution Name <span class="text-red-500">*</span>
                    </label>
                    <input type="text" name="institution_${academicEntryCount}" required placeholder="University/College Name" class="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all">
                    <div class="error-message text-red-500 text-sm mt-1"></div>
                </div>
                
                <div class="grid md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-gray-700 font-medium mb-2">
                            Field of Study <span class="text-red-500">*</span>
                        </label>
                        <input type="text" name="field_of_study_${academicEntryCount}" required placeholder="Major/Field of Study" class="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all">
                        <div class="error-message text-red-500 text-sm mt-1"></div>
                    </div>
                    
                    <div>
                        <label class="block text-gray-700 font-medium mb-2">
                            GPA (Optional)
                        </label>
                        <input type="text" name="gpa_${academicEntryCount}" placeholder="3.5/4.0" class="w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all">
                    </div>
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', entryHTML);
        lucide.createIcons();
    }

    // Make removeAcademicEntry global
    window.removeAcademicEntry = function(entryId) {
        const entry = document.querySelector(`.academic-entry[data-entry="${entryId}"]`);
        if (entry && academicEntryCount > 1) {
            entry.remove();
        }
    };

    // Add event listener for adding academic entries
    const addAcademicBtn = document.getElementById('addAcademicEntryBtn');
    if (addAcademicBtn) {
        addAcademicBtn.addEventListener('click', addAcademicEntry);
    }
    
    // ================= NAVIGATION =================
    function goToNextStep() {
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                currentStep++;
                updateStep();
            }
        }
    }
    
    function goToPrevStep() {
        if (currentStep > 1) {
            currentStep--;
            updateStep();
        }
    }
    
    // ================= STEP UPDATE =================
    function updateStep() {
        // Update step titles
        const title = stepTitles[currentStep];
        if (stepTitleElement) stepTitleElement.textContent = title;
        if (mobileStepTitleElement) mobileStepTitleElement.textContent = title;
        
        // Update current step number
        if (currentStepElement) currentStepElement.textContent = currentStep;
        
        // Update progress steps in sidebar
        progressSteps.forEach(step => {
            const stepNum = parseInt(step.getAttribute('data-step'));
            step.classList.remove('active', 'completed');
            
            if (stepNum < currentStep) {
                step.classList.add('completed');
            } else if (stepNum === currentStep) {
                step.classList.add('active');
            }
        });
        
        // Update form step visibility - SHOW ONLY CURRENT STEP
        formSteps.forEach((step, index) => {
            if (index + 1 === currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
        
        // Update navigation buttons
        if (prevBtn) prevBtn.classList.toggle('hidden', currentStep === 1);
        if (nextBtn) nextBtn.classList.toggle('hidden', currentStep === totalSteps);
        if (submitBtn) submitBtn.classList.toggle('hidden', currentStep !== totalSteps);
        
        // Calculate progress percentage
        const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
        
        // Update all progress bars
        if (progressBar) progressBar.style.width = `${progressPercent}%`;
        if (mobileProgressBar) mobileProgressBar.style.width = `${progressPercent}%`;
        if (stepProgressBar) stepProgressBar.style.width = `${progressPercent}%`;
        
        // Update percentage text
        const percentText = Math.round(progressPercent);
        if (progressPercentage) progressPercentage.textContent = percentText;
        if (mobileProgressPercentage) mobileProgressPercentage.textContent = percentText;
        
        // Update review section if on step 5
        if (currentStep === 5) {
            updateReviewSection();
        }
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // ================= VALIDATION =================
    function validateStep(step) {
        const activeStep = document.getElementById(`step${step}`);
        if (!activeStep) return false;
        
        let isValid = true;
        let errorMessages = [];
        
        // Clear previous errors
        activeStep.querySelectorAll('.error-message').forEach(el => el.textContent = '');
        activeStep.querySelectorAll('.border-red-500').forEach(el => {
            el.classList.remove('border-red-500');
        });
        
        // Remove any existing validation error box
        const existingError = activeStep.querySelector('.validation-errors');
        if (existingError) {
            existingError.remove();
        }
        
        // Get all required inputs in current step
        const inputs = activeStep.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            // Skip inputs inside hidden academic entries
            if (input.closest('.academic-entry') && !input.closest('.academic-entry').offsetParent) {
                return;
            }
            
            // Get field label
            const labelElement = input.closest('div').querySelector('label');
            const label = labelElement ? labelElement.textContent.replace('*', '').trim() : input.name;
            
            // Check if field has value
            if (input.type === 'checkbox' || input.type === 'radio') {
                const name = input.name;
                const checked = activeStep.querySelector(`input[name="${name}"]:checked`);
                if (!checked) {
                    isValid = false;
                    const firstInput = activeStep.querySelector(`input[name="${name}"]`);
                    if (firstInput) {
                        firstInput.classList.add('border-red-500');
                        const errorDiv = firstInput.closest('.mb-6')?.querySelector('.error-message');
                        const errorMsg = `Please select ${label}`;
                        if (errorDiv) errorDiv.textContent = errorMsg;
                        errorMessages.push(errorMsg);
                    }
                }
            } else if (input.tagName === 'SELECT') {
                // Check for empty or placeholder value in select fields
                if (!input.value || input.value === '' || input.value === '--------') {
                    isValid = false;
                    input.classList.add('border-red-500');
                    const errorDiv = input.parentElement.querySelector('.error-message');
                    const errorMsg = `Please select ${label}`;
                    if (errorDiv) errorDiv.textContent = errorMsg;
                    errorMessages.push(errorMsg);
                }
            } else if (!input.value || !input.value.trim()) {
                isValid = false;
                input.classList.add('border-red-500');
                const errorDiv = input.parentElement.querySelector('.error-message') || 
                            input.closest('div').querySelector('.error-message');
                const errorMsg = `${label} is required`;
                if (errorDiv) errorDiv.textContent = errorMsg;
                errorMessages.push(errorMsg);
            }
        });
        
        // Step-specific validation
        if (step === 2) {
            const englishType = activeStep.querySelector('input[name="english_proficiency_type"]:checked');
            if (!englishType || englishType.value === '') {
                errorMessages.push('Please select your English proficiency type');
                isValid = false;
            }
        }
        
        if (step === 5) {
            const declaration = form.querySelector('input[name="declaration"]');
            const privacy = form.querySelector('input[name="privacy"]');
            
            if (declaration && !declaration.checked) {
                errorMessages.push('Please accept the declaration to continue');
                isValid = false;
            }
            if (privacy && !privacy.checked) {
                errorMessages.push('Please accept the privacy policy to continue');
                isValid = false;
            }
        }
        
        // Show consolidated error message
        if (!isValid && errorMessages.length > 0) {
            const uniqueErrors = [...new Set(errorMessages)];
            
            // Create a detailed error message box
            let errorHTML = '<div class="bg-red-50 border-2 border-red-200 rounded-lg p-4 mb-6 animate-scale-in">';
            errorHTML += '<div class="flex items-start gap-3">';
            errorHTML += '<i data-lucide="alert-circle" class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"></i>';
            errorHTML += '<div class="flex-1">';
            errorHTML += '<h4 class="font-bold text-red-800 mb-2">Please fix the following errors:</h4>';
            errorHTML += '<ul class="list-disc list-inside space-y-1 text-sm text-red-700">';
            
            uniqueErrors.forEach(error => {
                errorHTML += `<li>${error}</li>`;
            });
            
            errorHTML += '</ul></div></div></div>';
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'validation-errors';
            errorDiv.innerHTML = errorHTML;
            activeStep.insertBefore(errorDiv, activeStep.firstChild);
            
            // Re-initialize lucide icons
            lucide.createIcons();
            
            // Scroll to error
            setTimeout(() => {
                errorDiv.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
            }, 100);
        }
        
        return isValid;
    }
    
    // ================= REVIEW SECTION =================
    function updateReviewSection() {
        const reviewSummary = document.getElementById('reviewSummary');
        if (!reviewSummary) return;
        
        const formData = new FormData(form);
        
        const firstName = formData.get('first_name') || '';
        const lastName = formData.get('last_name') || '';
        const email = formData.get('email') || '';
        const phone = formData.get('phone') || '';
        const country = form.querySelector('select[name="country"]')?.selectedOptions[0]?.text || 'Not selected';
        const program = form.querySelector('select[name="program"]')?.selectedOptions[0]?.text || 'Not selected';
        const degreeLevel = formData.get('degree_level') || 'Not selected';
        const studyMode = formData.get('study_mode') || 'Not selected';
        const intake = formData.get('intake') || 'Not selected';
        
        // Collect academic entries
        let academicHTML = '';
        for (let i = 1; i <= academicEntryCount; i++) {
            const level = formData.get(`education_level_${i}`);
            const institution = formData.get(`institution_${i}`);
            if (level && institution) {
                academicHTML += `<p>Entry ${i}: ${level} at ${institution}</p>`;
            }
        }
        
        let summaryHTML = `
            <div class="mb-4">
                <h4 class="font-semibold mb-2 text-purple-900">Personal Information</h4>
                <p class="text-gray-700">Name: ${firstName} ${lastName}</p>
                <p class="text-gray-700">Email: ${email}</p>
                <p class="text-gray-700">Phone: ${phone}</p>
                <p class="text-gray-700">Country: ${country}</p>
            </div>
            
            <div class="mb-4">
                <h4 class="font-semibold mb-2 text-purple-900">Academic History</h4>
                ${academicHTML || '<p class="text-gray-700">Not provided</p>'}
            </div>
            
            <div class="mb-4">
                <h4 class="font-semibold mb-2 text-purple-900">Program Selection</h4>
                <p class="text-gray-700">Program: ${program}</p>
                <p class="text-gray-700">Degree Level: ${degreeLevel}</p>
                <p class="text-gray-700">Study Mode: ${studyMode}</p>
                <p class="text-gray-700">Intake: ${intake}</p>
            </div>
        `;
        
        reviewSummary.innerHTML = summaryHTML;
    }
    
    // ================= FORM SUBMISSION =================
    function submitApplication(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!validateStep(5)) return false;
        
        const formData = new FormData(form);
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span> Submitting...';
        
        // Show loading toast
        window.showToast('info', 'Submitting your application...');
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                window.showToast('success', 'Application submitted successfully!');
                
                // Redirect immediately
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/application_status/';
                }, 500);
                
            } else {
                window.showToast('error', data.error || 'An error occurred. Please try again.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Submit Application</span>';
            }
        })
        .catch(error => {
            console.error('Submission Error:', error);
            window.showToast('error', 'Network error. Please check your connection and try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Submit Application</span>';
        });
        
        return false;
    }
    
    // ================= EVENT LISTENERS =================
    if (prevBtn) prevBtn.addEventListener('click', goToPrevStep);
    if (nextBtn) nextBtn.addEventListener('click', goToNextStep);
    if (submitBtn) submitBtn.addEventListener('click', submitApplication);
    
    // Progress step click handlers
    progressSteps.forEach(step => {
        step.addEventListener('click', function() {
            const stepNum = parseInt(this.getAttribute('data-step'));
            if (stepNum < currentStep || validateStep(currentStep)) {
                currentStep = stepNum;
                updateStep();
            }
        });
    });
    
    // ================= INITIALIZATION =================
    function initForm() {
        // Add initial academic entry
        addAcademicEntry();
        
        // Show only first step
        formSteps.forEach((step, index) => {
            if (index === 0) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
        
        updateStep();
        lucide.createIcons();
    }
    
    // Initialize form
    initForm();
});