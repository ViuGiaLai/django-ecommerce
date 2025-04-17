from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import favorites_view, add_to_favorites
from .views import add_to_cart  # Ensure the view is imported
from .views import update_cart_item  # Ensure this import exists

urlpatterns = [
    path('', views.home, name='home'),
    path('san-pham/', views.san_pham, name='san_pham'),
    path('giay-dep/', views.giay_dep, name='giay_dep'),
    path('tui-vi/', views.tui_vi, name='tui_vi'),
    path('phu-kien/', views.phu_kien, name='phu_kien'),
    path('giam-gia/', views.giam_gia, name='giam_gia'),
    path('about/', views.about, name='about'),
    path('san-pham/<slug:slug>/', views.product_detail, name='product_detail'),
    path('view-cart/', views.view_cart, name='view_cart'),
    path('cart/add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),  # Keep only this cart URL
    path('update-cart/<int:item_id>/', views.update_cart_item, name='update_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('delete-cart-item/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('order-success/<str:order_number>/', views.order_success, name='order_success'),  # Updated to use order_number
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/<str:order_number>/', views.my_order_detail, name='my_order_detail'),
    path('my-orders/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='app/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),
    # yêu thích
    path('favorites/', favorites_view, name='favorites'),
    path('add-to-favorites/<slug:slug>/', add_to_favorites, name='add_to_favorites'),
    path('remove-from-favorites/<slug:slug>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites/add/<slug:slug>/', add_to_favorites, name='add_to_favorites'),  # Ensure this line exists
    path('profile/', views.profile_view, name='profile'),
    path('search/', views.search_products, name='search_products'),
    # thêm sửa xóa địa chỉ
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('all-items/', views.all_items, name='all_items'),
    path('add-comment/<slug:slug>/', views.add_comment, name='add_comment'),
    path('validate-promo/', views.validate_promo, name='validate_promo'),
    path('set-csrf/', views.set_csrf_token, name='set_csrf'),
    path('social-login/', views.social_login, name='social_login'),
    path('my-orders/<str:order_number>/update-status/', views.update_order_status, name='update_order_status'),
    path('review-order/<str:order_number>/', views.review_order, name='review_order'),
    path('rebuy-order/<str:order_number>/', views.rebuy_order, name='rebuy_order'),
    path('get-address/<int:address_id>/', views.get_address, name='get_address'),
]
