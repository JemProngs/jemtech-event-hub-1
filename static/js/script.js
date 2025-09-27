// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initTooltips();
    initPopovers();
    initAlerts();
    initForms();
    initFilePreviews();
    initClock();
    initSmoothScrolling();
    initThemeToggle();
    initImageLazyLoading();
    initScrollAnimations();
    initPerformanceMonitoring();
});

// Tooltip initialization
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus'
        });
    });
}

// Popover initialization
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'focus'
        });
    });
}

// Auto-dismiss alerts
function initAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        const timeout = alert.dataset.dismissDelay || 5000;
        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, parseInt(timeout));
    });
}

// Form validation enhancement
function initForms() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    validateField(input);
                }
            });
        });

        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();

                // Focus first invalid field
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            form.classList.add('was-validated');
        });
    });
}

// Field validation with custom messages
function validateField(field) {
    const formGroup = field.closest('.form-group') || field.closest('.mb-3');
    const feedback = field.nextElementSibling;

    if (field.checkValidity()) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.style.display = 'none';
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.style.display = 'block';
        }
    }
}

// Image preview for file inputs
function initFilePreviews() {
    const fileInputs = document.querySelectorAll('input[type="file"][data-preview]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const previewId = this.getAttribute('data-preview');
            const preview = document.getElementById(previewId);
            const clearBtn = this.parentNode.querySelector('.file-clear');

            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    if (clearBtn) clearBtn.style.display = 'block';
                }
                reader.readAsDataURL(this.files[0]);
            } else {
                preview.style.display = 'none';
                if (clearBtn) clearBtn.style.display = 'none';
            }
        });

        // Add clear button functionality
        const clearBtn = input.parentNode.querySelector('.file-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                input.value = '';
                const previewId = input.getAttribute('data-preview');
                const preview = document.getElementById(previewId);
                preview.style.display = 'none';
                this.style.display = 'none';
            });
        }
    });
}

// Real-time clock
function initClock() {
    function updateClock() {
        const clockElements = document.querySelectorAll('.real-time-clock');
        if (clockElements.length > 0) {
            const now = new Date();
            const options = {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            };
            const timeString = now.toLocaleTimeString('en-US', options);
            const dateString = now.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            clockElements.forEach(el => {
                if (el.dataset.format === 'datetime') {
                    el.innerHTML = `${dateString} <br> <strong>${timeString}</strong>`;
                } else {
                    el.textContent = timeString;
                }
            });
        }
    }
    setInterval(updateClock, 1000);
    updateClock();
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const offsetTop = target.getBoundingClientRect().top + window.pageYOffset - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });

                // Update URL without page jump
                history.pushState(null, null, href);
            }
        });
    });
}

// Theme toggle functionality
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Get saved theme or use system preference
    let currentTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');
    setTheme(currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(currentTheme);
            localStorage.setItem('theme', currentTheme);
        });
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            currentTheme = e.matches ? 'dark' : 'light';
            setTheme(currentTheme);
        }
    });

    function setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
        if (themeToggle) {
            themeToggle.setAttribute('title', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
        }
    }
}

// Lazy loading for images
function initImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img.lazy').forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback for older browsers
        document.querySelectorAll('img.lazy').forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

// Scroll animations
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.fade-in, .slide-in, .zoom-in');

    if ('IntersectionObserver' in window) {
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                    animationObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animatedElements.forEach(el => {
            el.style.animationPlayState = 'paused';
            animationObserver.observe(el);
        });
    }
}

// Performance monitoring
function initPerformanceMonitoring() {
    // Log page load performance
    window.addEventListener('load', () => {
        if ('performance' in window) {
            const navTiming = performance.getEntriesByType('navigation')[0];
            console.log('Page load time:', navTiming.loadEventEnd - navTiming.navigationStart, 'ms');
        }
    });

    // Monitor long tasks
    if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
                if (entry.duration > 50) {
                    console.warn('Long task detected:', entry);
                }
            });
        });
        observer.observe({ entryTypes: ['longtask'] });
    }
}

// Utility functions
window.JemTechUtils = {
    // Show toast notification
    showToast: function(message, type = 'info', duration = 5000) {
        const toastContainer = document.querySelector('.toast-container') || createToastContainer();
        const toastId = 'toast-' + Date.now();

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.id = toastId;

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });

        function getToastIcon(type) {
            const icons = {
                'success': 'check-circle',
                'danger': 'exclamation-triangle',
                'warning': 'exclamation-circle',
                'info': 'info-circle'
            };
            return icons[type] || 'info-circle';
        }

        function createToastContainer() {
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1060';
            document.body.appendChild(container);
            return container;
        }
    },

    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle function
    throttle: function(func, limit) {
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
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { JemTechUtils };
}

console.log('JemTech Event Hub enhanced JavaScript initialized');