document.addEventListener('alpine:init', () => {
  Alpine.data('slider', () => ({
      currentSlide: 0,
      slides: [],
      init() {
          this.slides = document.querySelectorAll('[id^="slide-"]');
          this.showSlide(this.currentSlide);
          setInterval(() => this.nextSlide(), 5000);
      },
      nextSlide() {
          this.currentSlide = (this.currentSlide + 1) % this.slides.length;
          this.showSlide(this.currentSlide);
      },
      prevSlide() {
          this.currentSlide = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
          this.showSlide(this.currentSlide);
      },
      goToSlide(index) {
          this.currentSlide = index;
          this.showSlide(this.currentSlide);
      },
      showSlide(index) {
          this.slides.forEach((slide, i) => {
              slide.style.opacity = i === index ? '1' : '0';
          });
      }
  }));
});

document.addEventListener('DOMContentLoaded', () => {
    function getCSRFToken() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        return csrfToken ? csrfToken.getAttribute('content') : null;
    }

    function handleCartAction(productSlug, action) {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            showToast('CSRF token not found', 'error');
            return;
        }

        fetch(`/cart/add/${productSlug}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ quantity: 1, size: 'M' })
        })
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login/?next=' + window.location.pathname;
                return;
            }
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update cart count
                const cartCountElement = document.querySelector('.cart-count');
                if (cartCountElement && data.cart_count) {
                    cartCountElement.textContent = data.cart_count;
                }
                
                if (action === 'buy-now') {
                    window.location.href = '/checkout/';
                } else {
                    showToast('Sản phẩm đã được thêm vào giỏ hàng!', 'success');
                }
            } else {
                showToast(data.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast(error.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng', 'error');
        });
    }

    // Handle "MUA NGAY" button
    document.querySelectorAll('.buy-now-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productSlug = this.dataset.productSlug;
            handleCartAction(productSlug, 'buy-now');
        });
    });

    // Handle "Thêm vào giỏ" button
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productSlug = this.dataset.productSlug;
            handleCartAction(productSlug, 'add-to-cart');
        });
    });

    // Handle Add to Favorites
    document.querySelectorAll('.add-to-favorites').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productSlug = this.dataset.productSlug;
            const csrfToken = getCSRFToken();
            
            if (!csrfToken) {
                showToast('CSRF token not found', 'error');
                return;
            }

            fetch(`/add-to-favorites/${productSlug}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                if (response.status === 401 || response.status === 403) {
                    window.location.href = '/login/?next=' + window.location.pathname;
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Change icon from outline to filled
                    const icon = this.querySelector('i');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message || 'Có lỗi xảy ra khi thêm vào yêu thích', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Có lỗi xảy ra khi thêm vào yêu thích', 'error');
            });
        });
    });

    // Toast Notification Function
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        if (toast) {
            toast.textContent = message;
            toast.className = `toast-message ${type}`;
            toast.classList.remove('hidden');
            setTimeout(() => {
                toast.classList.add('hidden');
                toast.className = 'toast-message hidden';
            }, 3000);
        }
    }
});