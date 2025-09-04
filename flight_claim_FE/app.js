// Flight Compensation Claims Application
class FlightClaimApp {
    constructor() {
        this.currentView = 'home';
        this.currentStep = 1;
        this.maxStep = 4;
        this.isLoggedIn = false;
        this.currentUser = null;
        this.autoSaveTimer = null;
        this.chatSessionId = this.generateId();
        this.uploadedFiles = [];

        // Sample data from the specification
        this.sampleData = {
            airports: [
                {code: "LHR", name: "London Heathrow", city: "London"},
                {code: "CDG", name: "Paris Charles de Gaulle", city: "Paris"},
                {code: "FRA", name: "Frankfurt am Main", city: "Frankfurt"}, 
                {code: "AMS", name: "Amsterdam Schiphol", city: "Amsterdam"},
                {code: "BCN", name: "Barcelona El Prat", city: "Barcelona"},
                {code: "FCO", name: "Rome Fiumicino", city: "Rome"},
                {code: "MUC", name: "Munich", city: "Munich"},
                {code: "MAD", name: "Madrid Barajas", city: "Madrid"},
                {code: "DUS", name: "Düsseldorf", city: "Düsseldorf"},
                {code: "ZUR", name: "Zurich", city: "Zurich"}
            ],
            claims: [
                {
                    claimId: "CL001234",
                    status: "under review",
                    lastUpdated: "2025-09-01T10:30:00Z",
                    summary: "Flight LH1234 delayed 4 hours due to technical issues",
                    email: "test@example.com",
                    ticketNumber: "ABC123",
                    timeline: [
                        {date: "2025-08-30T14:00:00Z", event: "Claim submitted"},
                        {date: "2025-09-01T10:30:00Z", event: "Under review by legal team"}
                    ]
                },
                {
                    claimId: "CL001235", 
                    status: "resolved",
                    lastUpdated: "2025-08-28T16:45:00Z",
                    summary: "Flight BA456 cancelled, compensation of €400 approved",
                    email: "test@example.com",
                    ticketNumber: "ABC123",
                    timeline: [
                        {date: "2025-08-15T09:00:00Z", event: "Claim submitted"},
                        {date: "2025-08-20T11:00:00Z", event: "Documentation verified"},
                        {date: "2025-08-25T14:00:00Z", event: "Compensation approved"},
                        {date: "2025-08-28T16:45:00Z", event: "Payment processed"}
                    ]
                }
            ],
            chatResponses: {
                greeting: "Hello! I'm here to help you with your flight compensation claim. How can I assist you today?",
                compensation: "Under EU Regulation 261/2004, you may be entitled to compensation of €250-€600 depending on your flight distance and disruption type.",
                eligible: "You can claim compensation for delays over 3 hours, cancellations, denied boarding, or downgrades - unless caused by extraordinary circumstances.",
                timeframe: "You can submit a claim up to 3 years after your flight disruption occurred.",
                documents: "You'll need your boarding pass, booking confirmation, and any communication from the airline about the disruption."
            }
        };

        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.setupEventListeners();
        this.setupAutoSave();
        this.loadDraft();
        this.setupChatTimestamp();
        console.log('FlightClaimApp initialized');
    }

    setupEventListeners() {
        // Form navigation
        const nextBtn = document.getElementById('nextStep');
        const prevBtn = document.getElementById('prevStep');
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextStep());
        if (prevBtn) prevBtn.addEventListener('click', () => this.prevStep());
        
        // Form submission
        const claimForm = document.getElementById('claim-form');
        const loginForm = document.getElementById('login-form');
        if (claimForm) claimForm.addEventListener('submit', (e) => this.submitClaim(e));
        if (loginForm) loginForm.addEventListener('submit', (e) => this.login(e));
        
        // File upload
        const documentsInput = document.getElementById('documents');
        if (documentsInput) documentsInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Real-time validation
        this.setupFormValidation();
        
        // Chat input
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('input', (e) => {
                if (e.target.value.length > 1000) {
                    e.target.value = e.target.value.substring(0, 1000);
                }
            });
        }

        console.log('Event listeners set up');
    }

    setupFormValidation() {
        const form = document.getElementById('claim-form');
        if (!form) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearError(input));
        });
    }

    validateField(field) {
        const value = field.value.trim();
        const name = field.name;
        let isValid = true;
        let errorMessage = '';

        // Clear previous validation state
        field.classList.remove('error', 'success');
        
        switch (name) {
            case 'fullName':
                if (field.hasAttribute('required') && value.length < 2) {
                    isValid = false;
                    errorMessage = 'Full name must be at least 2 characters';
                }
                break;
                
            case 'email':
            case 'loginEmail':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (field.hasAttribute('required') && !emailRegex.test(value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
                break;
                
            case 'flightNumber':
                const flightRegex = /^[A-Z0-9]{2,6}$/i;
                if (field.hasAttribute('required') && !flightRegex.test(value)) {
                    isValid = false;
                    errorMessage = 'Flight number should be 2-6 alphanumeric characters (e.g., LH1234)';
                }
                break;
                
            case 'ticketNumber':
            case 'loginTicketNumber':
                if (field.hasAttribute('required') && value.length < 6) {
                    isValid = false;
                    errorMessage = 'Ticket number must be at least 6 characters';
                }
                break;
                
            case 'departureAirport':
            case 'arrivalAirport':
                const airportRegex = /^[A-Z]{3}$/;
                if (field.hasAttribute('required') && !airportRegex.test(value)) {
                    isValid = false;
                    errorMessage = 'Airport code must be 3 uppercase letters (e.g., LHR)';
                }
                break;
                
            case 'scheduledFlightDateTime':
                if (field.hasAttribute('required') && !value) {
                    isValid = false;
                    errorMessage = 'Scheduled flight date and time is required';
                }
                break;
                
            case 'disruptionType':
                if (field.hasAttribute('required') && !value) {
                    isValid = false;
                    errorMessage = 'Please select the type of disruption';
                }
                break;
        }

        // Check required fields
        if (field.hasAttribute('required') && !value && !errorMessage) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        this.showFieldError(field, isValid, errorMessage);
        return isValid;
    }

    showFieldError(field, isValid, errorMessage) {
        const errorElement = document.getElementById(`${field.id}-error`);
        
        if (isValid) {
            field.classList.add('success');
            field.classList.remove('error');
            if (errorElement) {
                errorElement.textContent = '';
                errorElement.classList.remove('show');
            }
        } else {
            field.classList.add('error');
            field.classList.remove('success');
            if (errorElement) {
                errorElement.textContent = errorMessage;
                errorElement.classList.add('show');
            }
        }
    }

    clearError(field) {
        field.classList.remove('error');
        const errorElement = document.getElementById(`${field.id}-error`);
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    validateStep(step) {
        const currentStepElement = document.querySelector(`[data-step="${step}"].form-step--active`);
        if (!currentStepElement) return true;

        const requiredFields = currentStepElement.querySelectorAll('[required]');
        let allValid = true;

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                allValid = false;
            }
        });

        return allValid;
    }

    nextStep() {
        if (!this.validateStep(this.currentStep)) {
            return;
        }

        if (this.currentStep < this.maxStep) {
            this.setStep(this.currentStep + 1);
        }
    }

    prevStep() {
        if (this.currentStep > 1) {
            this.setStep(this.currentStep - 1);
        }
    }

    setStep(step) {
        // Hide current step
        const currentStepElement = document.querySelector(`[data-step="${this.currentStep}"].form-step`);
        const currentProgressElement = document.querySelector(`[data-step="${this.currentStep}"].progress-step`);
        
        if (currentStepElement) currentStepElement.classList.remove('form-step--active');
        if (currentProgressElement) currentProgressElement.classList.remove('progress-step--active');

        // Mark completed steps
        if (step > this.currentStep && currentProgressElement) {
            currentProgressElement.classList.add('progress-step--completed');
        }

        this.currentStep = step;

        // Show new step
        const newStepElement = document.querySelector(`[data-step="${step}"].form-step`);
        const newProgressElement = document.querySelector(`[data-step="${step}"].progress-step`);
        
        if (newStepElement) newStepElement.classList.add('form-step--active');
        if (newProgressElement) newProgressElement.classList.add('progress-step--active');

        // Update navigation buttons
        this.updateNavigationButtons();
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevStep');
        const nextBtn = document.getElementById('nextStep');
        const submitBtn = document.getElementById('submitClaim');

        if (prevBtn) prevBtn.style.display = this.currentStep === 1 ? 'none' : 'block';
        if (nextBtn) nextBtn.style.display = this.currentStep === this.maxStep ? 'none' : 'block';
        if (submitBtn) submitBtn.style.display = this.currentStep === this.maxStep ? 'block' : 'none';
    }

    handleFileUpload(event) {
        const files = Array.from(event.target.files);
        const maxFiles = 5;
        const maxSize = 5 * 1024 * 1024; // 5MB
        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];

        let validFiles = [];
        let errors = [];

        files.forEach(file => {
            if (this.uploadedFiles.length + validFiles.length >= maxFiles) {
                errors.push(`Maximum ${maxFiles} files allowed`);
                return;
            }

            if (file.size > maxSize) {
                errors.push(`${file.name} is too large. Maximum size is 5MB`);
                return;
            }

            if (!allowedTypes.includes(file.type)) {
                errors.push(`${file.name} is not a supported file type`);
                return;
            }

            validFiles.push(file);
        });

        if (errors.length > 0) {
            this.showFieldError(event.target, false, errors[0]);
        } else {
            this.showFieldError(event.target, true, '');
        }

        // Add valid files to uploaded files
        this.uploadedFiles.push(...validFiles);
        this.displayUploadedFiles();
        
        // Reset input
        event.target.value = '';
    }

    displayUploadedFiles() {
        const container = document.querySelector('.uploaded-files');
        if (!container) return;

        container.innerHTML = '';
        
        this.uploadedFiles.forEach((file, index) => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'uploaded-file';
            fileDiv.innerHTML = `
                <span>${file.name} (${this.formatFileSize(file.size)})</span>
                <button type="button" onclick="app.removeFile(${index})" aria-label="Remove ${file.name}">&times;</button>
            `;
            container.appendChild(fileDiv);
        });
    }

    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.displayUploadedFiles();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    async submitClaim(event) {
        event.preventDefault();
        
        if (!this.validateStep(this.currentStep)) {
            return;
        }

        // Check required checkboxes
        const declaration = document.getElementById('declarationAccepted');
        const consent = document.getElementById('consentAccepted');
        
        if (!declaration?.checked) {
            this.showFieldError(declaration, false, 'You must accept the declaration to proceed');
            return;
        }
        
        if (!consent?.checked) {
            this.showFieldError(consent, false, 'You must accept the terms and privacy policy to proceed');
            return;
        }

        const submitBtn = document.getElementById('submitClaim');
        this.setLoading(submitBtn, true);

        try {
            const formData = this.getFormData();
            const result = await this.apiCall('/api/claims/submit', 'POST', formData);
            
            if (result.success) {
                this.clearDraft();
                document.getElementById('claim-id').textContent = result.claimId;
                this.showView('success');
            } else {
                throw new Error(result.message || 'Submission failed');
            }
        } catch (error) {
            this.showError('claim-form', error.message || 'Failed to submit claim. Please try again.');
        } finally {
            this.setLoading(submitBtn, false);
        }
    }

    getFormData() {
        const form = document.getElementById('claim-form');
        const formData = new FormData(form);
        const data = {};

        // Get form fields
        for (let [key, value] of formData.entries()) {
            if (key !== 'documents') {
                data[key] = value;
            }
        }

        // Add files
        data.documents = this.uploadedFiles.map(file => ({
            name: file.name,
            size: file.size,
            type: file.type
        }));

        // Convert datetime-local to ISO string
        if (data.scheduledFlightDateTime) {
            data.scheduledFlightDateTime = new Date(data.scheduledFlightDateTime).toISOString();
        }
        if (data.actualFlightDateTime) {
            data.actualFlightDateTime = new Date(data.actualFlightDateTime).toISOString();
        }

        // Convert checkboxes to boolean
        data.declarationAccepted = document.getElementById('declarationAccepted').checked;
        data.consentAccepted = document.getElementById('consentAccepted').checked;

        return data;
    }

    async login(event) {
        event.preventDefault();
        
        const email = document.getElementById('loginEmail').value;
        const ticketNumber = document.getElementById('loginTicketNumber').value;
        
        if (!this.validateField(document.getElementById('loginEmail')) || 
            !this.validateField(document.getElementById('loginTicketNumber'))) {
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        this.setLoading(submitBtn, true);

        try {
            const result = await this.apiCall('/api/auth/login', 'POST', { email, ticketNumber });
            
            if (result.success) {
                this.currentUser = { email, ticketNumber };
                this.isLoggedIn = true;
                this.updateUserInterface();
                this.showView('dashboard');
                await this.loadClaims();
            } else {
                throw new Error(result.message || 'Login failed');
            }
        } catch (error) {
            document.getElementById('login-error').textContent = error.message || 'Invalid credentials. Please try again.';
            document.getElementById('login-error').classList.add('show');
        } finally {
            this.setLoading(submitBtn, false);
        }
    }

    async loadClaims() {
        if (!this.currentUser) return;

        try {
            const result = await this.apiCall(`/api/claims/status?email=${this.currentUser.email}&ticketNumber=${this.currentUser.ticketNumber}`);
            
            if (result.success) {
                this.displayClaims(result.claims);
            }
        } catch (error) {
            console.error('Failed to load claims:', error);
        }
    }

    displayClaims(claims) {
        const container = document.getElementById('claims-list');
        if (!container) return;

        if (!claims || claims.length === 0) {
            container.innerHTML = `
                <div class="card">
                    <div class="card__body">
                        <p>No claims found. <a href="#" onclick="app.showView('claim-form')">Submit your first claim</a></p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = claims.map(claim => `
            <div class="claim-item" onclick="app.showClaimDetails('${claim.claimId}')">
                <div class="claim-header">
                    <div class="claim-id">Claim #${claim.claimId}</div>
                    <div class="claim-status claim-status--${claim.status.replace(' ', '-').toLowerCase()}">${this.formatStatus(claim.status)}</div>
                </div>
                <div class="claim-summary">${claim.summary}</div>
                <div class="claim-updated">Last updated: ${this.formatDate(claim.lastUpdated)}</div>
            </div>
        `).join('');
    }

    async showClaimDetails(claimId) {
        try {
            const result = await this.apiCall(`/api/claims/${claimId}/details`);
            
            if (result.success) {
                const claim = result.claim;
                const content = document.getElementById('claim-details-content');
                
                content.innerHTML = `
                    <div class="claim-details">
                        <div class="claim-info">
                            <h4>Claim #${claim.claimId}</h4>
                            <div class="claim-status claim-status--${claim.status.replace(' ', '-').toLowerCase()}">${this.formatStatus(claim.status)}</div>
                            <p>${claim.summary}</p>
                        </div>
                        
                        <div class="claim-timeline">
                            <h4>Timeline</h4>
                            <div class="timeline">
                                ${claim.timeline.map(event => `
                                    <div class="timeline-item">
                                        <div class="timeline-date">${this.formatDate(event.date)}</div>
                                        <div class="timeline-event">${event.event}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
                
                this.showModal('claim-details-modal');
            }
        } catch (error) {
            console.error('Failed to load claim details:', error);
        }
    }

    logout() {
        this.currentUser = null;
        this.isLoggedIn = false;
        this.updateUserInterface();
        this.showView('home');
    }

    updateUserInterface() {
        const userStatus = document.querySelector('.user-status');
        const nav = document.querySelector('.nav');
        
        if (this.isLoggedIn && this.currentUser) {
            if (nav) nav.style.display = 'none';
            if (userStatus) {
                userStatus.classList.remove('hidden');
                const userEmailElement = userStatus.querySelector('.user-email');
                if (userEmailElement) userEmailElement.textContent = this.currentUser.email;
            }
            
            const emailDisplay = document.querySelector('.user-email-display');
            if (emailDisplay) {
                emailDisplay.textContent = this.currentUser.email;
            }
        } else {
            if (nav) nav.style.display = 'flex';
            if (userStatus) userStatus.classList.add('hidden');
        }
    }

    showView(viewId) {
        console.log('Showing view:', viewId);
        
        // Hide all views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('view--active');
        });
        
        // Show target view
        const targetView = document.getElementById(`${viewId}-view`);
        if (targetView) {
            targetView.classList.add('view--active');
            this.currentView = viewId;
        } else {
            console.error('View not found:', `${viewId}-view`);
        }
        
        // Reset form if switching to claim form
        if (viewId === 'claim-form') {
            this.setStep(1);
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    // Chat functionality
    toggleChat() {
        const chatWindow = document.querySelector('.chatbot-window');
        if (chatWindow) {
            chatWindow.classList.toggle('hidden');
        }
    }

    handleChatKeyPress(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            this.sendMessage();
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message
        this.addChatMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const result = await this.apiCall('/api/chat/send', 'POST', {
                sessionId: this.chatSessionId,
                message: message
            });
            
            this.hideTypingIndicator();
            
            if (result.success) {
                this.addChatMessage(result.reply, 'bot');
            } else {
                this.addChatMessage('I apologize, but I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addChatMessage('I apologize, but I encountered an error. Please try again.', 'bot');
        }
    }

    addChatMessage(content, sender) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message--${sender}`;
        
        const now = new Date();
        const timestamp = now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit'
        });
        
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message message--bot typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">Typing...</div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typing = document.querySelector('.typing-indicator');
        if (typing) {
            typing.remove();
        }
    }

    setupChatTimestamp() {
        const timestamp = document.querySelector('.chatbot-messages .message-timestamp');
        if (timestamp && !timestamp.textContent) {
            const now = new Date();
            timestamp.textContent = now.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit'
            });
        }
    }

    // Auto-save functionality
    setupAutoSave() {
        this.autoSaveTimer = setInterval(() => {
            this.saveDraft();
        }, 30000); // 30 seconds
    }

    saveDraft() {
        if (this.currentView !== 'claim-form') return;
        
        try {
            const formData = {};
            const form = document.getElementById('claim-form');
            if (!form) return;
            
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.type === 'checkbox') {
                    formData[input.name] = input.checked;
                } else if (input.type !== 'file') {
                    formData[input.name] = input.value;
                }
            });
            
            formData.currentStep = this.currentStep;
            formData.timestamp = Date.now();
            
            localStorage.setItem('claimDraft', JSON.stringify(formData));
            this.showAutoSaveStatus('saved');
        } catch (error) {
            console.error('Failed to save draft:', error);
        }
    }

    loadDraft() {
        try {
            const draft = localStorage.getItem('claimDraft');
            if (!draft) return;
            
            const formData = JSON.parse(draft);
            const form = document.getElementById('claim-form');
            if (!form) return;
            
            // Check if draft is not too old (24 hours)
            const maxAge = 24 * 60 * 60 * 1000;
            if (Date.now() - formData.timestamp > maxAge) {
                this.clearDraft();
                return;
            }
            
            // Restore form data
            Object.keys(formData).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = formData[key];
                    } else if (input.type !== 'file') {
                        input.value = formData[key];
                    }
                }
            });
            
            if (formData.currentStep) {
                this.setStep(formData.currentStep);
            }
            
            this.showAutoSaveStatus('loaded');
        } catch (error) {
            console.error('Failed to load draft:', error);
        }
    }

    clearDraft() {
        try {
            localStorage.removeItem('claimDraft');
        } catch (error) {
            console.error('Failed to clear draft:', error);
        }
    }

    showAutoSaveStatus(type) {
        const indicator = document.querySelector('.auto-save-indicator');
        if (!indicator) return;
        
        switch (type) {
            case 'saved':
                indicator.textContent = 'Draft saved automatically';
                indicator.className = 'auto-save-indicator auto-save-indicator--saved';
                break;
            case 'loaded':
                indicator.textContent = 'Draft loaded from previous session';
                indicator.className = 'auto-save-indicator auto-save-indicator--saved';
                setTimeout(() => {
                    indicator.textContent = 'Auto-saving draft...';
                    indicator.className = 'auto-save-indicator';
                }, 3000);
                break;
            default:
                indicator.textContent = 'Auto-saving draft...';
                indicator.className = 'auto-save-indicator';
        }
    }

    // API simulation
    async apiCall(endpoint, method = 'GET', data = null) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
        
        // Simulate API responses
        if (endpoint === '/api/claims/submit' && method === 'POST') {
            return {
                success: true,
                claimId: 'CL' + Date.now().toString().slice(-6),
                message: 'Claim submitted successfully'
            };
        }
        
        if (endpoint === '/api/auth/login' && method === 'POST') {
            // Check against sample data
            const validLogin = data.email === 'test@example.com' && data.ticketNumber === 'ABC123';
            return {
                success: validLogin,
                message: validLogin ? 'Login successful' : 'Invalid email or ticket number'
            };
        }
        
        if (endpoint.includes('/api/claims/status')) {
            return {
                success: true,
                claims: this.sampleData.claims
            };
        }
        
        if (endpoint.includes('/api/claims/') && endpoint.includes('/details')) {
            const claimId = endpoint.split('/')[3];
            const claim = this.sampleData.claims.find(c => c.claimId === claimId);
            return {
                success: !!claim,
                claim: claim
            };
        }
        
        if (endpoint === '/api/chat/send' && method === 'POST') {
            const message = data.message.toLowerCase();
            let reply = this.sampleData.chatResponses.greeting;
            
            if (message.includes('compensation') || message.includes('money') || message.includes('amount')) {
                reply = this.sampleData.chatResponses.compensation;
            } else if (message.includes('eligible') || message.includes('qualify')) {
                reply = this.sampleData.chatResponses.eligible;
            } else if (message.includes('time') || message.includes('long')) {
                reply = this.sampleData.chatResponses.timeframe;
            } else if (message.includes('document') || message.includes('need') || message.includes('require')) {
                reply = this.sampleData.chatResponses.documents;
            }
            
            return {
                success: true,
                reply: reply,
                intent: 'general',
                confidence: 0.8
            };
        }
        
        return { success: false, message: 'Endpoint not found' };
    }

    // Utility functions
    setLoading(button, loading) {
        if (!button) return;
        
        const spinner = button.querySelector('.spinner');
        const text = button.querySelector('.btn-text');
        
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            if (spinner) spinner.classList.remove('hidden');
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            if (spinner) spinner.classList.add('hidden');
        }
    }

    showError(containerId, message) {
        const container = document.getElementById(containerId);
        let errorDiv = container.querySelector('.form-error');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message form-error show';
            container.appendChild(errorDiv);
        }
        
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
        
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }

    formatStatus(status) {
        return status.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    generateId() {
        return 'sess_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// Initialize the application
const app = new FlightClaimApp();

// Expose app globally for HTML onclick handlers
window.app = app;