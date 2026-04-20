/**
 * Performance optimization for Si Chen's Homepage
 */

// Lazy loading for images
document.addEventListener('DOMContentLoaded', function() {
    // Check if native lazy loading is supported
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
            }
        });
    } else {
        // Fallback to Intersection Observer for older browsers
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });

        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => imageObserver.observe(img));
    }
});

// Optimize media logo hover effects
document.addEventListener('DOMContentLoaded', function() {
    const mediaLogos = document.querySelectorAll('.media-logo img');
    
    // Preload images on hover for smoother transitions
    mediaLogos.forEach(logo => {
        logo.addEventListener('mouseenter', function() {
            this.style.willChange = 'transform, filter, opacity';
        });
        
        logo.addEventListener('mouseleave', function() {
            this.style.willChange = 'auto';
        });
    });
});

// Performance monitoring (optional - remove in production)
if (window.performance && window.performance.timing) {
    window.addEventListener('load', function() {
        const timing = window.performance.timing;
        const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
        console.log('Page load time:', pageLoadTime + 'ms');
        
        // Send to analytics if needed
        if (typeof gtag !== 'undefined') {
            gtag('event', 'timing_complete', {
                'name': 'load',
                'value': pageLoadTime,
                'event_category': 'Performance'
            });
        }
    });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
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

// Optimize font loading
if ('fonts' in document) {
    document.fonts.ready.then(function() {
        document.body.classList.add('fonts-loaded');
    });
}