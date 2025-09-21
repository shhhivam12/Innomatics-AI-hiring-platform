// Main JavaScript for Hiring Portal

// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navbarToggle = document.getElementById('navbar-toggle');
    const navbarNav = document.getElementById('navbar-nav');
    
    if (navbarToggle && navbarNav) {
        navbarToggle.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
            
            // Update toggle button icon
            const isActive = navbarNav.classList.contains('active');
            navbarToggle.innerHTML = isActive ? '✕' : '☰';
        });
        
        // Close mobile menu when clicking on a link
        const navLinks = navbarNav.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navbarNav.classList.remove('active');
                navbarToggle.innerHTML = '☰';
            });
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navbarToggle.contains(event.target) && !navbarNav.contains(event.target)) {
                navbarNav.classList.remove('active');
                navbarToggle.innerHTML = '☰';
            }
        });
    }
    
    // Initialize portal toggle
    initializePortalToggle();
});

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    // Clear previous error messages
    form.querySelectorAll('.form-error').forEach(error => error.remove());
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            // Email validation
            if (field.type === 'email' && !isValidEmail(field.value)) {
                showFieldError(field, 'Please enter a valid email address');
                isValid = false;
            }
            
            // Phone validation
            if (field.type === 'tel' && !isValidPhone(field.value)) {
                showFieldError(field, 'Please enter a valid phone number');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
    field.style.borderColor = 'var(--primary-color)';
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

// File Upload Handling
function handleFileUpload(input, callback) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const maxSize = 5 * 1024 * 1024; // 5MB
        
        if (file.size > maxSize) {
            alert('File size must be less than 5MB');
            return;
        }
        
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            alert('Please upload a PDF or Word document');
            return;
        }
        
        if (callback) {
            callback(file);
        }
    }
}

// Loading States
function showLoading(element) {
    if (element) {
        element.innerHTML = '<span class="loading"></span> Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

// Alert Messages
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Insert at the top of the main content
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Smooth Scrolling
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Portal Toggle Functionality
function switchPortal() {
    try {
        const toggle = document.getElementById('portal-toggle');
        if (!toggle) {
            console.error('Portal toggle element not found');
            return;
        }
        
        const isPlacement = toggle.checked;
        
        // Store the current portal preference
        try {
            localStorage.setItem('portalMode', isPlacement ? 'placement' : 'student');
        } catch (e) {
            console.warn('Could not save portal preference to localStorage:', e);
        }
        
        // Show loading state
        showAlert('Switching portal...', 'info');
        
        // Redirect to the appropriate portal
        if (isPlacement) {
            window.location.href = '/placement';
        } else {
            window.location.href = '/student';
        }
    } catch (error) {
        console.error('Error switching portal:', error);
        showAlert('Error switching portal. Please try again.', 'error');
    }
}

// Initialize portal toggle based on current page
function initializePortalToggle() {
    try {
        const toggle = document.getElementById('portal-toggle');
        if (!toggle) {
            console.warn('Portal toggle element not found');
            return;
        }
        
        const currentPath = window.location.pathname;
        const isPlacementPage = currentPath.includes('/placement');
        
        // Set toggle state based on current page
        toggle.checked = isPlacementPage;
        
        // Also check localStorage for user preference
        try {
            const savedMode = localStorage.getItem('portalMode');
            if (savedMode && savedMode !== (isPlacementPage ? 'placement' : 'student')) {
                toggle.checked = savedMode === 'placement';
            }
        } catch (e) {
            console.warn('Could not read portal preference from localStorage:', e);
        }
    } catch (error) {
        console.error('Error initializing portal toggle:', error);
    }
}

// Export functions for use in other scripts
window.HiringPortal = {
    validateForm,
    showAlert,
    showLoading,
    hideLoading,
    handleFileUpload,
    smoothScrollTo,
    debounce,
    throttle,
    switchPortal,
    initializePortalToggle
};
