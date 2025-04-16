document.addEventListener('DOMContentLoaded', function() {
    
    // Back to top button
    const backToTop = document.getElementById('back-to-top');
    
    // Scroll animation
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                backToTop.classList.remove('opacity-0', 'scale-0');
                backToTop.classList.add('opacity-100', 'scale-100');
            } else {
                backToTop.classList.remove('opacity-100', 'scale-100');
                backToTop.classList.add('opacity-0', 'scale-0');
            }
        });

        // Smooth scroll to top
        backToTop.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Newsletter form animation
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = this.querySelector('input[type="email"]');
            const submitBtn = this.querySelector('button[type="submit"]');
            
            if (emailInput.value) {
                // Animation khi submit thành công
                submitBtn.innerHTML = `
                    <span class="flex items-center">
                        <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        Đã đăng ký
                    </span>
                `;
                submitBtn.classList.add('bg-green-600');
                submitBtn.classList.remove('bg-black');

                // Reset sau 3 giây
                setTimeout(() => {
                    emailInput.value = '';
                    submitBtn.innerHTML = 'ĐĂNG KÝ';
                    submitBtn.classList.remove('bg-green-600');
                    submitBtn.classList.add('bg-black');
                }, 3000);
            }
        });
    }

    // Thêm animation cho các phần tử
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.scroll-animate');
        elements.forEach(el => {
            const elementPosition = el.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.2;
            
            if (elementPosition < screenPosition) {
                el.classList.add('animate-fadeInUp');
            }
        });
    };

    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Chạy lần đầu khi load trang
});

// JavaScript để toggle chat box
document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chat-box-comment');
    const chatContainer = document.getElementById('chatgpt-container');
    
    if (chatButton && chatContainer) {
        const closeButton = chatContainer.querySelector('.close-btn-gpt');
        
        chatButton.addEventListener('click', function() {
            chatContainer.classList.toggle('hidden');
        });

        if (closeButton) {
            closeButton.addEventListener('click', function() {
                chatContainer.classList.add('hidden');
            });
        }

        // Đóng chat khi click bên ngoài
        document.addEventListener('click', function(event) {
            if (!chatContainer.contains(event.target) && !chatButton.contains(event.target)) {
                chatContainer.classList.add('hidden');
            }
        });
    }
});