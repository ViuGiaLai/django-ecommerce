document.addEventListener('DOMContentLoaded', function() {
    // Create filter form
    const filterForm = document.createElement('form');
    filterForm.method = 'GET';
    filterForm.action = window.location.pathname;

    // Add existing query parameters
    const urlParams = new URLSearchParams(window.location.search);
    for (const [key, value] of urlParams.entries()) {
        if (key !== 'page') {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            filterForm.appendChild(input);
        }
    }

    // Handle remove filter clicks
    const removeFilterButtons = document.querySelectorAll('.remove-filter');
    if (removeFilterButtons) {
        removeFilterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const type = button.dataset.type;
                const value = button.dataset.value;
                
                // Create new URLSearchParams from current URL
                const searchParams = new URLSearchParams(window.location.search);
                
                // Remove the specific filter
                if (type === 'category') {
                    const categories = searchParams.getAll('category');
                    searchParams.delete('category');
                    categories.forEach(cat => {
                        if (cat !== value) {
                            searchParams.append('category', cat);
                        }
                    });
                } else if (type === 'color') {
                    const colors = searchParams.getAll('color');
                    searchParams.delete('color');
                    colors.forEach(color => {
                        if (color !== value) {
                            searchParams.append('color', color);
                        }
                    });
                } else if (type === 'size') {
                    const sizes = searchParams.getAll('size');
                    searchParams.delete('size');
                    sizes.forEach(size => {
                        if (size !== value) {
                            searchParams.append('size', size);
                        }
                    });
                } else if (type === 'price') {
                    // Reset price range to default
                    searchParams.delete('min_price');
                    searchParams.delete('max_price');
                    const priceRange = document.getElementById('priceRange');
                    const currentPrice = document.getElementById('currentPrice');
                    if (priceRange) priceRange.value = 1500000;
                    if (currentPrice) currentPrice.textContent = '1.500.000 ₫';
                }
                
                // Redirect to new URL
                window.location.search = searchParams.toString();
            });
        });
    }

    // Handle category checkboxes
    const categoryCheckboxes = document.querySelectorAll('input[type="checkbox"]');
    if (categoryCheckboxes) {
        categoryCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const categories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
                                    .map(cb => cb.value);
                
                // Remove existing category parameters
                filterForm.querySelectorAll('input[name="category"]').forEach(input => input.remove());
                
                // Add new category parameters
                categories.forEach(category => {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'category';
                    input.value = category;
                    filterForm.appendChild(input);
                });
                
                filterForm.submit();
            });
        });
    }

    // Price range slider
    const priceRange = document.getElementById('priceRange');
    const currentPrice = document.getElementById('currentPrice');
    let priceTimeout;

    if (priceRange && currentPrice) {
        priceRange.addEventListener('input', function() {
            // Format price with thousand separator
            const formattedValue = new Intl.NumberFormat('vi-VN').format(this.value);
            currentPrice.textContent = formattedValue + ' ₫';

            // Update filter with debounce
            clearTimeout(priceTimeout);
            priceTimeout = setTimeout(() => {
                // Create new URLSearchParams from current URL
                const searchParams = new URLSearchParams(window.location.search);
                
                // Update min_price parameter
                searchParams.set('min_price', this.value);
                
                // Keep max_price if it exists, otherwise use default
                if (!searchParams.has('max_price')) {
                    searchParams.set('max_price', '3000000');
                }
                
                // Redirect to new URL
                window.location.search = searchParams.toString();
            }, 500);
        });
    }

    // Handle color buttons
    const colorButtons = document.querySelectorAll('.color-button');
    if (colorButtons) {
        colorButtons.forEach(button => {
            button.addEventListener('click', () => {
                const color = button.dataset.color;
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'color';
                input.value = color;
                filterForm.appendChild(input);
                filterForm.submit();
            });
        });
    }

    // Handle sort select
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'sort';
            input.value = e.target.value;
            filterForm.appendChild(input);
            filterForm.submit();
        });
    }

    // Handle view mode
    const viewButtons = document.querySelectorAll('.view-button');
    if (viewButtons) {
        viewButtons.forEach(button => {
            button.addEventListener('click', () => {
                const view = button.dataset.view;
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'view';
                input.value = view;
                filterForm.appendChild(input);
                filterForm.submit();
            });
        });
    }

    // Add form to body
    document.body.appendChild(filterForm);

    // Handle add to cart
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    if (addToCartButtons) {
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const productSlug = this.dataset.productSlug;
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

                if (!csrfToken) {
                    console.error('CSRF token not found');
                    showToast('CSRF token not found', 'error');
                    return;
                }
                
                fetch(`/cart/add/${productSlug}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        quantity: 1,
                        size: 'M'
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 403) {
                            window.location.href = '/login/?next=' + window.location.pathname;
                            return;
                        }
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
                        showToast('Sản phẩm đã được thêm vào giỏ hàng!', 'success');
                    } else {
                        showToast(data.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast(error.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng', 'error');
                });
            });
        });
    }

    // Handle add to favorites
    const favoriteButtons = document.querySelectorAll('.add-to-favorites');
    if (favoriteButtons) {
        favoriteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const productSlug = this.dataset.productSlug;
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

                if (!csrfToken) {
                    console.error('CSRF token not found');
                    showToast('CSRF token not found', 'error');
                    return;
                }
                
                fetch(`/add-to-favorites/${productSlug}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                })
                .then(response => {
                    if (!response.ok) {
                        if (response.status === 403) {
                            window.location.href = '/login/?next=' + window.location.pathname;
                            return;
                        }
                        throw new Error('Có lỗi xảy ra khi thêm vào yêu thích');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Change icon from outline to filled
                        const icon = this.querySelector('i');
                        if (icon) {
                            icon.classList.remove('far');
                            icon.classList.add('fas');
                        }
                        showToast('Đã thêm vào danh sách yêu thích!', 'success');
                    } else {
                        showToast(data.message || 'Có lỗi xảy ra khi thêm vào yêu thích', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast(error.message || 'Có lỗi xảy ra khi thêm vào yêu thích', 'error');
                });
            });
        });
    }
});

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) {
        console.error('Toast element not found');
        return;
    }

    toast.textContent = message;
    toast.className = `toast-message ${type}`;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
        toast.className = 'toast-message hidden';
    }, 3000);
}