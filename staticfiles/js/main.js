// Slider functionality
let currentSlide = 0;
const slides = document.querySelectorAll('[id^="slide-"]');
const indicators = document.querySelectorAll('[onclick^="goToSlide"]');

function showSlide(index) {
    // Hide all slides
    slides.forEach(slide => {
        slide.classList.remove('opacity-100');
        slide.classList.add('opacity-0');
    });
    
    // Hide all slide contents
    slides.forEach(slide => {
        const content = slide.querySelector('div > div');
        content.classList.remove('opacity-100', 'translate-y-0');
        content.classList.add('opacity-0', 'translate-y-5');
    });
    
    // Show current slide
    slides[index].classList.remove('opacity-0');
    slides[index].classList.add('opacity-100');
    
    // Show current slide content
    const currentContent = slides[index].querySelector('div > div');
    currentContent.classList.remove('opacity-0', 'translate-y-5');
    currentContent.classList.add('opacity-100', 'translate-y-0');
    
    // Update indicators
    indicators.forEach((indicator, i) => {
        if (i === index) {
            indicator.classList.remove('bg-opacity-50');
            indicator.classList.add('bg-white');
        } else {
            indicator.classList.remove('bg-white');
            indicator.classList.add('bg-opacity-50');
        }
    });
    
    currentSlide = index;
}

function nextSlide() {
    const nextIndex = (currentSlide + 1) % slides.length;
    showSlide(nextIndex);
}

function prevSlide() {
    const prevIndex = (currentSlide - 1 + slides.length) % slides.length;
    showSlide(prevIndex);
}

function goToSlide(index) {
    showSlide(index);
}

// Auto slide
let slideInterval = setInterval(nextSlide, 5000);

// Pause on hover
const slider = document.querySelector('.relative.h-\\[500px\\]');
if (slider) {
    slider.addEventListener('mouseenter', () => clearInterval(slideInterval));
    slider.addEventListener('mouseleave', () => slideInterval = setInterval(nextSlide, 5000));
}

// Mobile menu toggle
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

// Initialize first slide
document.addEventListener('DOMContentLoaded', () => {
    if (slides.length > 0) {
        showSlide(0);
    }
    
    // Intersection Observer for scroll animations
    const animateOnScroll = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    };
    
    const observer = new IntersectionObserver(animateOnScroll, {
        threshold: 0.1
    });
    
    document.querySelectorAll('[data-animate]').forEach(element => {
        observer.observe(element);
    });
});