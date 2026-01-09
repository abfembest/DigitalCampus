
// Mobile menu toggle
const menuBtn = document.getElementById('menuBtn');
const mobileMenu = document.getElementById('mobileMenu');

menuBtn.onclick = () => {
    mobileMenu.classList.toggle("hidden");
    // Close all dropdown menus when mobile menu closes
    programsMenuMobile.classList.add("hidden");
    programsArrowMobile.style.transform = "";
    facultiesMenuMobile.classList.add("hidden");
    facultiesArrowMobile.style.transform = "";
    moreMenuMobile.classList.add("hidden");
    moreArrowMobile.style.transform = "";
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

// Faculties dropdown functionality for mobile
const facultiesBtnMobile = document.getElementById('facultiesBtnMobile');
const facultiesMenuMobile = document.getElementById('facultiesMenuMobile');
const facultiesArrowMobile = document.getElementById('facultiesArrowMobile');
let facultiesMenuOpen = false;

// Toggle mobile faculties menu
facultiesBtnMobile.addEventListener('click', (e) => {
    e.stopPropagation();
    facultiesMenuOpen = !facultiesMenuOpen;
    if (facultiesMenuOpen) {
        facultiesMenuMobile.classList.remove("hidden");
        facultiesMenuMobile.classList.add("dropdown-enter");
        facultiesArrowMobile.style.transform = "rotate(180deg)";
    } else {
        facultiesMenuMobile.classList.add("hidden");
        facultiesArrowMobile.style.transform = "";
    }
});

// More dropdown functionality for mobile
const moreBtnMobile = document.getElementById('moreBtnMobile');
const moreMenuMobile = document.getElementById('moreMenuMobile');
const moreArrowMobile = document.getElementById('moreArrowMobile');
let moreMenuOpen = false;

// Toggle mobile more menu
moreBtnMobile.addEventListener('click', (e) => {
    e.stopPropagation();
    moreMenuOpen = !moreMenuOpen;
    if (moreMenuOpen) {
        moreMenuMobile.classList.remove("hidden");
        moreMenuMobile.classList.add("dropdown-enter");
        moreArrowMobile.style.transform = "rotate(180deg)";
    } else {
        moreMenuMobile.classList.add("hidden");
        moreArrowMobile.style.transform = "";
    }
});

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    // Check if click is outside desktop programs dropdown
    if (!programsBtnDesktop.contains(e.target) && !programsMenuDesktop.contains(e.target)) {
        programsMenuDesktop.classList.add("hidden");
        programsMenuOpen = false;
    }

    // For mobile, close if clicking outside any mobile menu element
    if (window.innerWidth < 1024) {
        const mobileMenuElements = [
            programsBtnMobile, programsMenuMobile,
            facultiesBtnMobile, facultiesMenuMobile,
            moreBtnMobile, moreMenuMobile,
            menuBtn, mobileMenu
        ];

        const isClickInside = mobileMenuElements.some(element =>
            element && element.contains(e.target)
        );

        if (!isClickInside) {
            mobileMenu.classList.add("hidden");
            programsMenuMobile.classList.add("hidden");
            programsMenuOpen = false;
            programsArrowMobile.style.transform = "";
            facultiesMenuMobile.classList.add("hidden");
            facultiesMenuOpen = false;
            facultiesArrowMobile.style.transform = "";
            moreMenuMobile.classList.add("hidden");
            moreMenuOpen = false;
            moreArrowMobile.style.transform = "";
        }
    }
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

// Testimonials carousel
const testimonials = [
    ["MIU's flexible online platform allowed me to complete my MBA while working full-time. The faculty support was exceptional, and I've already seen career advancement.", "Sarah K.", "MBA Graduate, 2023"],
    ["The Data Science program gave me practical skills that landed me a job at a tech giant before graduation. The curriculum is perfectly aligned with industry needs.", "Daniel P.", "Data Science Graduate, 2024"],
    ["As an international student, MIU provided the support I needed to succeed. The global community here is incredible.", "Amina R.", "Computer Science Student"]
];

let t = 0;
const quote = document.getElementById('quote');
const author = document.getElementById('author');
const testimonialIndicators = document.querySelectorAll('.testimonial-indicator');

function showTestimonial(n) {
    t = n;
    quote.textContent = testimonials[t][0];
    author.innerHTML = `<span class="font-bold text-lg">${testimonials[t][1]}</span><br><span class="text-gray-600">${testimonials[t][2]}</span>`;

    testimonialIndicators.forEach((ind, i) => {
        ind.classList.toggle('bg-gray-300', i !== n);
        ind.classList.toggle('bg-miu-secondary', i === n);
        ind.classList.toggle('w-2', i !== n);
        ind.classList.toggle('w-6', i === n);
    });
}

// Add click events to testimonial indicators
testimonialIndicators.forEach((indicator, i) => {
    indicator.onclick = () => showTestimonial(i);
});

setInterval(() => {
    let nextT = (t + 1) % testimonials.length;
    showTestimonial(nextT);
}, 6000);

// Form submission
// const contactForm = document.getElementById('contactForm');
// contactForm.onsubmit = (e) => {
//     e.preventDefault();
//     alert("Thank you for your message! We'll contact you soon.");
//     contactForm.reset();
// };

// Video fallback if iframe fails
window.addEventListener('load', () => {
    const videoFallback = document.getElementById('videoFallback');
    setTimeout(() => {
        // Check if iframe loaded properly (simplified check)
        const iframe = document.querySelector('iframe');
        if (iframe && iframe.offsetHeight === 0) {
            videoFallback.classList.remove('hidden');
        }
    }, 2000);
});

// Map controls (simulated - in a real implementation these would interact with the map API)
document.querySelectorAll('.map-container + div button').forEach(button => {
    button.addEventListener('click', function () {
        const action = this.innerHTML.includes('➕') ? 'Zoom In' :
            this.innerHTML.includes('➖') ? 'Zoom Out' : 'Reset View';
        console.log(`Map action: ${action}`);
        // In a real implementation, this would call the map API
    });
});



// ================= CHATBOT JAVASCRIPT =================
// Add this JavaScript at the end of your existing <script> section

// Chatbot State Management
let chatbotState = {
    isOpen: false,
    isMinimized: false,
    conversationHistory: [],
    currentTopic: null,
    userPreferences: {
        name: null,
        studentId: null,
        interests: []
    }
};

// Sample responses for different topics (in production, these would come from your LLM API)
const topicResponses = {
    academic: {
        title: "📚 Academic Support",
        response: `I can help you with various academic support services at MIU:

**Available Resources:**
• **24/7 Online Tutoring** - Get help with any course via our virtual tutoring platform
• **Writing Center** - Assistance with essays, research papers, and citations
• **Math Lab** - Drop-in help for calculus, statistics, and programming
• **Study Groups** - Connect with peers in your courses

**Upcoming Workshops:**
- Time Management for Online Learners (Tomorrow, 3 PM EST)
- Research Paper Writing (Friday, 2 PM EST)
- Exam Preparation Strategies (Next Monday, 4 PM EST)

**Need immediate help?** Visit the Academic Support Portal: https://miu.edu/academic-support`,
        quickActions: [
            { text: "Schedule Tutoring", action: "tutoring" },
            { text: "Find Study Groups", action: "study_groups" },
            { text: "View Workshop Calendar", action: "workshops" }
        ]
    },
    community: {
        title: "🌍 Virtual Community",
        response: `Welcome to our global MIU community! Here's how to connect:

**Virtual Campus Hub:**
• **Discord Server** - Join 5,000+ students in course-specific channels
• **Student Forums** - Discuss topics, share resources, ask questions
• **Virtual Lounges** - Hang out with peers in themed virtual spaces
• **Cultural Exchange** - Connect with students from 120+ countries

**Monthly Events:**
- International Food Night (1st Friday)
- Virtual Game Night (Every Wednesday)
- Study With Me Sessions (Daily, various times)

**Clubs & Organizations:**
We have 50+ student-run clubs including:
• Coding Club • Debate Society • Photography Club
• Environmental Club • Music Appreciation Society

Would you like me to connect you with any specific community?`,
        quickActions: [
            { text: "Join Discord", action: "discord" },
            { text: "View Club Directory", action: "clubs" },
            { text: "Upcoming Events", action: "events" }
        ]
    },
    activities: {
        title: "🎭 Extracurricular Activities",
        response: `Stay engaged with these extracurricular opportunities:

**Virtual Activities:**
• **Esports Team** - Compete in collegiate gaming tournaments
• **Virtual Book Club** - Monthly readings and discussions
• **Podcast Studio** - Create and host your own show
• **Digital Art Gallery** - Showcase your creative work

**Leadership Opportunities:**
- Student Government (elections in October)
- Club Executive Positions
- Peer Mentor Program
- Campus Ambassador Program

**Competitions & Hackathons:**
- Annual MIU Hackathon (March)
- Business Plan Competition
- Research Symposium
- Creative Writing Contest

Interested in any specific activity? I can provide more details!`,
        quickActions: [
            { text: "Join a Club", action: "join_club" },
            { text: "Leadership Roles", action: "leadership" },
            { text: "Upcoming Competitions", action: "competitions" }
        ]
    },
    career: {
        title: "💼 Career Services",
        response: `Your career success is our priority. Here's what we offer:

**Career Development Services:**
• **Resume Review** - Get personalized feedback from career coaches
• **Mock Interviews** - Practice with industry professionals
• **Career Counseling** - One-on-one guidance sessions
• **Job Portal** - Exclusive access to 500+ employer partners

**Upcoming Events:**
- Tech Industry Panel (Next Tuesday, 6 PM EST)
- Resume Workshop (Thursday, 4 PM EST)
- Virtual Career Fair (October 15-16)

**Internship Programs:**
We partner with companies like Google, Amazon, Microsoft, and local startups for semester-long internships.

**Alumni Network:**
Connect with 50,000+ alumni for mentorship and networking.

Ready to boost your career prospects?`,
        quickActions: [
            { text: "Book Career Coaching", action: "coaching" },
            { text: "View Job Postings", action: "jobs" },
            { text: "Register for Career Fair", action: "career_fair" }
        ]
    },
    wellbeing: {
        title: "❤️ Wellbeing Resources",
        response: `Your wellbeing matters. Here are our support services:

**24/7 Support Services:**
• **Counseling Center** - Free confidential sessions with licensed therapists
• **Crisis Hotline** - Immediate support: 1-800-MIU-HELP
• **Wellness Workshops** - Mindfulness, stress management, sleep hygiene
• **Peer Support** - Connect with trained student volunteers

**Health & Wellness:**
- Virtual Fitness Classes (Yoga, HIIT, Meditation)
- Nutrition Counseling
- Mental Health First Aid Training
- Substance Abuse Prevention Programs

**Accessibility Services:**
We provide accommodations for students with disabilities, including:
- Extended test times
- Note-taking assistance
- Accessible digital materials

**Emergency Resources:**
If you're experiencing a crisis, please contact our 24/7 support line immediately.

Remember: Your mental health is just as important as your academic success.`,
        quickActions: [
            { text: "Schedule Counseling", action: "counseling" },
            { text: "Wellness Workshops", action: "wellness" },
            { text: "Accessibility Services", action: "accessibility" }
        ]
    }
};

// Initialize Chatbot
document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const quickMenu = document.getElementById('quickMenu');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatbotMinimize = document.getElementById('chatbotMinimize');
    const chatInput = document.getElementById('chatInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const quickActions = document.querySelectorAll('.quick-action, .quick-topic');
    const openFullChat = document.getElementById('openFullChat');
    const voiceInput = document.getElementById('voiceInput');
    const charCount = document.getElementById('charCount');
    const notificationBadge = document.getElementById('notificationBadge');

    // Toggle Chatbot Window
    chatbotToggle.addEventListener('click', function () {
        if (!chatbotState.isOpen) {
            openChatbot();
        } else if (chatbotState.isMinimized) {
            openChatbot();
        } else {
            minimizeChatbot();
        }
    });

    // Open Chatbot
    function openChatbot() {
        chatbotState.isOpen = true;
        chatbotState.isMinimized = false;
        chatbotWindow.classList.remove('hidden');
        quickMenu.classList.add('hidden');
        chatbotWindow.classList.add('chatbot-enter');

        // Hide notification badge
        notificationBadge.classList.add('hidden');

        // Focus input
        setTimeout(() => {
            chatInput.focus();
        }, 300);

        // Update icon
        document.getElementById('chatbotIcon').textContent = '💬';
    }

    // Minimize Chatbot
    function minimizeChatbot() {
        chatbotState.isMinimized = true;
        chatbotWindow.classList.add('hidden');
        quickMenu.classList.remove('hidden');
        quickMenu.classList.add('chatbot-enter');
    }

    // Close Chatbot
    chatbotClose.addEventListener('click', function () {
        chatbotState.isOpen = false;
        chatbotState.isMinimized = false;
        chatbotWindow.classList.add('hidden');
        quickMenu.classList.add('hidden');
        document.getElementById('chatbotIcon').textContent = '💬';
    });

    // Minimize button
    chatbotMinimize.addEventListener('click', minimizeChatbot);

    // Open full chat from quick menu
    openFullChat.addEventListener('click', openChatbot);

    // Character counter
    chatInput.addEventListener('input', function () {
        charCount.textContent = `${this.value.length}/500`;
        if (this.value.length > 450) {
            charCount.classList.add('text-red-500');
        } else {
            charCount.classList.remove('text-red-500');
        }
    });

    // Send message function
    function sendUserMessage() {
        const message = chatInput.value.trim();
        if (message === '') return;

        // Add user message to chat
        addMessageToChat(message, 'user');

        // Clear input
        chatInput.value = '';
        charCount.textContent = '0/500';

        // Show typing indicator
        typingIndicator.classList.remove('hidden');

        // Simulate API call to backend/LLM
        setTimeout(() => {
            typingIndicator.classList.add('hidden');
            const response = getBotResponse(message);
            addMessageToChat(response.text, 'bot', response.quickActions);

            // Auto-scroll to bottom
            scrollToBottom();
        }, 1500);
    }

    // Send message on button click
    sendMessage.addEventListener('click', sendUserMessage);

    // Send message on Enter key (but allow Shift+Enter for new line)
    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendUserMessage();
        }
    });

    // Quick action buttons
    quickActions.forEach(button => {
        button.addEventListener('click', function () {
            const action = this.getAttribute('data-action');
            handleQuickAction(action);
        });
    });

    // Handle quick actions
    function handleQuickAction(action) {
        if (topicResponses[action]) {
            const topic = topicResponses[action];
            addMessageToChat(`Tell me about ${topic.title.toLowerCase()}`, 'user');

            // Show typing indicator
            typingIndicator.classList.remove('hidden');

            setTimeout(() => {
                typingIndicator.classList.add('hidden');
                addMessageToChat(topic.response, 'bot', topic.quickActions);
                scrollToBottom();
            }, 1000);
        }
    }

    // Add message to chat
    function addMessageToChat(text, sender, quickActions = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (sender === 'user') {
            messageDiv.innerHTML = `
        <div class="flex items-start justify-end space-x-2">
          <div class="text-right">
            <div class="message-content inline-block px-4 py-3 rounded-2xl rounded-br-none bg-gradient-miu text-white max-w-[80%]">
              <p>${escapeHtml(text)}</p>
            </div>
            <div class="text-xs text-gray-500 mt-1 mr-1">${timestamp}</div>
          </div>
          <div class="w-8 h-8 bg-gradient-to-r from-miu-accent to-yellow-400 rounded-full flex items-center justify-center text-miu-primary font-bold text-sm">
            You
          </div>
        </div>
      `;
        } else {
            messageDiv.innerHTML = `
        <div class="flex items-start space-x-2">
          <div class="w-8 h-8 bg-gradient-to-r from-miu-primary to-miu-secondary rounded-full flex items-center justify-center text-white text-sm">
            AI
          </div>
          <div>
            <div class="message-content bg-gray-100 rounded-2xl rounded-tl-none p-4 max-w-[80%]">
              ${formatBotResponse(text)}
            </div>
            ${quickActions ? `
              <div class="mt-3 flex flex-wrap gap-2">
                ${quickActions.map(action => `
                  <button class="quick-followup bg-white border border-gray-300 hover:border-miu-secondary text-gray-700 hover:text-miu-secondary px-3 py-2 rounded-lg text-sm transition-colors" data-action="${action.action}">
                    ${action.text}
                  </button>
                `).join('')}
              </div>
            ` : ''}
            <div class="text-xs text-gray-500 mt-1 ml-1">${timestamp}</div>
          </div>
        </div>
      `;

            // Add event listeners to follow-up buttons
            if (quickActions) {
                setTimeout(() => {
                    const followupButtons = messageDiv.querySelectorAll('.quick-followup');
                    followupButtons.forEach(button => {
                        button.addEventListener('click', function () {
                            const action = this.getAttribute('data-action');
                            handleFollowUpAction(action);
                        });
                    });
                }, 100);
            }
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();

        // Add to conversation history
        chatbotState.conversationHistory.push({
            sender,
            text,
            timestamp: new Date().toISOString()
        });
    }

    // Format bot response with markdown-like syntax
    function formatBotResponse(text) {
        // Convert **bold** to <strong>
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Convert *italic* to <em>
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Convert lists
        text = text.replace(/^•\s+(.*)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

        // Convert line breaks
        text = text.replace(/\n\n/g, '<br><br>');

        // Convert URLs to links
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="text-miu-secondary hover:underline">$1</a>');

        return text;
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Handle follow-up actions
    function handleFollowUpAction(action) {
        const responses = {
            tutoring: "I'll help you schedule a tutoring session. What subject do you need help with?",
            study_groups: "Great! I can connect you with study groups. Which course are you taking?",
            workshops: "Here are the upcoming workshops...",
            discord: "Join our Discord server: https://discord.gg/miu",
            clubs: "View our club directory: https://miu.edu/clubs",
            events: "Check out upcoming events: https://miu.edu/events",
            join_club: "Which type of club are you interested in?",
            leadership: "Here are available leadership positions...",
            competitions: "Upcoming competitions include...",
            coaching: "Book career coaching: https://miu.edu/career/coaching",
            jobs: "View job postings: https://miu.edu/career/jobs",
            career_fair: "Register for career fair: https://miu.edu/career/fair",
            counseling: "Schedule counseling: https://miu.edu/wellbeing/counseling",
            wellness: "Wellness workshops: https://miu.edu/wellbeing/workshops",
            accessibility: "Accessibility services: https://miu.edu/accessibility"
        };

        if (responses[action]) {
            addMessageToChat(responses[action], 'bot');
            scrollToBottom();
        }
    }

    // Get bot response (simulated - in production, this would call your LLM API)
    function getBotResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();

        // Check for specific topics
        if (lowerMessage.includes('academic') || lowerMessage.includes('tutor') || lowerMessage.includes('study')) {
            return {
                text: topicResponses.academic.response,
                quickActions: topicResponses.academic.quickActions
            };
        } else if (lowerMessage.includes('community') || lowerMessage.includes('social') || lowerMessage.includes('friend')) {
            return {
                text: topicResponses.community.response,
                quickActions: topicResponses.community.quickActions
            };
        } else if (lowerMessage.includes('activity') || lowerMessage.includes('club') || lowerMessage.includes('extracurricular')) {
            return {
                text: topicResponses.activities.response,
                quickActions: topicResponses.activities.quickActions
            };
        } else if (lowerMessage.includes('career') || lowerMessage.includes('job') || lowerMessage.includes('intern')) {
            return {
                text: topicResponses.career.response,
                quickActions: topicResponses.career.quickActions
            };
        } else if (lowerMessage.includes('wellbeing') || lowerMessage.includes('health') || lowerMessage.includes('mental')) {
            return {
                text: topicResponses.wellbeing.response,
                quickActions: topicResponses.wellbeing.quickActions
            };
        }

        // Default response
        return {
            text: `I understand you're asking about "${userMessage}". As your Student Life Assistant, I can help you with:\n\n1. **Academic Support** - Tutoring, workshops, study groups\n2. **Virtual Community** - Clubs, events, social connections\n3. **Career Services** - Internships, job search, resume help\n4. **Wellbeing Resources** - Counseling, health services, support\n\nWhat specific area would you like to explore?`,
            quickActions: [
                { text: "Academic Support", action: "academic" },
                { text: "Virtual Community", action: "community" },
                { text: "Career Services", action: "career" }
            ]
        };
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Voice input simulation
    voiceInput.addEventListener('click', function () {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();

            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.start();

            recognition.onresult = function (event) {
                const transcript = event.results[0][0].transcript;
                chatInput.value = transcript;
                charCount.textContent = `${transcript.length}/500`;
            };

            recognition.onspeechend = function () {
                recognition.stop();
            };

            recognition.onerror = function (event) {
                console.error('Speech recognition error', event.error);
            };
        } else {
            alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
        }
    });

    // Simulate new message notification
    function simulateNotification() {
        if (!chatbotState.isOpen) {
            notificationBadge.classList.remove('hidden');
            document.getElementById('chatbotIcon').textContent = '🔔';

            // Add welcome back message when opened
            setTimeout(() => {
                if (!chatbotState.conversationHistory.some(msg =>
                    msg.text.includes('Welcome back') && msg.sender === 'bot')) {
                    const welcomeBackMessage = "Welcome back! While you were away:\n\n• 3 new study groups formed\n• Career fair registration opened\n• New wellness workshop scheduled\n\nHow can I help you today?";
                    addMessageToChat(welcomeBackMessage, 'bot');
                }
            }, 1000);
        }
    }

    // Simulate initial notifications after page load
    setTimeout(simulateNotification, 10000);

    // API Integration Functions (for connecting to your backend/LLM)
    window.chatbotAPI = {
        // Send message to your LLM backend
        async sendToLLM(message, context = {}) {
            // This is where you would integrate with your actual LLM API
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message,
                    context: {
                        ...context,
                        conversationHistory: chatbotState.conversationHistory.slice(-10), // Send last 10 messages
                        userPreferences: chatbotState.userPreferences,
                        currentTopic: chatbotState.currentTopic
                    }
                })
            });

            return await response.json();
        },

        // Update user preferences
        updatePreferences(preferences) {
            chatbotState.userPreferences = { ...chatbotState.userPreferences, ...preferences };
            localStorage.setItem('miuChatbotPreferences', JSON.stringify(chatbotState.userPreferences));
        },

        // Get chatbot state
        getState() {
            return { ...chatbotState };
        },

        // Clear conversation
        clearConversation() {
            chatbotState.conversationHistory = [];
            chatMessages.innerHTML = `
        <div class="chat-message bot-message">
          <div class="flex items-start space-x-2">
            <div class="w-8 h-8 bg-gradient-to-r from-miu-primary to-miu-secondary rounded-full flex items-center justify-center text-white text-sm">
              AI
            </div>
            <div>
              <div class="bg-gray-100 rounded-2xl rounded-tl-none p-4 max-w-[80%]">
                <p class="text-gray-800">👋 Welcome to MIU Student Life Assistant! I'm here to help you explore campus life, academic support, extracurricular activities, career services, and wellbeing resources. How can I assist you today?</p>
              </div>
            </div>
          </div>
        </div>
      `;
        }
    };

    // Load saved preferences
    const savedPreferences = localStorage.getItem('miuChatbotPreferences');
    if (savedPreferences) {
        chatbotState.userPreferences = JSON.parse(savedPreferences);
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatInput = document.getElementById('chatInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');

    // 1. Toggle Chatbot Visibility
    chatbotToggle.addEventListener('click', () => {
        const isHidden = chatbotWindow.classList.contains('hidden');
        if (isHidden) {
            chatbotWindow.classList.remove('hidden');
            chatbotWindow.classList.add('chatbot-enter');
        } else {
            chatbotWindow.classList.add('hidden');
        }
    });

    chatbotClose.onclick = () => chatbotWindow.classList.add('hidden');

    // 2. Handle Sending Message
    function handleSend() {
        const text = chatInput.value.trim();
        if (text) {
            addMessage(text, 'user');
            chatInput.value = '';
            simulateBotReply(text);
        }
    }

    sendMessage.onclick = handleSend;
    chatInput.onkeypress = (e) => { if (e.key === 'Enter') handleSend(); };

    // 3. Add Message to UI
    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${sender}-message flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const contentClass = sender === 'user' 
            ? 'bg-gradient-to-r from-[#0F2A44] to-[#1D4ED8] text-white rounded-br-none' 
            : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none shadow-sm';

        msgDiv.innerHTML = `
            <div class="max-w-[85%] p-3 rounded-2xl text-sm ${contentClass}">
                ${text}
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 4. Simulated Dummy Bot Logic
    function simulateBotReply(userText) {
        typingIndicator.classList.remove('hidden');
        chatMessages.scrollTop = chatMessages.scrollHeight;

        setTimeout(() => {
            typingIndicator.classList.add('hidden');
            let response = "I'm not sure how to help with that specifically, but I can guide you to Academic Support or Career Services!";
            
            const lower = userText.toLowerCase();
            if (lower.includes('academic')) response = "Our Academic Support includes 24/7 online tutoring and writing assistance.";
            if (lower.includes('career')) response = "Career Services offers resume reviews and mock interviews for all MIU students.";
            if (lower.includes('hi') || lower.includes('hello')) response = "Hello! How can I assist you with student life today?";

            addMessage(response, 'bot');
        }, 1500);
    }
});