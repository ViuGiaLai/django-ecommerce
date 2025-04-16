document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const searchIcon = document.querySelector('.search-icon');
    const searchContainer = document.querySelector('.search-container');
    const searchClose = document.querySelector('.search-close');

    // Toggle menu hamburger
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }

    // Toggle search bar
    if (searchIcon) {
        searchIcon.addEventListener('click', function(e) {
            e.preventDefault();
            searchContainer.style.display = searchContainer.style.display === 'block' ? 'none' : 'block';
        });
    }

    // Close search bar
    if (searchClose) {
        searchClose.addEventListener('click', function() {
            searchContainer.style.display = 'none';
        });
    }

    // Close search bar when clicking outside
    document.addEventListener('click', function(e) {
        if (searchContainer && !searchContainer.contains(e.target) && !searchIcon.contains(e.target)) {
            searchContainer.style.display = 'none';
        }
    });

    // Chọn size trong product_detail
    const sizeButtons = document.querySelectorAll('.size-btn');
    const selectedSizeInput = document.getElementById('selected-size');
    
    if (sizeButtons.length > 0) {
        sizeButtons.forEach(button => {
            button.addEventListener('click', () => {
                sizeButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                selectedSizeInput.value = button.textContent;
            });
        });
    }

    setTimeout(function () {
        let alerts = document.querySelectorAll(".alert");
        alerts.forEach((alert) => {
            alert.style.opacity = "0";  // Làm mờ dần
            setTimeout(() => alert.remove(), 500); // Xóa hẳn sau khi mờ dần
        });
    }, 2000);

    // Kiểm tra và khởi tạo modal Bootstrap
    const cartModal = document.getElementById('cartModal');
    if (cartModal) {
        const modalInstance = new bootstrap.Modal(cartModal);
        document.querySelectorAll('[data-bs-toggle="modal"]').forEach(trigger => {
            trigger.addEventListener('click', function(event) {
                event.preventDefault();
                modalInstance.show();
            });
        });
    }

    const cartOffcanvas = document.getElementById("cartOffcanvas");

    if (cartOffcanvas) {
        const offcanvasInstance = new bootstrap.Offcanvas(cartOffcanvas);

        // Đóng offcanvas khi click bên ngoài
        document.addEventListener("click", function (event) {
            const isClickInside = cartOffcanvas.contains(event.target) || event.target.closest('[data-bs-toggle="offcanvas"]');
            if (!isClickInside && cartOffcanvas.classList.contains("show")) {
                offcanvasInstance.hide();
            }
        });

        // Xóa backdrop ngay khi modal đóng
        cartOffcanvas.addEventListener("hidden.bs.offcanvas", function () {
            setTimeout(() => {
                document.querySelectorAll(".offcanvas-backdrop").forEach(backdrop => backdrop.remove());
                document.body.classList.remove("offcanvas-backdrop", "show", "modal-open");
            }, 10); // Đợi một chút để Bootstrap hoàn tất đóng modal
        });
    }
});
