// Constants for API URLs
const API_URLS = {
    PROVINCE: 'https://provinces.open-api.vn/api/p/',
    DISTRICT: 'https://provinces.open-api.vn/api/p/{province_code}?depth=2',
    WARD: 'https://provinces.open-api.vn/api/d/{district_code}?depth=2',
    BANKS: 'https://api.vietqr.io/v2/banks'
};

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('checkoutForm');
    const toastElement = document.getElementById('errorToast');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (!form || !toastElement || !loadingOverlay) {
        console.error('Required elements not found');
        return;
    }

    const toast = new bootstrap.Toast(toastElement);

    // Function to show error message
    function showError(message) {
        const toastBody = document.querySelector('.toast-body');
        if (toastBody) {
            toastBody.textContent = message || 'Có lỗi xảy ra. Vui lòng thử lại sau.';
            toast.show();
        }
    }

    // Function to show/hide loading overlay
    function toggleLoading(show) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    // Function to validate a single field
    function validateField(field) {
        let isValid = true;
        field.classList.remove('is-invalid');

        if (field.hasAttribute('required') && !field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        }

        if (field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        }

        if (field.id === 'phone' && field.value) {
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(field.value)) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        }

        return isValid;
    }

    // Function to validate the entire form
    function validateForm() {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });

        // Validate payment method
        const selectedPayment = document.querySelector('.payment-option.active');
        const paymentMethods = document.querySelector('.payment-methods');
        const paymentError = document.querySelector('.payment-method-error');
        
        if (!selectedPayment) {
            if (paymentMethods) paymentMethods.classList.add('is-invalid');
            if (paymentError) paymentError.style.display = 'block';
            isValid = false;
        } else {
            if (paymentMethods) paymentMethods.classList.remove('is-invalid');
            if (paymentError) paymentError.style.display = 'none';
        }

        return isValid;
    }

    // Load provinces
    async function loadProvinces() {
        try {
            const response = await fetch(API_URLS.PROVINCE);
            if (!response.ok) throw new Error('Failed to fetch provinces');
            
            const provinces = await response.json();
            const provinceSelect = document.getElementById('province');
            
            if (provinceSelect) {
                provinceSelect.innerHTML = '<option value="">Chọn tỉnh/thành phố</option>';
                provinces.forEach(province => {
                    const option = document.createElement('option');
                    option.value = province.code;
                    option.textContent = province.name;
                    provinceSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading provinces:', error);
            showError('Không thể tải danh sách tỉnh/thành phố');
        }
    }

    // Load districts
    async function loadDistricts(provinceCode) {
        try {
            const url = API_URLS.DISTRICT.replace('{province_code}', provinceCode);
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch districts');
            
            const data = await response.json();
            const districtSelect = document.getElementById('district');
            const wardSelect = document.getElementById('ward');
            
            if (districtSelect) {
                districtSelect.innerHTML = '<option value="">Chọn quận/huyện</option>';
                data.districts.forEach(district => {
                    const option = document.createElement('option');
                    option.value = district.code;
                    option.textContent = district.name;
                    districtSelect.appendChild(option);
                });
            }
            
            if (wardSelect) {
                wardSelect.innerHTML = '<option value="">Chọn phường/xã</option>';
            }
        } catch (error) {
            console.error('Error loading districts:', error);
            showError('Không thể tải danh sách quận/huyện');
        }
    }

    // Load wards
    async function loadWards(districtCode) {
        try {
            const url = API_URLS.WARD.replace('{district_code}', districtCode);
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch wards');
            
            const data = await response.json();
            const wardSelect = document.getElementById('ward');
            
            if (wardSelect) {
                wardSelect.innerHTML = '<option value="">Chọn phường/xã</option>';
                data.wards.forEach(ward => {
                    const option = document.createElement('option');
                    option.value = ward.code;
                    option.textContent = ward.name;
                    wardSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading wards:', error);
            showError('Không thể tải danh sách phường/xã');
        }
    }

    // Load banks
    async function loadBanks() {
        try {
            const response = await fetch(API_URLS.BANKS);
            if (!response.ok) throw new Error('Failed to fetch banks');
            
            const data = await response.json();
            const bankSelect = document.getElementById('bankName');
            
            if (bankSelect && data.data) {
                bankSelect.innerHTML = '<option value="">Vui lòng chọn ngân hàng</option>';
                data.data.forEach(bank => {
                    const option = document.createElement('option');
                    option.value = bank.bin;
                    option.textContent = bank.name;
                    bankSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading banks:', error);
            showError('Không thể tải danh sách ngân hàng');
        }
    }

    // Event Listeners
    const provinceSelect = document.getElementById('province');
    const districtSelect = document.getElementById('district');
    const wardSelect = document.getElementById('ward');

    if (provinceSelect) {
        provinceSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                loadDistricts(e.target.value);
                const provinceNameInput = document.getElementById('provinceName');
                if (provinceNameInput) {
                    provinceNameInput.value = e.target.options[e.target.selectedIndex].text;
                }
            }
            validateField(provinceSelect);
        });
    }

    if (districtSelect) {
        districtSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                loadWards(e.target.value);
                const districtNameInput = document.getElementById('districtName');
                if (districtNameInput) {
                    districtNameInput.value = e.target.options[e.target.selectedIndex].text;
                }
            }
            validateField(districtSelect);
        });
    }

    if (wardSelect) {
        wardSelect.addEventListener('change', (e) => {
            const wardNameInput = document.getElementById('wardName');
            if (wardNameInput && e.target.selectedIndex !== -1) {
                wardNameInput.value = e.target.options[e.target.selectedIndex].text;
            }
            validateField(wardSelect);
        });
    }

    // Payment method selection
    const paymentOptions = document.querySelectorAll('.payment-option');
    paymentOptions.forEach(option => {
        option.addEventListener('click', function() {
            paymentOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.payment-info-section').forEach(section => {
                section.style.display = 'none';
            });
            
            const method = this.dataset.method;
            const methodSection = document.getElementById(method + 'Selection') || 
                                document.getElementById(method + 'Info');
            
            if (methodSection) {
                methodSection.style.display = 'block';
                if (method === 'bank') {
                    loadBanks();
                }
            }

            const paymentMethods = document.querySelector('.payment-methods');
            const errorElement = document.querySelector('.payment-method-error');
            if (paymentMethods) paymentMethods.classList.remove('is-invalid');
            if (errorElement) errorElement.style.display = 'none';
        });
    });

    // Handle promo code
    const applyPromoButton = document.getElementById('applyPromo');
    if (applyPromoButton) {
        applyPromoButton.addEventListener('click', async function() {
            const promoCode = document.getElementById('promoCode')?.value.trim();
            if (!promoCode) {
                showError('Vui lòng nhập mã giảm giá');
                return;
            }

            try {
                const response = await fetch('/validate-promo/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ promo_code: promoCode })
                });

                const data = await response.json();
                const promoMessage = document.getElementById('promoMessage');
                const discountRow = document.getElementById('discountRow');
                const discountAmount = document.getElementById('discountAmount');
                const totalAmount = document.getElementById('totalAmount');
                const subtotalAmount = document.getElementById('subtotalAmount');

                if (data.success) {
                    if (promoMessage) {
                        promoMessage.textContent = data.message;
                        promoMessage.style.color = '#28a745';
                    }
                    if (discountRow) discountRow.style.display = 'flex';
                    
                    const subtotal = parseFloat(subtotalAmount?.textContent.replace(/[^\d]/g, '') || 0);
                    const shipping = 30000;
                    const discount = parseFloat(data.discount_amount || 0);
                    const total = subtotal + shipping - discount;
                    
                    if (discountAmount) {
                        discountAmount.textContent = `-${discount.toLocaleString('vi-VN')}₫`;
                    }
                    if (totalAmount) {
                        totalAmount.textContent = `${total.toLocaleString('vi-VN')}₫`;
                    }
                    
                    let promoInput = form.querySelector('input[name="promo_code"]');
                    if (!promoInput) {
                        promoInput = document.createElement('input');
                        promoInput.type = 'hidden';
                        promoInput.name = 'promo_code';
                        form.appendChild(promoInput);
                    }
                    promoInput.value = promoCode;
                } else {
                    if (promoMessage) {
                        promoMessage.textContent = data.message;
                        promoMessage.style.color = '#dc3545';
                    }
                    if (discountRow) discountRow.style.display = 'none';
                    
                    const subtotal = parseFloat(subtotalAmount?.textContent.replace(/[^\d]/g, '') || 0);
                    const shipping = 30000;
                    const total = subtotal + shipping;
                    
                    if (totalAmount) {
                        totalAmount.textContent = `${total.toLocaleString('vi-VN')}₫`;
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Có lỗi xảy ra khi áp dụng mã giảm giá');
            }
        });
    }

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            showError('Vui lòng điền đầy đủ thông tin bắt buộc');
            return;
        }

        toggleLoading(true);

        try {
            const formData = new FormData(this);
            const selectedPayment = document.querySelector('.payment-option.active');
            
            if (!selectedPayment) {
                toggleLoading(false);
                showError('Vui lòng chọn phương thức thanh toán');
                return;
            }

            // Get province, district, ward names from select elements
            const provinceSelect = document.getElementById('province');
            const districtSelect = document.getElementById('district');
            const wardSelect = document.getElementById('ward');

            if (provinceSelect && provinceSelect.selectedOptions[0]) {
                formData.set('province_name', provinceSelect.selectedOptions[0].text);
            }
            if (districtSelect && districtSelect.selectedOptions[0]) {
                formData.set('district_name', districtSelect.selectedOptions[0].text);
            }
            if (wardSelect && wardSelect.selectedOptions[0]) {
                formData.set('ward_name', wardSelect.selectedOptions[0].text);
            }
            
            formData.append('payment_method', selectedPayment.dataset.method);
            
            if (selectedPayment.dataset.method === 'bank') {
                const bankSelect = document.getElementById('bankName');
                if (!bankSelect || !bankSelect.value) {
                    toggleLoading(false);
                    showError('Vui lòng chọn ngân hàng');
                    return;
                }
                formData.append('bank_name', bankSelect.options[bankSelect.selectedIndex].text);
                formData.append('bank_bin', bankSelect.value);
            }

            // Get the checkout URL from the form's data attribute or window variable
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                throw new Error('Server response was not JSON');
            }

            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                toggleLoading(false);
                showError(data.message || 'Có lỗi xảy ra. Vui lòng thử lại sau.');
            }
        } catch (error) {
            console.error('Error:', error);
            toggleLoading(false);
            showError('Có lỗi xảy ra. Vui lòng thử lại sau.');
        }
    });

    // Initialize
    loadProvinces();
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}