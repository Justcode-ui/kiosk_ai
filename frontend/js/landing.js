/**
 * KioskAI Landing Page - Interactive JavaScript
 * Smooth animations, scroll effects, and intelligent interactions
 */

// ==================== UTILITY FUNCTIONS ====================
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

function isPartiallyInViewport(element, threshold = 0.2) {
    const rect = element.getBoundingClientRect();
    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
    const elementHeight = rect.height;
    const visibleHeight = Math.min(rect.bottom, windowHeight) - Math.max(rect.top, 0);
    return visibleHeight / elementHeight >= threshold;
}

// ==================== ANIMATED COUNTERS ====================
function animateCounter(element, target, duration = 2000, suffix = '%') {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// ==================== HERO STATS ANIMATION ====================
function initHeroStats() {
    const statNumbers = document.querySelectorAll('.stat-number');
    let animated = false;

    function checkAndAnimate() {
        if (animated) return;

        const firstStat = statNumbers[0];
        if (isPartiallyInViewport(firstStat, 0.5)) {
            statNumbers.forEach(stat => {
                const target = parseInt(stat.dataset.target);
                animateCounter(stat, target, 2000);
            });
            animated = true;
        }
    }

    window.addEventListener('scroll', checkAndAnimate);
    checkAndAnimate(); // Check on load
}

// ==================== IMPACT SECTION COUNTERS ====================
function initImpactCounters() {
    const impactNumbers = document.querySelectorAll('.impact-number');
    let animated = false;

    function checkAndAnimate() {
        if (animated) return;

        const firstImpact = impactNumbers[0];
        if (isPartiallyInViewport(firstImpact, 0.5)) {
            impactNumbers.forEach(number => {
                const target = parseInt(number.dataset.count);
                animateCounter(number, target, 2500);
            });
            animated = true;
        }
    }

    window.addEventListener('scroll', checkAndAnimate);
    checkAndAnimate();
}

// ==================== TIMELINE SCROLL ANIMATION ====================
function initTimeline() {
    const timelineItems = document.querySelectorAll('.timeline-item');

    function updateTimeline() {
        timelineItems.forEach((item, index) => {
            if (isPartiallyInViewport(item, 0.3)) {
                setTimeout(() => {
                    item.classList.add('active');
                }, index * 150);
            }
        });
    }

    window.addEventListener('scroll', updateTimeline);
    updateTimeline(); // Check on load
}

// ==================== NEURAL NETWORK ANIMATION ====================
function initNeuralNetwork() {
    const connections = document.querySelectorAll('.connection');
    const nodes = document.querySelectorAll('.node');

    let currentIndex = 0;
    const animationDelay = 300;

    function activateNext() {
        // Deactivate all
        connections.forEach(c => c.classList.remove('active'));
        nodes.forEach(n => n.classList.remove('active'));

        // Activate current
        if (connections[currentIndex]) {
            connections[currentIndex].classList.add('active');
        }
        if (nodes[currentIndex]) {
            nodes[currentIndex].classList.add('active');
        }

        currentIndex = (currentIndex + 1) % Math.max(connections.length, nodes.length);
    }

    // Start animation when in viewport
    function checkAndStart() {
        const network = document.querySelector('.neural-network');
        if (network && isPartiallyInViewport(network, 0.3)) {
            setInterval(activateNext, animationDelay);
            window.removeEventListener('scroll', checkAndStart);
        }
    }

    window.addEventListener('scroll', checkAndStart);
    checkAndStart();
}

// ==================== CHAT DEMO ANIMATION ====================
function initChatDemo() {
    const messages = document.querySelectorAll('.chat-message');
    const typingMessage = document.querySelector('.chat-message.typing');
    let currentMessageIndex = 0;
    let demoStarted = false;

    function showNextMessage() {
        if (currentMessageIndex >= messages.length) {
            // Restart demo after delay
            setTimeout(() => {
                messages.forEach(msg => msg.classList.add('hidden'));
                currentMessageIndex = 0;
                showNextMessage();
            }, 3000);
            return;
        }

        const message = messages[currentMessageIndex];

        // Handle typing indicator
        if (message.classList.contains('typing')) {
            message.classList.remove('hidden');
            setTimeout(() => {
                message.classList.add('hidden');
                currentMessageIndex++;
                showNextMessage();
            }, 1500);
        } else {
            message.classList.remove('hidden');
            currentMessageIndex++;
            setTimeout(showNextMessage, message.classList.contains('ai') ? 2000 : 1500);
        }
    }

    function checkAndStart() {
        if (demoStarted) return;

        const chatDemo = document.querySelector('.chat-demo');
        if (chatDemo && isPartiallyInViewport(chatDemo, 0.4)) {
            demoStarted = true;
            // Hide all messages initially except first customer message
            messages.forEach((msg, index) => {
                if (index > 0) msg.classList.add('hidden');
            });

            setTimeout(() => {
                currentMessageIndex = 1; // Start from typing indicator
                showNextMessage();
            }, 1000);

            window.removeEventListener('scroll', checkAndStart);
        }
    }

    window.addEventListener('scroll', checkAndStart);
    checkAndStart();
}

// ==================== FEATURE CARDS HOVER EFFECT ====================
function initFeatureCards() {
    const featureCards = document.querySelectorAll('.feature-card');

    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            // Add subtle scale to icon
            const icon = this.querySelector('.feature-icon');
            if (icon) {
                icon.style.transform = 'scale(1.1) rotate(5deg)';
            }
        });

        card.addEventListener('mouseleave', function () {
            const icon = this.querySelector('.feature-icon');
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
            }
        });
    });
}

// ==================== SMOOTH SCROLL ====================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ==================== SCROLL TO DEMO ====================
function scrollToDemo() {
    const demoSection = document.querySelector('#demo');
    if (demoSection) {
        demoSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// ==================== NAVBAR SCROLL EFFECT ====================
function initNavbarScroll() {
    const nav = document.querySelector('.nav');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            nav.style.boxShadow = '0 4px 12px rgba(13, 27, 42, 0.08)';
            nav.style.background = 'rgba(255, 255, 255, 0.95)';
        } else {
            nav.style.boxShadow = 'none';
            nav.style.background = 'rgba(255, 255, 255, 0.8)';
        }

        lastScroll = currentScroll;
    });
}

// ==================== PARALLAX EFFECT FOR ORBS ====================
function initParallax() {
    const orbs = document.querySelectorAll('.gradient-orb');

    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;

        orbs.forEach((orb, index) => {
            const speed = 0.5 + (index * 0.2);
            const yPos = -(scrolled * speed);
            orb.style.transform = `translateY(${yPos}px)`;
        });
    });
}

// ==================== INTERSECTION OBSERVER FOR FADE-IN ====================
function initFadeInObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all sections
    document.querySelectorAll('section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
        observer.observe(section);
    });
}

// ==================== CURSOR TRAIL EFFECT (SUBTLE) ====================
function initCursorEffect() {
    const trail = [];
    const trailLength = 5;

    document.addEventListener('mousemove', (e) => {
        // Only on hero section
        const hero = document.querySelector('.hero');
        if (!hero) return;

        const rect = hero.getBoundingClientRect();
        if (e.clientY < rect.top || e.clientY > rect.bottom) return;

        trail.push({ x: e.clientX, y: e.clientY, time: Date.now() });

        if (trail.length > trailLength) {
            trail.shift();
        }
    });
}

// ==================== INITIALIZE ALL ====================
function init() {
    console.log('🚀 KioskAI Landing Page Initialized');

    // Initialize all features
    initHeroStats();
    initImpactCounters();
    initTimeline();
    initNeuralNetwork();
    initChatDemo();
    initFeatureCards();
    initSmoothScroll();
    initNavbarScroll();
    initParallax();
    initCursorEffect();

    // Add loaded class to body
    document.body.classList.add('loaded');

    console.log('✨ All animations ready');
}

// ==================== DOM READY ====================
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// ==================== EXPORT FOR GLOBAL ACCESS ====================
window.scrollToDemo = scrollToDemo;
