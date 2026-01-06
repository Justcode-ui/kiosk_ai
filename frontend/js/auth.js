/**
 * KioskAI Authentication - Interactive JavaScript
 * Smooth animations and intelligent micro-interactions
 */

// ==================== CONFIGURATION ====================
// Determine API Base URL based on environment
let API_BASE_URL = '';

if (window.location.protocol === 'file:') {
    API_BASE_URL = 'http://127.0.0.1:8000';
} else if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {
    if (window.location.port === '8000') {
        API_BASE_URL = '';
    } else {
        API_BASE_URL = 'http://127.0.0.1:8000';
    }
} else {
    API_BASE_URL = '';
}

// ==================== PASSWORD VISIBILITY TOGGLE ====================
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;

    if (input.type === 'password') {
        input.type = 'text';
        button.classList.add('active');
    } else {
        input.type = 'password';
        button.classList.remove('active');
    }
}

// ==================== PASSWORD STRENGTH CHECKER ====================
function checkPasswordStrength(password) {
    let strength = 0;

    // Length check
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;

    // Character variety
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    return strength;
}

function updatePasswordStrength() {
    const passwordInput = document.getElementById('password');
    if (!passwordInput) return;

    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');

    if (!strengthFill || !strengthText) return;

    passwordInput.addEventListener('input', function () {
        const password = this.value;
        const strength = checkPasswordStrength(password);

        // Remove all classes
        strengthFill.className = 'strength-fill';

        if (password.length === 0) {
            strengthText.textContent = 'Enter a password';
            return;
        }

        if (strength <= 2) {
            strengthFill.classList.add('weak');
            strengthText.textContent = 'Weak password';
            strengthText.style.color = '#EF4444';
        } else if (strength <= 4) {
            strengthFill.classList.add('medium');
            strengthText.textContent = 'Medium password';
            strengthText.style.color = '#F59E0B';
        } else {
            strengthFill.classList.add('strong');
            strengthText.textContent = 'Strong password';
            strengthText.style.color = '#4CD7B4';
        }
    });
}

// ==================== INPUT FOCUS ANIMATIONS ====================
function initInputAnimations() {
    const inputs = document.querySelectorAll('.form-input');

    inputs.forEach(input => {
        // Add focus animation
        input.addEventListener('focus', function () {
            this.parentElement.style.transform = 'translateY(-2px)';
        });

        input.addEventListener('blur', function () {
            this.parentElement.style.transform = 'translateY(0)';
        });

        // Add typing animation to icon
        input.addEventListener('input', function () {
            const icon = this.parentElement.querySelector('.input-icon');
            if (icon) {
                icon.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    icon.style.transform = 'scale(1)';
                }, 200);
            }
        });
    });
}

// ==================== FORM VALIDATION ====================
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showError(input, message) {
    input.classList.add('error');

    // Remove existing error message
    const existingError = input.parentElement.parentElement.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }

    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="2"/>
            <path d="M8 4V8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="8" cy="11" r="1" fill="currentColor"/>
        </svg>
        <span>${message}</span>
    `;
    input.parentElement.parentElement.appendChild(errorDiv);
}

function clearError(input) {
    input.classList.remove('error');
    const errorMessage = input.parentElement.parentElement.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

// ==================== SIGNUP FORM HANDLER ====================
function initSignupForm() {
    const form = document.getElementById('signupForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Get form data
        const fullName = document.getElementById('fullName');
        const email = document.getElementById('email');
        const businessName = document.getElementById('businessName');
        const password = document.getElementById('password');
        const submitBtn = form.querySelector('.btn-auth-primary');

        // Clear previous errors
        [fullName, email, businessName, password].forEach(clearError);

        // Validate
        let isValid = true;

        if (fullName.value.trim().length < 2) {
            showError(fullName, 'Please enter your full name');
            isValid = false;
        }

        if (!validateEmail(email.value)) {
            showError(email, 'Please enter a valid email address');
            isValid = false;
        }

        if (businessName.value.trim().length < 2) {
            showError(businessName, 'Please enter your business name');
            isValid = false;
        }

        if (password.value.length < 8) {
            showError(password, 'Password must be at least 8 characters');
            isValid = false;
        }

        if (!isValid) return;

        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        try {
            // Call actual API
            // Call actual API
            const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    business_name: businessName.value,
                    email: email.value,
                    phone_number: '',
                    password: password.value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            console.log('✅ Signup successful');
            alert('Account created successfully! Please log in.');
            window.location.href = 'login.html';

        } catch (error) {
            console.error('❌ Signup error:', error);
            showError(email, error.message || 'Registration failed');
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });
}

// ==================== LOGIN FORM HANDLER ====================
function initLoginForm() {
    const form = document.getElementById('loginForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Get form data
        const email = document.getElementById('email');
        const password = document.getElementById('password');
        const submitBtn = form.querySelector('.btn-auth-primary');

        // Clear previous errors
        [email, password].forEach(clearError);

        // Validate
        let isValid = true;

        if (!validateEmail(email.value)) {
            showError(email, 'Please enter a valid email address');
            isValid = false;
        }

        if (password.value.length < 1) {
            showError(password, 'Please enter your password');
            isValid = false;
        }

        if (!isValid) return;

        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        try {
            // Call actual API
            // Call actual API
            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email.value,
                    password: password.value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            console.log('✅ Login successful');

            // Store auth token
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);

            // Redirect to dashboard
            window.location.href = 'index.html';

        } catch (error) {
            console.error('❌ Login error:', error);
            showError(email, error.message || 'Invalid email or password');
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    });
}

// ==================== SMOOTH PAGE TRANSITIONS ====================
function initPageTransitions() {
    // Fade in on load
    document.body.style.opacity = '0';

    window.addEventListener('load', () => {
        setTimeout(() => {
            document.body.style.transition = 'opacity 0.5s ease-out';
            document.body.style.opacity = '1';
        }, 100);
    });

    // Fade out on navigation
    const links = document.querySelectorAll('a[href]');
    links.forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');

            // Only for internal links
            if (href && !href.startsWith('#') && !href.startsWith('http')) {
                e.preventDefault();

                document.body.style.transition = 'opacity 0.3s ease-out';
                document.body.style.opacity = '0';

                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });
}

// ==================== FLOATING ORB INTERACTIONS ====================
function initOrbInteractions() {
    const orbs = document.querySelectorAll('.floating-orb');

    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;

        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 0.5;
            const x = (mouseX - 0.5) * speed * 50;
            const y = (mouseY - 0.5) * speed * 50;

            orb.style.transform = `translate(${x}px, ${y}px)`;
        });
    });
}

// ==================== CARD TILT EFFECT ====================
function initCardTilt() {
    const card = document.querySelector('.auth-card');
    if (!card) return;

    card.addEventListener('mousemove', function (e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = (y - centerY) / 30;
        const rotateY = (centerX - x) / 30;

        this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
    });

    card.addEventListener('mouseleave', function () {
        this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
    });
}

// ==================== AUTO-FILL DETECTION ====================
function initAutoFillDetection() {
    const inputs = document.querySelectorAll('.form-input');

    inputs.forEach(input => {
        // Check for autofill
        const checkAutoFill = () => {
            if (input.matches(':-webkit-autofill')) {
                input.parentElement.querySelector('.input-icon')?.classList.add('filled');
            }
        };

        input.addEventListener('animationstart', checkAutoFill);
        setTimeout(checkAutoFill, 100);
    });
}

// ==================== INITIALIZE ALL ====================
function init() {
    console.log('🔐 KioskAI Auth Initialized');

    // Initialize all features
    updatePasswordStrength();
    initInputAnimations();
    initSignupForm();
    initLoginForm();
    initPageTransitions();
    initOrbInteractions();
    initCardTilt();
    initAutoFillDetection();

    console.log('✨ Auth page ready');
}

// ==================== DOM READY ====================
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// ==================== EXPORT FOR GLOBAL ACCESS ====================
window.togglePassword = togglePassword;
