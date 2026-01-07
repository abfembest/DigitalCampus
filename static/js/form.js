// Mobile menu toggle
const menuBtn = document.getElementById('menuBtn');
const mobileMenu = document.getElementById('mobileMenu');

menuBtn.onclick = () => {
    mobileMenu.classList.toggle("hidden");
    // Close programs menu when mobile menu closes
    programsMenuMobile.classList.add("hidden");
    programsArrowMobile.style.transform = "";
};

// Programs dropdown functionality for desktop
const programsBtnDesktop = document.getElementById('programsBtnDesktop');
const programsMenuDesktop = document.getElementById('programsMenuDesktop');

// Programs dropdown functionality for mobile
const programsBtnMobile = document.getElementById('programsBtnMobile');
const programsMenuMobile = document.getElementById('programsMenuMobile');
const programsArrowMobile = document.getElementById('programsArrowMobile');

let programsMenuOpen = false;

// Toggle desktop programs menu
programsBtnDesktop.addEventListener('click', (e) => {
    e.stopPropagation();
    programsMenuOpen = !programsMenuOpen;
    if (programsMenuOpen) {
        programsMenuDesktop.classList.remove("hidden");
        programsMenuDesktop.classList.add("dropdown-enter");
    } else {
        programsMenuDesktop.classList.add("hidden");
    }
});

// Toggle mobile programs menu
programsBtnMobile.addEventListener('click', (e) => {
    e.stopPropagation();
    programsMenuOpen = !programsMenuOpen;
    if (programsMenuOpen) {
        programsMenuMobile.classList.remove("hidden");
        programsMenuMobile.classList.add("dropdown-enter");
        programsArrowMobile.style.transform = "rotate(180deg)";
    } else {
        programsMenuMobile.classList.add("hidden");
        programsArrowMobile.style.transform = "";
    }
});

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    // Check if click is outside desktop programs dropdown
    if (!programsBtnDesktop.contains(e.target) && !programsMenuDesktop.contains(e.target)) {
        programsMenuDesktop.classList.add("hidden");
        programsMenuOpen = false;
    }

    // For mobile, only close if clicking outside both menu button and mobile menu itself
    if (window.innerWidth < 1024) {
        if (!programsBtnMobile.contains(e.target) && !programsMenuMobile.contains(e.target) &&
            !menuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
            mobileMenu.classList.add("hidden");
            programsMenuMobile.classList.add("hidden");
            programsMenuOpen = false;
            programsArrowMobile.style.transform = "";
        }
    }
});

// Close dropdown when a program is selected
const programLinks = document.querySelectorAll('[data-program]');
programLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();

        // Get the program type
        const programType = link.getAttribute('data-program');

        // Show selected program (in a real site, this would navigate to program page)
        alert(`You selected: ${link.textContent}`);

        // Close all dropdowns
        programsMenuDesktop.classList.add("hidden");
        programsMenuMobile.classList.add("hidden");
        programsMenuOpen = false;
        programsArrowMobile.style.transform = "";

        // Also close mobile menu on mobile
        if (window.innerWidth < 1024) {
            mobileMenu.classList.add("hidden");
        }
    });
});

// Hero carousel
let slides = document.querySelectorAll(".slide");
let indicators = document.querySelectorAll(".carousel-indicator");
let index = 0;

function showSlide(n) {
    slides.forEach(slide => slide.classList.add("hidden"));
    indicators.forEach(ind => ind.classList.remove("bg-white", "opacity-100"));
    indicators.forEach(ind => ind.classList.add("opacity-50"));

    index = n;
    slides[index].classList.remove("hidden");
    indicators[index].classList.remove("opacity-50");
    indicators[index].classList.add("bg-white", "opacity-100");
}

// Add click events to indicators
indicators.forEach((indicator, i) => {
    indicator.onclick = () => showSlide(i);
});

setInterval(() => {
    let nextIndex = (index + 1) % slides.length;
    showSlide(nextIndex);
}, 5000);


// Map controls (simulated - in a real implementation these would interact with the map API)
document.querySelectorAll('.map-container + div button').forEach(button => {
    button.addEventListener('click', function () {
        const action = this.innerHTML.includes('➕') ? 'Zoom In' :
            this.innerHTML.includes('➖') ? 'Zoom Out' : 'Reset View';
        console.log(`Map action: ${action}`);
        // In a real implementation, this would call the map API
    });
});


// ================= APPLICATION FORM JAVASCRIPT =================
// Global variables for the application form
let applicationFormInitialized = false;

// Initialize application form when the page loads
document.addEventListener('DOMContentLoaded', function () {
    // Only initialize if we're on the application form section
    const applicationForm = document.getElementById('applicationForm');
    if (applicationForm && !applicationFormInitialized) {
        initializeApplicationForm();
        applicationFormInitialized = true;
    }
});

// Initialize the application form
function initializeApplicationForm() {
    // Step Management
    let currentStep = 1;
    const totalSteps = 5;
    const form = document.getElementById('applicationForm');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressSteps = document.querySelectorAll('.progress-step');
    const formSteps = document.querySelectorAll('.form-step');
    const progressBar = document.getElementById('progressBar');
    const stepProgressBar = document.getElementById('stepProgressBar');
    const mobileProgressBar = document.getElementById('mobileProgressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const stepProgressPercentage = document.getElementById('stepProgressPercentage');
    const mobileProgressPercentage = document.getElementById('mobileProgressPercentage');
    const currentStepElement = document.getElementById('currentStep');
    const mobileCurrentStepElement = document.getElementById('mobileCurrentStep');
    const stepTitleElement = document.getElementById('stepTitle');
    const mobileStepTitleElement = document.getElementById('mobileStepTitle');
    const successMessage = document.getElementById('successMessage');

    // File Upload Variables
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const browseFilesBtn = document.getElementById('browseFilesBtn');
    let currentUploadType = null; // Track which document type is being uploaded
    const uploadedFiles = {
        transcripts: false,
        english: false,
        statement: false,
        cv: false,
        additional: []
    };

    // Academic History Variables
    const academicEntriesContainer = document.getElementById('academicEntriesContainer');
    const addAcademicEntryBtn = document.getElementById('addAcademicEntryBtn');
    let academicEntryCount = 0;

    // Step titles for display
    const stepTitles = {
        1: "Personal Information",
        2: "Academic History",
        3: "Course Selection",
        4: "Documents",
        5: "Review & Submit"
    };

    // Initialize the form
    initForm();

    // Navigation Event Listeners
    if (prevBtn) prevBtn.addEventListener('click', goToPrevStep);
    if (nextBtn) nextBtn.addEventListener('click', goToNextStep);

    // Form submission
    if (form) form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitApplication();
    });

    // Save progress button
    const saveProgressBtn = document.getElementById('saveProgressBtn');
    if (saveProgressBtn) saveProgressBtn.addEventListener('click', saveProgress);

    // Add academic entry button
    if (addAcademicEntryBtn) addAcademicEntryBtn.addEventListener('click', addAcademicEntry);

    // File upload functionality
    if (dropArea && browseFilesBtn && fileInput) {
        // Click to browse files
        browseFilesBtn.addEventListener('click', () => fileInput.click());
        dropArea.addEventListener('click', () => fileInput.click());

        // Drag and drop functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight() {
            dropArea.classList.add('dragover');
        }

        function unhighlight() {
            dropArea.classList.remove('dragover');
        }

        // Handle file drop
        dropArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }

        // Handle file selection via input
        fileInput.addEventListener('change', function () {
            handleFiles(this.files);
        });
    }

    // Step click handlers
    if (progressSteps.length > 0) {
        progressSteps.forEach(step => {
            step.addEventListener('click', function () {
                const stepNum = parseInt(this.getAttribute('data-step'));
                if (stepNum < currentStep || validateStep(currentStep)) {
                    currentStep = stepNum;
                    updateStep();
                }
            });
        });
    }

    // Functions
    function initForm() {
        // Load saved data from localStorage
        loadSavedData();

        // Add the first academic entry
        addAcademicEntry();

        // Update the form
        updateStep();
    }

    function goToPrevStep() {
        if (currentStep > 1) {
            currentStep--;
            updateStep();
        }
    }

    function goToNextStep() {
        // Validate current step before proceeding
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                currentStep++;
                updateStep();
                saveProgress(); // Auto-save on step change
            }
        }
    }

    function updateStep() {
        // Update step titles
        if (stepTitleElement) stepTitleElement.textContent = stepTitles[currentStep];
        if (mobileStepTitleElement) mobileStepTitleElement.textContent = stepTitles[currentStep];

        // Update progress indicator
        if (progressSteps.length > 0) {
            progressSteps.forEach(step => {
                const stepNum = parseInt(step.getAttribute('data-step'));
                step.classList.remove('active', 'completed');

                if (stepNum < currentStep) {
                    step.classList.add('completed');
                } else if (stepNum === currentStep) {
                    step.classList.add('active');
                }
            });
        }

        // Update form steps visibility
        if (formSteps.length > 0) {
            formSteps.forEach(step => {
                step.classList.remove('active');
                if (step.id === `step${currentStep}`) {
                    step.classList.add('active');
                }
            });
        }

        // Update navigation buttons
        if (prevBtn) prevBtn.classList.toggle('hidden', currentStep === 1);
        if (nextBtn) nextBtn.classList.toggle('hidden', currentStep === totalSteps);
        if (submitBtn) submitBtn.classList.toggle('hidden', currentStep !== totalSteps);

        // Update step numbers
        if (currentStepElement) currentStepElement.textContent = currentStep;
        if (mobileCurrentStepElement) mobileCurrentStepElement.textContent = currentStep;

        // Update progress bars
        const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
        if (progressBar) progressBar.style.width = `${progressPercent}%`;
        if (mobileProgressBar) mobileProgressBar.style.width = `${progressPercent}%`;
        if (progressPercentage) progressPercentage.textContent = `${Math.round(progressPercent)}%`;
        if (mobileProgressPercentage) mobileProgressPercentage.textContent = `${Math.round(progressPercent)}%`;

        // Step-specific progress (showing completion within step)
        const stepProgressPercent = currentStep === 5 ? 100 : 20;
        if (stepProgressBar) stepProgressBar.style.width = `${stepProgressPercent}%`;
        if (stepProgressPercentage) stepProgressPercentage.textContent = `${stepProgressPercent}%`;

        // Update review section if on step 5
        if (currentStep === 5) {
            updateReviewSection();
        }

        // Scroll to top of form
        const formContent = document.querySelector('.form-content');
        if (formContent) {
            formContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function validateStep(step) {
        let isValid = true;
        const activeStep = document.getElementById(`step${step}`);
        if (!activeStep) return false;

        const requiredInputs = activeStep.querySelectorAll('[required]');

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('border-red-500');

                // Add error message if not already present
                if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('error-message')) {
                    const errorMsg = document.createElement('p');
                    errorMsg.className = 'error-message text-red-500 text-sm mt-1';
                    errorMsg.textContent = 'This field is required';
                    input.parentNode.appendChild(errorMsg);
                }
            } else {
                input.classList.remove('border-red-500');

                // Remove error message if exists
                const errorMsg = input.parentNode.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });

        // Special validation for step 4 (documents)
        if (step === 4) {
            // Check if at least transcripts and statement are uploaded
            if (!uploadedFiles.transcripts || !uploadedFiles.statement) {
                alert('Please upload at least your academic transcripts and personal statement before proceeding.');
                isValid = false;
            }
        }

        return isValid;
    }

    function addAcademicEntry() {
        academicEntryCount++;
        const entryId = `academicEntry${academicEntryCount}`;

        const entryHTML = `
      <div class="academic-entry" id="${entryId}">
        <button type="button" class="remove-entry" onclick="removeAcademicEntry('${entryId}')">×</button>
        <h4 class="font-bold text-lg mb-4 text-miu-primary">Academic Entry #${academicEntryCount}</h4>
        
        <div class="mb-4">
          <label class="block text-gray-700 mb-2 font-medium">Level of Education <span class="text-red-500">*</span></label>
          <select name="educationLevel[]" required class="w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition bg-white">
            <option value="">Select Education Level</option>
            <option value="high-school">High School Diploma</option>
            <option value="associate">Associate Degree</option>
            <option value="bachelor">Bachelor's Degree</option>
            <option value="master">Master's Degree</option>
            <option value="phd">PhD</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 mb-2 font-medium">Name of Institution <span class="text-red-500">*</span></label>
          <input type="text" name="institution[]" required class="w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition">
        </div>
        
        <div class="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-gray-700 mb-2 font-medium">Field of Study</label>
            <input type="text" name="fieldOfStudy[]" class="w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition">
          </div>
          
          <div>
            <label class="block text-gray-700 mb-2 font-medium">Graduation Year <span class="text-red-500">*</span></label>
            <input type="number" name="graduationYear[]" min="1950" max="2025" required class="w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition">
          </div>
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 mb-2 font-medium">GPA / Final Grade</label>
          <div class="flex items-center">
            <input type="text" name="gpa[]" class="w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition">
            <span class="ml-2 text-gray-500">(on a 4.0 scale or equivalent)</span>
          </div>
        </div>
      </div>
    `;

        if (academicEntriesContainer) {
            academicEntriesContainer.insertAdjacentHTML('beforeend', entryHTML);
        }

        // Update the add button text if we have multiple entries
        if (addAcademicEntryBtn && academicEntryCount > 1) {
            addAcademicEntryBtn.textContent = `+ Add Another Academic Entry (${academicEntryCount} added)`;
        }
    }

    // Make removeAcademicEntry available globally
    window.removeAcademicEntry = function (entryId) {
        const entry = document.getElementById(entryId);
        if (entry) {
            entry.remove();
            academicEntryCount--;

            // Update the count on the button
            if (addAcademicEntryBtn && academicEntryCount > 0) {
                addAcademicEntryBtn.textContent = `+ Add Another Academic Entry (${academicEntryCount} added)`;
            } else if (addAcademicEntryBtn) {
                addAcademicEntryBtn.textContent = '+ Add Another Academic Entry';
            }

            // If we removed the last entry, add a new one
            if (academicEntryCount === 0) {
                addAcademicEntry();
            }
        }
    };

    // Function to upload specific document type
    window.uploadSpecificDocument = function (docType) {
        currentUploadType = docType;
        if (fileInput) fileInput.click();
    };

    function handleFiles(files) {
        [...files].forEach(file => {
            // Check file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                return;
            }

            // Check file type
            const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                alert(`File "${file.name}" is not a supported file type. Please upload PDF, DOC, DOCX, JPG, or PNG files.`);
                return;
            }

            // Simulate file upload
            simulateFileUpload(file);
        });
    }

    function simulateFileUpload(file) {
        // Determine document type based on currentUploadType or filename
        let docType = currentUploadType || 'additional';
        const fileName = file.name.toLowerCase();

        // If no specific type is selected, try to guess from filename
        if (!currentUploadType) {
            if (fileName.includes('transcript') || fileName.includes('academic') || fileName.includes('grade')) {
                docType = 'transcripts';
            } else if (fileName.includes('ielts') || fileName.includes('toefl') || fileName.includes('english') || fileName.includes('proficiency')) {
                docType = 'english';
            } else if (fileName.includes('statement') || fileName.includes('purpose') || fileName.includes('personal')) {
                docType = 'statement';
            } else if (fileName.includes('cv') || fileName.includes('resume') || fileName.includes('curriculum')) {
                docType = 'cv';
            } else {
                docType = 'additional';
            }
        }

        // Update status
        if (docType !== 'additional') {
            uploadedFiles[docType] = true;
            updateDocumentStatus(docType, file.name);
        } else {
            uploadedFiles.additional.push(file.name);
            addAdditionalFile(file.name);
        }

        // Reset current upload type
        currentUploadType = null;

        // Show success message
        showUploadSuccess(file.name);
    }

    function updateDocumentStatus(docType, fileName) {
        const statusElement = document.getElementById(`${docType}Status`);
        const documentItem = document.querySelector(`[data-doc-type="${docType}"]`);

        if (statusElement) {
            statusElement.textContent = fileName.length > 20 ? fileName.substring(0, 17) + '...' : fileName;
            statusElement.className = 'text-sm text-green-600 mr-4';

            // Update icon
            const iconElement = statusElement.parentNode.querySelector('.flex.items-center > div:last-child');
            if (iconElement) {
                iconElement.innerHTML = '<span class="text-green-500">✓</span>';
                iconElement.className = 'w-8 h-8 rounded-full bg-green-100 flex items-center justify-center';
            }
        }

        if (documentItem) {
            documentItem.classList.add('uploaded');
        }
    }

    function addAdditionalFile(fileName) {
        const additionalFilesContainer = document.getElementById('additionalFiles');
        if (!additionalFilesContainer) return;

        // Remove placeholder if present
        const placeholder = additionalFilesContainer.querySelector('p');
        if (placeholder && placeholder.textContent.includes('No additional documents')) {
            placeholder.remove();
        }

        // Add file element
        const fileElement = document.createElement('div');
        fileElement.className = 'uploaded-file';
        fileElement.innerHTML = `
      <div class="flex items-center">
        <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
          <span class="text-blue-600">📄</span>
        </div>
        <div>
          <p class="font-medium">${fileName}</p>
          <p class="text-xs text-gray-500">${formatFileSize(Math.floor(Math.random() * 5000) + 100)} KB</p>
        </div>
      </div>
      <button type="button" class="text-red-500 hover:text-red-700" onclick="removeAdditionalFile(this)">
        Remove
      </button>
    `;

        additionalFilesContainer.appendChild(fileElement);
    }

    function showUploadSuccess(fileName) {
        // Create and show a temporary success notification
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-green-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
      <div class="flex items-center">
        <span class="text-xl mr-2">✓</span>
        <div>
          <p class="font-medium">File uploaded successfully</p>
          <p class="text-sm opacity-90">${fileName}</p>
        </div>
      </div>
    `;

        document.body.appendChild(notification);

        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes;
        return (bytes / 1024).toFixed(1);
    }

    // Make removeAdditionalFile available globally
    window.removeAdditionalFile = function (button) {
        const fileElement = button.closest('.uploaded-file');
        const fileName = fileElement.querySelector('.font-medium').textContent;

        // Remove from uploadedFiles array
        uploadedFiles.additional = uploadedFiles.additional.filter(name => name !== fileName);

        // Remove from DOM
        fileElement.remove();

        // Show placeholder if no files left
        const additionalFilesContainer = document.getElementById('additionalFiles');
        if (uploadedFiles.additional.length === 0 && additionalFilesContainer.children.length === 0) {
            const placeholder = document.createElement('p');
            placeholder.className = 'text-gray-500 text-sm';
            placeholder.textContent = 'No additional documents uploaded yet. Use the upload area above or click "Browse Files" to add additional documents.';
            additionalFilesContainer.appendChild(placeholder);
        }
    };

    function updateReviewSection() {
        // Personal Information
        const personalData = {
            name: `${form.querySelector('[name="firstName"]').value} ${form.querySelector('[name="lastName"]').value}`,
            email: form.querySelector('[name="email"]').value,
            phone: form.querySelector('[name="phone"]').value,
            dob: form.querySelector('[name="dob"]').value,
            country: form.querySelector('[name="country"]').value
        };

        const reviewPersonal = document.getElementById('reviewPersonal');
        if (reviewPersonal) {
            reviewPersonal.innerHTML = `
        <p><strong>Name:</strong> ${personalData.name || 'Not provided'}</p>
        <p><strong>Email:</strong> ${personalData.email || 'Not provided'}</p>
        <p><strong>Phone:</strong> ${personalData.phone || 'Not provided'}</p>
        <p><strong>Country:</strong> ${personalData.country || 'Not provided'}</p>
      `;
        }

        // Academic History - collect all entries
        const educationLevels = form.querySelectorAll('[name="educationLevel[]"]');
        const institutions = form.querySelectorAll('[name="institution[]"]');
        const graduationYears = form.querySelectorAll('[name="graduationYear[]"]');

        let academicHTML = '';
        for (let i = 0; i < educationLevels.length; i++) {
            const level = educationLevels[i].value ? educationLevels[i].value.replace('-', ' ').toUpperCase() : 'Not provided';
            const institution = institutions[i].value || 'Not provided';
            const year = graduationYears[i].value || 'Not provided';

            academicHTML += `<p><strong>Entry ${i + 1}:</strong> ${level} from ${institution} (${year})</p>`;
        }

        const reviewAcademic = document.getElementById('reviewAcademic');
        if (reviewAcademic) {
            reviewAcademic.innerHTML = academicHTML || '<p>No academic history provided</p>';
        }

        // Course Selection
        const courseData = {
            program: form.querySelector('[name="program"]').value,
            degree: document.querySelector('[name="degreeLevel"]:checked') ? document.querySelector('[name="degreeLevel"]:checked').value : 'Not selected',
            mode: document.querySelector('[name="studyMode"]:checked') ? document.querySelector('[name="studyMode"]:checked').value : 'Not selected',
            intake: document.querySelector('[name="intake"]:checked') ? document.querySelector('[name="intake"]:checked').value : 'Not selected'
        };

        const reviewCourse = document.getElementById('reviewCourse');
        if (reviewCourse) {
            reviewCourse.innerHTML = `
        <p><strong>Program:</strong> ${courseData.program ? courseData.program.replace('-', ' ').toUpperCase() : 'Not provided'}</p>
        <p><strong>Degree Level:</strong> ${courseData.degree ? courseData.degree.replace('-', ' ').toUpperCase() : 'Not provided'}</p>
        <p><strong>Study Mode:</strong> ${courseData.mode ? courseData.mode.replace('-', ' ').toUpperCase() : 'Not provided'}</p>
        <p><strong>Intake:</strong> ${courseData.intake ? courseData.intake.replace('-', ' ').toUpperCase() : 'Not provided'}</p>
      `;
        }

        // Documents
        const docStatus = [];
        if (uploadedFiles.transcripts) docStatus.push('✓ Academic Transcripts');
        if (uploadedFiles.english) docStatus.push('✓ English Proficiency');
        if (uploadedFiles.statement) docStatus.push('✓ Personal Statement');
        if (uploadedFiles.cv) docStatus.push('✓ Curriculum Vitae');
        if (uploadedFiles.additional.length > 0) docStatus.push(`✓ ${uploadedFiles.additional.length} additional document(s)`);

        const reviewDocuments = document.getElementById('reviewDocuments');
        if (reviewDocuments) {
            reviewDocuments.innerHTML = docStatus.length > 0
                ? docStatus.map(item => `<p>${item}</p>`).join('')
                : '<p>No documents uploaded</p>';
        }
    }

    function saveProgress() {
        const formData = new FormData(form);
        const data = {};

        // Collect form data
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // If the key already exists (arrays), convert to array
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }

        // Add uploaded files status
        data.uploadedFiles = uploadedFiles;

        // Add academic entry count
        data.academicEntryCount = academicEntryCount;

        // Save to localStorage
        localStorage.setItem('miuApplication', JSON.stringify(data));
        localStorage.setItem('miuApplicationStep', currentStep);

        // Show save confirmation
        const saveBtn = document.getElementById('saveProgressBtn');
        if (saveBtn) {
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '✓ Progress Saved!';
            saveBtn.classList.add('text-green-600');

            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.classList.remove('text-green-600');
            }, 2000);
        }
    }

    function loadSavedData() {
        const savedData = localStorage.getItem('miuApplication');
        const savedStep = localStorage.getItem('miuApplicationStep');

        if (savedData) {
            const data = JSON.parse(savedData);

            // Clear existing academic entries except the first one
            const academicEntries = document.querySelectorAll('.academic-entry');
            academicEntries.forEach((entry, index) => {
                if (index > 0) entry.remove();
            });

            // Reset academic entry count
            academicEntryCount = data.academicEntryCount || 1;

            // Add additional academic entries if saved
            if (academicEntryCount > 1) {
                for (let i = 1; i < academicEntryCount; i++) {
                    addAcademicEntry();
                }
            }

            // Populate form fields
            Object.keys(data).forEach(key => {
                if (key !== 'uploadedFiles' && key !== 'academicEntryCount') {
                    if (key.endsWith('[]')) {
                        // Handle array inputs (academic entries)
                        const baseKey = key.replace('[]', '');
                        const elements = form.querySelectorAll(`[name="${key}"]`);
                        const values = Array.isArray(data[key]) ? data[key] : [data[key]];

                        values.forEach((value, index) => {
                            if (elements[index]) {
                                elements[index].value = value;
                            }
                        });
                    } else {
                        const element = form.querySelector(`[name="${key}"]`);
                        if (element) {
                            if (element.type === 'radio' || element.type === 'checkbox') {
                                if (element.value === data[key]) {
                                    element.checked = true;
                                }
                            } else {
                                element.value = data[key];
                            }
                        }
                    }
                }
            });

            // Load uploaded files status
            if (data.uploadedFiles) {
                Object.assign(uploadedFiles, data.uploadedFiles);

                // Update UI for uploaded files
                if (uploadedFiles.transcripts) updateDocumentStatus('transcripts', 'Transcripts.pdf');
                if (uploadedFiles.english) updateDocumentStatus('english', 'IELTS.pdf');
                if (uploadedFiles.statement) updateDocumentStatus('statement', 'PersonalStatement.pdf');
                if (uploadedFiles.cv) updateDocumentStatus('cv', 'CV.pdf');

                // Load additional files
                if (uploadedFiles.additional && uploadedFiles.additional.length > 0) {
                    uploadedFiles.additional.forEach(fileName => addAdditionalFile(fileName));
                }
            }

            // Restore step
            if (savedStep) {
                currentStep = parseInt(savedStep);
            }
        }
    }

    function submitApplication() {
        // Validate final step
        if (!validateStep(5)) {
            alert('Please complete all required fields before submitting.');
            return;
        }

        // Check declarations
        const declaration = document.getElementById('declaration');
        const privacy = document.getElementById('privacy');

        if (!declaration || !declaration.checked || !privacy || !privacy.checked) {
            alert('You must agree to the declaration and privacy policy before submitting.');
            return;
        }

        // Generate application ID
        const applicationId = 'MIU-2025-' + Math.floor(10000 + Math.random() * 90000);
        const applicationIdElement = document.getElementById('applicationId');
        if (applicationIdElement) applicationIdElement.textContent = applicationId;

        // Hide form, show success message
        if (form) form.style.display = 'none';
        if (successMessage) successMessage.classList.remove('hidden');

        // Save to localStorage as submitted
        const formData = new FormData(form);
        const data = {};
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }
        data.uploadedFiles = uploadedFiles;
        data.academicEntryCount = academicEntryCount;
        data.submitted = true;
        data.applicationId = applicationId;
        data.submissionDate = new Date().toISOString();

        localStorage.setItem('miuApplication', JSON.stringify(data));

        // Scroll to success message
        if (successMessage) {
            successMessage.scrollIntoView({ behavior: 'smooth' });
        }
    }
}
