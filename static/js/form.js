// ================= APPLICATION FORM JAVASCRIPT =================
document.addEventListener('DOMContentLoaded', function() {
    // Global State
    let currentStep = 1;
    const totalSteps = 5;
    let academicEntryCount = 0;
    
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
    const addAcademicBtn = document.getElementById('addAcademicEntryBtn');
    const academicContainer = document.getElementById('academicEntriesContainer');
    
    // Progress indicators
    const progressBar = document.getElementById('progressBar');
    const mobileProgressBar = document.getElementById('mobileProgressBar');
    const stepProgressBar = document.getElementById('stepProgressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const mobileProgressPercentage = document.getElementById('mobileProgressPercentage');
    const currentStepElement = document.getElementById('mobileCurrentStep');
    const stepTitleElement = document.getElementById('stepTitle');
    const mobileStepTitleElement = document.getElementById('mobileStepTitle');
    
    // Debug: Log all element selections
    console.log('DOM Elements Check:', {
        form: !!form,
        prevBtn: !!prevBtn,
        nextBtn: !!nextBtn,
        submitBtn: !!submitBtn,
        progressSteps: progressSteps.length,
        formSteps: formSteps.length,
        progressBar: !!progressBar,
        mobileProgressBar: !!mobileProgressBar,
        stepProgressBar: !!stepProgressBar,
        progressPercentage: !!progressPercentage,
        mobileProgressPercentage: !!mobileProgressPercentage,
        currentStepElement: !!currentStepElement,
        stepTitleElement: !!stepTitleElement,
        mobileStepTitleElement: !!mobileStepTitleElement
    });
    
    // ================= INITIALIZATION =================
    function initForm() {
        // Count existing academic entries from Django template
        const existingEntries = academicContainer.querySelectorAll('.academic-entry');
        academicEntryCount = existingEntries.length;
        
        updateStep(); // Set initial step state
        loadSavedData(); // Load any saved progress
    }
    
    // ================= NAVIGATION =================
    function goToNextStep() {
        console.log('goToNextStep called, current step:', currentStep);
        
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                currentStep++;
                console.log('Moving to step:', currentStep);
                updateStep();
                saveProgressWithTime();
            } else {
                console.log('Already at last step');
            }
        } else {
            console.log('Validation failed for step:', currentStep);
        }
    }
    
    function goToPrevStep() {
        console.log('goToPrevStep called, current step:', currentStep);
        
        if (currentStep > 1) {
            currentStep--;
            console.log('Moving back to step:', currentStep);
            updateStep();
        } else {
            console.log('Already at first step');
        }
    }
    
    // ================= STEP UPDATE =================
    function updateStep() {
        console.log('Updating step to:', currentStep); // Debug log
        
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
        
        // Update form step visibility
        formSteps.forEach(step => {
            step.classList.remove('active');
        });
        const activeStep = document.getElementById(`step${currentStep}`);
        if (activeStep) {
            activeStep.classList.add('active');
        }
        
        // Update navigation buttons
        if (prevBtn) prevBtn.classList.toggle('hidden', currentStep === 1);
        if (nextBtn) nextBtn.classList.toggle('hidden', currentStep === totalSteps);
        if (submitBtn) submitBtn.classList.toggle('hidden', currentStep !== totalSteps);
        
        // Calculate progress percentage correctly
        // Step 1 = 0%, Step 2 = 25%, Step 3 = 50%, Step 4 = 75%, Step 5 = 100%
        const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
        
        console.log('Progress calculation:', {
            currentStep,
            totalSteps,
            calculation: `((${currentStep} - 1) / (${totalSteps} - 1)) * 100`,
            progressPercent
        }); // Debug log
        
        // Update all progress bars with the calculated percentage
        if (progressBar) {
            progressBar.style.width = `${progressPercent}%`;
            console.log('Desktop progress bar updated to:', progressPercent + '%');
        }
        if (mobileProgressBar) {
            mobileProgressBar.style.width = `${progressPercent}%`;
            console.log('Mobile progress bar updated to:', progressPercent + '%');
        }
        if (stepProgressBar) {
            stepProgressBar.style.width = `${progressPercent}%`;
            console.log('Step progress bar updated to:', progressPercent + '%');
        }
        
        // Update percentage text
        const percentText = Math.round(progressPercent);
        if (progressPercentage) {
            progressPercentage.textContent = percentText;
            console.log('Desktop percentage text updated to:', percentText);
        }
        if (mobileProgressPercentage) {
            mobileProgressPercentage.textContent = percentText;
            console.log('Mobile percentage text updated to:', percentText);
        }
        
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
        const requiredInputs = activeStep.querySelectorAll('[required]');
        
        // Clear previous errors
        activeStep.querySelectorAll('.error-message').forEach(el => el.textContent = '');
        activeStep.querySelectorAll('.border-red-500').forEach(el => {
            el.classList.remove('border-red-500');
        });
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('border-red-500');
                
                const errorDiv = input.parentElement.querySelector('.error-message');
                if (errorDiv) {
                    errorDiv.textContent = 'This field is required';
                }
            }
        });
        
        // Step 2: Validate at least one academic entry
        if (step === 2) {
            const educationLevels = document.querySelectorAll('[name="educationLevel[]"]');
            let hasValidEntry = false;
            educationLevels.forEach(select => {
                if (select.value) hasValidEntry = true;
            });
            
            if (!hasValidEntry) {
                showMessage('Please add at least one academic entry', 'error');
                isValid = false;
            }
        }
        
        // Step 5: Validate declarations
        if (step === 5) {
            const declaration = document.querySelector('[name="declaration"]');
            const privacy = document.querySelector('[name="privacy"]');
            
            if (declaration && !declaration.checked) {
                showMessage('Please accept the declaration', 'error');
                isValid = false;
            }
            if (privacy && !privacy.checked) {
                showMessage('Please accept the privacy policy', 'error');
                isValid = false;
            }
        }
        
        if (!isValid) {
            showMessage('Please complete all required fields', 'error');
        }
        
        return isValid;
    }
    
    // ================= ACADEMIC HISTORY =================
    // Note: Academic entry HTML is now generated by Django template for first entry
    // This function only adds additional entries dynamically
    function addAcademicEntry() {
        academicEntryCount++;
        
        // Clone the first academic entry as template
        const firstEntry = academicContainer.querySelector('.academic-entry');
        if (!firstEntry) return;
        
        const newEntry = firstEntry.cloneNode(true);
        const entryId = `academicEntry${academicEntryCount}`;
        newEntry.id = entryId;
        
        // Clear all input values in the cloned entry
        newEntry.querySelectorAll('input, select').forEach(input => {
            input.value = '';
        });
        
        // Update the entry number
        const entryTitle = newEntry.querySelector('.entry-title');
        if (entryTitle) {
            entryTitle.textContent = `Academic Entry #${academicEntryCount}`;
        }
        
        // Add remove button if it's not the first entry
        if (academicEntryCount > 1) {
            let removeBtn = newEntry.querySelector('.remove-entry-btn');
            if (!removeBtn) {
                removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'remove-entry-btn absolute top-4 right-4 text-red-500 hover:text-red-700 font-bold text-xl';
                removeBtn.innerHTML = '×';
                removeBtn.onclick = function() { removeAcademicEntry(entryId); };
                newEntry.style.position = 'relative';
                newEntry.appendChild(removeBtn);
            }
        }
        
        academicContainer.appendChild(newEntry);
        
        if (addAcademicBtn) {
            addAcademicBtn.textContent = `+ Add Another Academic Entry (${academicEntryCount} added)`;
        }
    }
    
    window.removeAcademicEntry = function(entryId) {
        const entry = document.getElementById(entryId);
        if (entry && academicEntryCount > 1) {
            entry.remove();
            academicEntryCount--;
            
            if (addAcademicBtn) {
                addAcademicBtn.textContent = academicEntryCount > 1 
                    ? `+ Add Another Academic Entry (${academicEntryCount} added)`
                    : '+ Add Another Academic Entry';
            }
        }
    };
    
    // ================= REVIEW SECTION =================
    function updateReviewSection() {
        const reviewSummary = document.getElementById('reviewSummary');
        if (!reviewSummary) return;
        
        const formData = new FormData(form);
        
        let summaryHTML = `
            <div class="mb-4">
                <h4 class="font-semibold mb-2">Personal Information</h4>
                <p>Name: ${formData.get('first_name') || ''} ${formData.get('last_name') || ''}</p>
                <p>Email: ${formData.get('email') || ''}</p>
                <p>Phone: ${formData.get('phone') || ''}</p>
                <p>Country: ${formData.get('country') || ''}</p>
            </div>
            
            <div class="mb-4">
                <h4 class="font-semibold mb-2">Academic History</h4>
                <p>${academicEntryCount} academic ${academicEntryCount === 1 ? 'entry' : 'entries'} provided</p>
            </div>
            
            <div class="mb-4">
                <h4 class="font-semibold mb-2">Program Selection</h4>
                <p>Program: ${formData.get('program') || 'Not selected'}</p>
                <p>Degree Level: ${formData.get('degree_level') || 'Not selected'}</p>
                <p>Study Mode: ${formData.get('study_mode') || 'Not selected'}</p>
                <p>Intake: ${formData.get('intake') || 'Not selected'}</p>
            </div>
        `;
        
        reviewSummary.innerHTML = summaryHTML;
    }
    
    // ================= FORM SUBMISSION (AJAX) =================
    function submitApplication(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!validateStep(5)) return false;
        
        const formData = new FormData(form);
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span> Submitting...';
        
        // Show loading message
        showMessage('Submitting your application...', 'info');
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message
                showSuccessMessage(data.application_id);
                
                // Clear saved progress
                localStorage.removeItem('miuApplication');
                
                // Hide all form steps
                document.querySelectorAll('.form-step').forEach(step => {
                    step.classList.add('hidden');
                });
                
                // Hide navigation buttons
                if (prevBtn) prevBtn.classList.add('hidden');
                if (nextBtn) nextBtn.classList.add('hidden');
                if (submitBtn) submitBtn.classList.add('hidden');
                
                // Update progress to 100%
                if (progressBar) progressBar.style.width = '100%';
                if (mobileProgressBar) mobileProgressBar.style.width = '100%';
                if (stepProgressBar) stepProgressBar.style.width = '100%';
                if (progressPercentage) progressPercentage.textContent = '100';
                if (mobileProgressPercentage) mobileProgressPercentage.textContent = '100';
                
                // Mark all steps as completed
                progressSteps.forEach(step => {
                    step.classList.remove('active');
                    step.classList.add('completed');
                });
                
            } else {
                showMessage(data.error || 'An error occurred. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Application';
            }
        })
        .catch(error => {
            console.error('Submission Error:', error);
            showMessage('Network error. Please check your connection and try again.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Application';
        });
        
        return false;
    }
    
    // ================= SUCCESS MESSAGE DISPLAY =================
    function showSuccessMessage(applicationId) {
        const messagesDiv = document.getElementById('formMessages');
        if (!messagesDiv) return;
        
        const successHTML = `
            <div class="bg-white rounded-2xl shadow-2xl p-8 md:p-12 border-4 border-green-500 animate-scale-in">
                <div class="text-center">
                    <div class="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
                        <svg class="w-16 h-16 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    
                    <h2 class="text-3xl md:text-4xl font-bold mb-4" style="color: #840384;">
                        🎉 Application Submitted Successfully!
                    </h2>
                    
                    <div class="bg-purple-50 border-2 border-purple-300 rounded-lg p-6 mb-6">
                        <p class="text-sm text-gray-600 mb-2">Your Application ID</p>
                        <p class="text-2xl md:text-3xl font-bold" style="color: #840384;">${applicationId}</p>
                    </div>
                    
                    <div class="space-y-4 text-left max-w-2xl mx-auto mb-8">
                        <div class="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
                            <svg class="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <div>
                                <h4 class="font-bold text-gray-900 mb-1">What's Next?</h4>
                                <p class="text-gray-700 text-sm">Our admissions team will review your application within 5-7 business days.</p>
                            </div>
                        </div>
                        
                        <div class="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
                            <svg class="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            <div>
                                <h4 class="font-bold text-gray-900 mb-1">Email Confirmation</h4>
                                <p class="text-gray-700 text-sm">A confirmation email has been sent to your registered email address.</p>
                            </div>
                        </div>
                        
                        <div class="flex items-start gap-3 p-4 bg-yellow-50 rounded-lg">
                            <svg class="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <div>
                                <h4 class="font-bold text-gray-900 mb-1">Save Your Application ID</h4>
                                <p class="text-gray-700 text-sm">Please save your Application ID for future reference and tracking.</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="/" 
                           class="inline-block px-8 py-4 text-white rounded-lg font-bold text-lg hover:opacity-90 transition-all shadow-lg" 
                           style="background-color: #840384;">
                            Return to Home
                        </a>
                        
                        <button onclick="window.print()" 
                                class="inline-block px-8 py-4 bg-gray-700 text-white rounded-lg font-bold text-lg hover:bg-gray-800 transition-all shadow-lg">
                            Print Confirmation
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        messagesDiv.innerHTML = successHTML;
        messagesDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // ================= SAVE & LOAD PROGRESS =================
    function saveProgressWithTime() {
        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            if (key.endsWith('[]')) {
                if (!data[key]) data[key] = [];
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }
        
        data.currentStep = currentStep;
        data.academicEntryCount = academicEntryCount;
        data.savedTime = Date.now();
        
        localStorage.setItem('miuApplication', JSON.stringify(data));
    }
    
    function loadSavedData() {
        const savedData = localStorage.getItem('miuApplication');
        if (!savedData) return;
        
        try {
            const data = JSON.parse(savedData);
            
            // Check if data is too old (more than 24 hours)
            const savedTime = data.savedTime || 0;
            const currentTime = Date.now();
            const hoursDiff = (currentTime - savedTime) / (1000 * 60 * 60);
            
            if (hoursDiff > 24) {
                localStorage.removeItem('miuApplication');
                return;
            }
            
            // Restore academic entries
            if (data.academicEntryCount && data.academicEntryCount > 1) {
                for (let i = 1; i < data.academicEntryCount; i++) {
                    addAcademicEntry();
                }
            }
            
            // Restore form values
            Object.keys(data).forEach(key => {
                if (key === 'currentStep' || key === 'academicEntryCount' || key === 'savedTime') return;
                
                if (key.endsWith('[]')) {
                    const elements = form.querySelectorAll(`[name="${key}"]`);
                    const values = Array.isArray(data[key]) ? data[key] : [data[key]];
                    values.forEach((value, index) => {
                        if (elements[index]) elements[index].value = value;
                    });
                } else {
                    const element = form.querySelector(`[name="${key}"]`);
                    if (element) {
                        if (element.type === 'radio' || element.type === 'checkbox') {
                            if (element.value === data[key]) element.checked = true;
                        } else {
                            element.value = data[key];
                        }
                    }
                }
            });
            
            // Restore step
            if (data.currentStep) {
                currentStep = parseInt(data.currentStep);
                updateStep();
            }
            
            showMessage('Previous progress restored', 'info');
        } catch (error) {
            console.error('Error loading saved data:', error);
            localStorage.removeItem('miuApplication');
        }
    }
    
    // ================= MESSAGE DISPLAY =================
    function showMessage(message, type = 'info') {
        const messagesDiv = document.getElementById('formMessages');
        if (!messagesDiv) return;
        
        const colors = {
            success: 'bg-green-50 border-green-500 text-green-800',
            error: 'bg-red-50 border-red-500 text-red-800',
            info: 'bg-blue-50 border-blue-500 text-blue-800'
        };
        
        const messageHTML = `
            <div class="${colors[type]} border-l-4 p-4 rounded-lg mb-4" role="alert">
                <p class="font-medium">${message}</p>
            </div>
        `;
        
        messagesDiv.innerHTML = messageHTML;
        messagesDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Auto-hide info messages after 5 seconds
        if (type === 'info') {
            setTimeout(() => {
                messagesDiv.innerHTML = '';
            }, 5000);
        }
    }
    
    // ================= EVENT LISTENERS =================
    if (prevBtn) prevBtn.addEventListener('click', goToPrevStep);
    if (nextBtn) nextBtn.addEventListener('click', goToNextStep);
    if (submitBtn) submitBtn.addEventListener('click', submitApplication);
    if (addAcademicBtn) addAcademicBtn.addEventListener('click', addAcademicEntry);
    
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
    
    // Initialize the form
    initForm();
});