# Frontend Update Plan - Flight Compensation Claim App

## Overview

This document outlines the plan to update the frontend to work seamlessly with the new FastAPI backend that implements the OpenAPI specification exactly.

## Current Frontend Issues

1. **Monolithic API Calls**: Frontend expects single `/api/claims/submit` endpoint
2. **Missing Authentication**: No JWT token handling
3. **Incompatible Data Formats**: Some field names don't match OpenAPI spec
4. **No File Upload Integration**: File handling needs to be updated
5. **Missing Error Handling**: Need proper API error handling

## Required Changes

### 1. Authentication System

**Current**: Simple email + ticket number validation
**New**: JWT-based authentication with proper token management

```javascript
// Add to FlightClaimApp class
class FlightClaimApp {
    constructor() {
        // ... existing code ...
        this.accessToken = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
    }

    // Add authentication methods
    async login(email, ticketNumber) {
        try {
            const response = await fetch('/api/auth/login-json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    bookingReference: ticketNumber
                })
            });

            if (!response.ok) {
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            this.accessToken = data.access_token;
            this.tokenExpiry = new Date().getTime() + (30 * 60 * 1000); // 30 minutes
            
            return { success: true };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async refreshToken() {
        if (!this.accessToken) return false;
        
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`
                }
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            this.accessToken = data.access_token;
            this.tokenExpiry = new Date().getTime() + (30 * 60 * 1000);
            
            return true;
        } catch (error) {
            this.logout();
            return false;
        }
    }

    isTokenExpired() {
        if (!this.tokenExpiry) return true;
        return new Date().getTime() >= this.tokenExpiry;
    }

    async ensureValidToken() {
        if (this.isTokenExpired()) {
            return await this.refreshToken();
        }
        return true;
    }

    logout() {
        this.accessToken = null;
        this.refreshToken = null;
        this.tokenExpiry = null;
        this.currentUser = null;
        this.isLoggedIn = false;
    }
}
```

### 2. API Call Updates

**Current**: Monolithic `apiCall()` method with hardcoded responses
**New**: Proper API integration with OpenAPI spec endpoints

```javascript
// Update apiCall method to use real API
async apiCall(endpoint, method = 'GET', data = null) {
    try {
        // Ensure valid token for authenticated endpoints
        if (this.isLoggedIn && !endpoint.includes('/auth/')) {
            await this.ensureValidToken();
        }

        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.accessToken && !endpoint.includes('/auth/')) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const config = {
            method: method,
            headers: headers,
        };

        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, config);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'API request failed');
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error on ${endpoint}:`, error);
        throw error;
    }
}

// Update submitClaim to use new API flow
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
        // Step 1: Submit flight details
        const flightDetails = {
            flightNumber: document.getElementById('flightNumber').value,
            plannedDepartureDate: document.getElementById('scheduledFlightDateTime').value.split('T')[0],
            actualDepartureTime: document.getElementById('actualFlightDateTime')?.value || null
        };

        await this.apiCall('/api/flight-details', 'POST', flightDetails);

        // Step 2: Submit personal information
        const personalInfo = {
            fullName: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            bookingReference: document.getElementById('ticketNumber').value
        };

        await this.apiCall('/api/personal-info', 'POST', personalInfo);

        // Step 3: Upload documents if any
        if (this.uploadedFiles.length > 0) {
            const formData = new FormData();
            
            // Add boarding pass (required)
            if (this.uploadedFiles.length > 0) {
                formData.append('boardingPass', this.uploadedFiles[0]);
            }
            
            // Add receipt if available
            if (this.uploadedFiles.length > 1) {
                formData.append('receipt', this.uploadedFiles[1]);
            }

            await this.apiCall('/api/upload', 'POST', formData);
        }

        // Clear draft and show success
        this.clearDraft();
        document.getElementById('claim-id').textContent = 'Claim submitted successfully';
        this.showView('success');

    } catch (error) {
        this.showError('claim-form', error.message || 'Failed to submit claim. Please try again.');
    } finally {
        this.setLoading(submitBtn, false);
    }
}
```

### 3. Login Form Updates

**Update login form to use new authentication endpoint:**

```javascript
// Update login method
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
        const result = await this.login(email, ticketNumber);
        
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
```

### 4. Claims Loading Updates

**Update claims loading to use new API endpoints:**

```javascript
// Update loadClaims method
async loadClaims() {
    if (!this.currentUser || !this.accessToken) return;

    try {
        // Get all user claims
        const result = await this.apiCall('/api/claims');
        
        if (result && Array.isArray(result)) {
            this.displayClaims(result);
        } else {
            this.displayClaims([]);
        }
    } catch (error) {
        console.error('Failed to load claims:', error);
        this.displayClaims([]);
    }
}

// Update showClaimDetails method
async showClaimDetails(claimId) {
    try {
        const result = await this.apiCall(`/api/claims/${claimId}`);
        
        if (result) {
            const content = document.getElementById('claim-details-content');
            
            content.innerHTML = `
                <div class="claim-details">
                    <div class="claim-info">
                        <h4>Claim #${result.claimId}</h4>
                        <div class="claim-status claim-status--${result.status.replace(' ', '-').toLowerCase()}">${this.formatStatus(result.status)}</div>
                        <p>Last updated: ${this.formatDate(result.lastUpdated)}</p>
                    </div>
                </div>
            `;
            
            this.showModal('claim-details-modal');
        }
    } catch (error) {
        console.error('Failed to load claim details:', error);
    }
}
```

### 5. Chat Functionality Updates

**Update chat to use new API endpoints:**

```javascript
// Update sendMessage method
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
```

### 6. File Upload Updates

**Update file upload to work with new API:**

```javascript
// Update handleFileUpload method
async handleFileUpload(event) {
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
```

## Implementation Steps

1. **Update Authentication Flow**
   - Replace current login with JWT-based authentication
   - Add token refresh mechanism
   - Update all API calls to include Bearer token

2. **Update API Integration**
   - Replace monolithic `apiCall` with proper endpoint calls
   - Implement step-by-step claim submission
   - Add proper error handling

3. **Update Data Models**
   - Ensure all field names match OpenAPI spec
   - Update form field mapping
   - Add proper data validation

4. **Update File Upload**
   - Integrate with new file upload endpoint
   - Add proper file validation
   - Handle multipart form data

5. **Update Error Handling**
   - Add comprehensive error handling
   - Display user-friendly error messages
   - Add retry mechanisms

6. **Testing**
   - Test all API endpoints
   - Test authentication flow
   - Test file upload functionality
   - Test error scenarios

## Benefits of New Implementation

1. **Better Architecture**: Clean separation of concerns
2. **Improved Security**: JWT authentication with proper token management
3. **Scalability**: Modular design allows for easy scaling
4. **Maintainability**: Well-structured code with proper error handling
5. **Performance**: Optimized API calls and data handling
6. **User Experience**: Better error messages and feedback

## Migration Timeline

1. **Phase 1**: Update authentication system (1-2 days)
2. **Phase 2**: Update claim submission flow (2-3 days)
3. **Phase 3**: Update file upload functionality (1-2 days)
4. **Phase 4**: Update chat functionality (1 day)
5. **Phase 5**: Testing and bug fixes (2-3 days)

Total estimated time: 7-11 days