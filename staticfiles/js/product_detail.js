document.addEventListener("DOMContentLoaded", function () {
    // Initialize variables
    const addToCartBtn = document.querySelector('.add-to-cart-btn');
    const buyNowBtn = document.querySelector('.buy-now-btn');
    const quantityInput = document.querySelector('#quantity');
    const sizeButtons = document.querySelectorAll('.size-btn');
    let selectedSize = 'M'; // Default size

    // Size selection
    sizeButtons.forEach(button => {
        // Set initial active state for size M
        if (button.dataset.size === 'M') {
            button.classList.add('active');
        }

        button.addEventListener('click', function() {
            sizeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            selectedSize = this.dataset.size;
        });
    });

    // Get CSRF Token
    function getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!tokenElement) {
            console.error('CSRF token not found');
            return null;
        }
        return tokenElement.value;
    }

    // Handle cart actions
    function handleCartAction(action) {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            showToast('CSRF token not found', 'error');
            return;
        }

        const quantity = parseInt(quantityInput.value) || 1;
        const productSlug = addToCartBtn.dataset.productSlug;

        if (!productSlug) {
            showToast('Product slug not found', 'error');
            return;
        }

        // Validate quantity
        if (quantity < 1) {
            showToast('Số lượng phải lớn hơn 0', 'error');
            return;
        }

        // Validate size selection
        if (!selectedSize) {
            showToast('Vui lòng chọn kích thước', 'error');
            return;
        }

        // Show loading state
        const originalText = action === 'add-to-cart' ? addToCartBtn.innerHTML : buyNowBtn.innerHTML;
        if (action === 'add-to-cart') {
            addToCartBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang thêm...';
            addToCartBtn.disabled = true;
        } else {
            buyNowBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
            buyNowBtn.disabled = true;
        }

        fetch(`/cart/add/${productSlug}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                quantity: quantity,
                size: selectedSize
            })
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('Vui lòng đăng nhập để thêm vào giỏ hàng');
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
        })
        .finally(() => {
            // Reset button state
            if (action === 'add-to-cart') {
                addToCartBtn.innerHTML = originalText;
                addToCartBtn.disabled = false;
            } else {
                buyNowBtn.innerHTML = originalText;
                buyNowBtn.disabled = false;
            }
        });
    }

    // Add to cart button click handler
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleCartAction('add-to-cart');
        });
    }

    // Buy now button click handler
    if (buyNowBtn) {
        buyNowBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleCartAction('buy-now');
        });
    }

    // Quantity update function
    function updateQuantity(change) {
        const currentValue = parseInt(quantityInput.value) || 0;
        const newValue = currentValue + change;
        const maxStock = parseInt(quantityInput.getAttribute('max')) || 999;
        
        if (newValue >= 1 && newValue <= maxStock) {
            quantityInput.value = newValue;
        }
    }

    // Add quantity button handlers
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const change = this.textContent === '+' ? 1 : -1;
            updateQuantity(change);
        });
    });

    // Toast notification function
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

    // Review form handling
    const reviewForm = document.getElementById('reviewForm');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const reviewsList = document.querySelector('.reviews-list');

    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Check if rating is selected
            const rating = document.querySelector('input[name="rating"]:checked');
            if (!rating) {
                showToast('Vui lòng chọn số sao đánh giá', 'error');
                return;
            }
            
            const formData = new FormData(this);
            const images = document.getElementById('reviewImages').files;
            
            // Add each selected image to FormData
            for (let i = 0; i < images.length; i++) {
                formData.append('images[]', images[i]);
            }

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'success');
                    
                    // Add new review to the list
                    const newReview = createReviewElement(data.comment);
                    if (reviewsList.querySelector('.no-reviews')) {
                        reviewsList.innerHTML = '';
                    }
                    reviewsList.insertBefore(newReview, reviewsList.firstChild);
                    
                    // Reset form and clear image preview
                    reviewForm.reset();
                    imagePreviewContainer.innerHTML = '';
                    
                    // Reset star rating
                    document.querySelectorAll('input[name="rating"]').forEach(input => {
                        input.checked = false;
                    });
                    document.querySelectorAll('.star-label i').forEach(star => {
                        star.className = 'far fa-star';
                    });
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Có lỗi xảy ra khi gửi đánh giá', 'error');
            });
        });
    }

    // Create review element
    function createReviewElement(comment) {
        const reviewItem = document.createElement('div');
        reviewItem.className = 'review-item';
        
        const stars = Array(5).fill().map((_, i) => 
            `<i class="${i < comment.rating ? 'fas' : 'far'} fa-star"></i>`
        ).join('');
        
        const images = comment.images.map(imageUrl => `
            <div class="review-image-item">
                <img src="${imageUrl}" alt="Review image" onclick="showFullImage(this.src)">
            </div>
        `).join('');
        
        reviewItem.innerHTML = `
            <div class="review-header">
                <div class="reviewer-info">
                    <img src="${comment.user.avatar}" alt="${comment.user.username}" class="reviewer-avatar">
                    <div class="reviewer-details">
                        <div class="reviewer-name">${comment.user.username}</div>
                        <div class="review-date">${comment.created_at}</div>
                    </div>
                </div>
                <div class="review-rating">
                    ${stars}
                </div>
            </div>
            <div class="review-content">
                ${comment.content.replace(/\n/g, '<br>')}
                ${comment.images.length > 0 ? `
                    <div class="review-images">
                        ${images}
                    </div>
                ` : ''}
            </div>
        `;
        
        return reviewItem;
    }

    // Favorite button handling
    const favoriteBtn = document.querySelector('.favorite-btn');
    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const productSlug = this.dataset.productSlug;
            const csrfToken = getCSRFToken();
            
            if (!csrfToken) {
                showToast('CSRF token not found', 'error');
                return;
            }

            // Show loading state
            const icon = this.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'fas fa-spinner fa-spin';
            this.disabled = true;

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
                        throw new Error('Vui lòng đăng nhập để thêm vào yêu thích');
                    }
                    return response.json().then(data => {
                        throw new Error(data.message || 'Có lỗi xảy ra khi thêm vào yêu thích');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Toggle heart icon
                    icon.className = icon.classList.contains('far') ? 'fas fa-heart' : 'far fa-heart';
                    showToast(data.message, 'success');
                } else {
                    icon.className = originalClass;
                    showToast(data.message || 'Có lỗi xảy ra khi thêm vào yêu thích', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                icon.className = originalClass;
                showToast(error.message || 'Có lỗi xảy ra khi thêm vào yêu thích', 'error');
            })
            .finally(() => {
                this.disabled = false;
            });
        });
    }

    // Image preview handling
    const imageUploadArea = document.querySelector('.image-upload-section');
    if (imageUploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            imageUploadArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            imageUploadArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            imageUploadArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            imageUploadArea.classList.add('highlight');
        }

        function unhighlight(e) {
            imageUploadArea.classList.remove('highlight');
        }

        imageUploadArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            const input = document.getElementById('reviewImages');
            
            // Combine existing files with new files
            const existingFiles = Array.from(input.files || []);
            const newFiles = Array.from(files);
            const totalFiles = existingFiles.length + newFiles.length;
            
            if (totalFiles > 5) {
                showToast('Chỉ được chọn tối đa 5 hình ảnh', 'error');
                return;
            }
            
            const dt2 = new DataTransfer();
            existingFiles.forEach(file => dt2.items.add(file));
            newFiles.forEach(file => dt2.items.add(file));
            
            input.files = dt2.files;
            previewImages({ target: input });
        }
    }

    // Star rating hover effect
    const starLabels = document.querySelectorAll('.star-label');
    starLabels.forEach((label, index) => {
        label.addEventListener('mouseover', () => {
            // Highlight stars up to current
            starLabels.forEach((l, i) => {
                const star = l.querySelector('i');
                star.className = i <= index ? 'fas fa-star' : 'far fa-star';
            });
        });
        
        label.addEventListener('mouseout', () => {
            // Reset to selected rating
            const selectedRating = document.querySelector('input[name="rating"]:checked');
            starLabels.forEach((l, i) => {
                const star = l.querySelector('i');
                star.className = selectedRating && i < selectedRating.value ? 'fas fa-star' : 'far fa-star';
            });
        });
    });
});

// Global functions
function previewImages(event) {
    const container = document.getElementById('imagePreviewContainer');
    const files = event.target.files;
    const existingImages = container.querySelectorAll('.image-preview-item').length;
    const totalImages = existingImages + files.length;
    
    if (totalImages > 5) {
        showToast('Chỉ được chọn tối đa 5 hình ảnh', 'error');
        event.target.value = '';
        return;
    }
    
    Array.from(files).forEach((file, index) => {
        // Check file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showToast(`Hình ảnh ${file.name} vượt quá 5MB`, 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const div = document.createElement('div');
            div.className = 'image-preview-item';
            div.dataset.fileIndex = existingImages + index;
            
            div.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button type="button" class="remove-image" onclick="removeImage(this)">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(div);
        }
        reader.readAsDataURL(file);
    });
}

function removeImage(button) {
    const container = document.getElementById('imagePreviewContainer');
    const item = button.closest('.image-preview-item');
    const input = document.getElementById('reviewImages');
    
    const dt = new DataTransfer();
    const { files } = input;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== parseInt(item.dataset.fileIndex)) {
            dt.items.add(files[i]);
        }
    }
    
    input.files = dt.files;
    item.remove();
    
    // Update indices for remaining images
    container.querySelectorAll('.image-preview-item').forEach((item, index) => {
        item.dataset.fileIndex = index;
    });
}

function previewReview() {
    const rating = document.querySelector('input[name="rating"]:checked')?.value;
    const content = document.getElementById('reviewContent').value;
    const images = document.getElementById('reviewImages').files;
    const previewSection = document.getElementById('reviewPreview');
    const submitButton = document.querySelector('.submit-review');
    
    if (!rating) {
        showToast('Vui lòng chọn số sao đánh giá', 'error');
        return;
    }
    
    if (!content.trim()) {
        showToast('Vui lòng nhập nội dung đánh giá', 'error');
        return;
    }
    
    // Update preview content
    const previewStars = previewSection.querySelector('.preview-stars');
    previewStars.innerHTML = Array(5).fill().map((_, i) => 
        `<i class="fa${i < rating ? 's' : 'r'} fa-star"></i>`
    ).join('');
    
    previewSection.querySelector('.preview-text').textContent = content;
    
    const previewImages = previewSection.querySelector('.preview-images');
    previewImages.innerHTML = '';
    Array.from(images).forEach(file => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            previewImages.appendChild(img);
        }
        reader.readAsDataURL(file);
    });
    
    previewSection.style.display = 'block';
    submitButton.style.display = 'block';
}

function showFullImage(src) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('fullImage');
    modal.style.display = "block";
    modalImg.src = src;
}

// Close modal when clicking the x button
document.querySelector('.close-modal').onclick = function() {
    document.getElementById('imageModal').style.display = "none";
}

// Close modal when clicking outside the image
document.getElementById('imageModal').onclick = function(e) {
    if (e.target === this) {
        this.style.display = "none";
    }
}
