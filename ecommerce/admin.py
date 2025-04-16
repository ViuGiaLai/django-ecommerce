from django.contrib import admin
from .models import Category, Product, FeaturedProduct, ProductImage, Slide, CartItem, Color , Brand, InstagramPost, Order, OrderItem, Coupon, Comment, CommentImage
from .models import DiscountCode
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')  # Hiển thị tên màu và mã màu trong danh sách
    search_fields = ('name',)  # Cho phép tìm kiếm theo tên màu
# Đăng ký model Product
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]  # Thêm Inline cho ProductImage
    list_display = ('name', 'category', 'price', 'sale_price', 'is_featured', 'sold_quantity', 'stock', 'is_new', 'is_sale', 'is_active', 'sale_start_time', 'sale_end_time', 'rating', 'created_at', 'updated_at')
    list_filter = ('category', 'is_featured', 'is_new', 'is_sale', 'is_active', 'colors')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    filter_horizontal = ('colors',)
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'description', 'category', 'image', 'colors')
        }),
        ('Giá & Kho', {
            'fields': ('price', 'sale_price', 'stock', 'sold_quantity')
        }),
        ('Trạng thái', {
            'fields': ('is_featured', 'is_new', 'is_sale', 'is_active')
        }),
        ('Thời gian Flash Sale', {
            'fields': ('sale_start_time', 'sale_end_time'),
            'classes': ('collapse',)
        }),
        ('Điểm đánh giá', {
            'fields': ('rating',),
            'classes': ('collapse',)
        }),
    )

# Avoid registering the model multiple times
if not admin.site.is_registered(Product):
    admin.site.register(Product, ProductAdmin)

# Đăng ký model FeaturedProduct
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_featured')
    list_filter = ('is_featured',)

admin.site.register(FeaturedProduct, FeaturedProductAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'show_on_home', 'is_active')
    list_editable = ('show_on_home', 'is_active')
    search_fields = ('name',)
    list_filter = ('show_on_home', 'is_active')

class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'image', 'cta', 'is_active')  # Thêm 'cta' vào list_display
    search_fields = ('title', 'subtitle')

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'size', 'created_at')
    list_filter = ('user', 'product')
    date_hierarchy = 'created_at'

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_featured')  # Hiển thị tên và trạng thái nổi bật
    list_filter = ('is_featured',)
    search_fields = ('name',)
# Định nghĩa admin cho model InstagramPost
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'caption', 'is_active', 'created_at')  # Hiển thị các trường cần thiết
    list_filter = ('is_active',)  # Lọc theo trạng thái kích hoạt
    search_fields = ('caption',)  # Tìm kiếm theo mô tả
    ordering = ('-created_at',)  # Sắp xếp theo thời gian tạo, mới nhất lên đầu

# Đăng ký model InstagramPost vào admin
admin.site.register(InstagramPost, InstagramPostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductImage)
admin.site.register(Slide, SlideAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Brand, BrandAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price', 'size', 'color')
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'full_name', 'total_amount', 'status', 'created_at', 'action_buttons')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('order_number', 'full_name', 'phone', 'email')
    readonly_fields = ('order_number', 'user', 'created_at', 'subtotal', 'shipping_fee', 'discount', 'total')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)

    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('order_number', 'status', 'created_at')
        }),
        ('Thông tin khách hàng', {
            'fields': ('user', 'full_name', 'phone', 'email')
        }),
        ('Địa chỉ giao hàng', {
            'fields': ('address', 'province', 'district', 'ward')
        }),
        ('Thanh toán', {
            'fields': ('payment_method', 'bank_name', 'subtotal', 'shipping_fee', 'discount', 'total')
        }),
    )

    def total_amount(self, obj):
        return format_html('<b style="color: #28a745;">{}₫</b>', '{:,.0f}'.format(obj.total))
    total_amount.short_description = 'Tổng tiền'

    def action_buttons(self, obj):
        buttons = []
        status_transitions = {
            'pending': ('processing', 'Chuẩn bị hàng'),
            'processing': ('shipped', 'Giao hàng'),
            'shipped': ('delivered', 'Đã giao'),
        }

        if obj.status in status_transitions:
            next_status, button_text = status_transitions[obj.status]
            buttons.append(
                f'<a class="button" '
                f'href="{reverse("admin:update_order_status", args=[obj.id, next_status])}" '
                f'style="background-color: #28a745; color: white; padding: 5px 10px; '
                f'border-radius: 4px; text-decoration: none; margin-right: 5px;">'
                f'{button_text}</a>'
            )

        if obj.status not in ['cancelled', 'delivered']:
            buttons.append(
                f'<a class="button" '
                f'href="{reverse("admin:cancel_order", args=[obj.id])}" '
                f'style="background-color: #dc3545; color: white; padding: 5px 10px; '
                f'border-radius: 4px; text-decoration: none;" '
                f'onclick="return confirm(\'Bạn có chắc chắn muốn hủy đơn hàng này?\');">'
                f'Hủy đơn</a>'
            )

        return format_html(''.join(buttons))
    action_buttons.short_description = 'Thao tác'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/update-status/<str:new_status>/',
                 self.admin_site.admin_view(self.update_order_status),
                 name='update_order_status'),
            path('<path:object_id>/cancel/',
                 self.admin_site.admin_view(self.cancel_order),
                 name='cancel_order'),
        ]
        return custom_urls + urls

    def update_order_status(self, request, object_id, new_status):
        order = self.get_object(request, object_id)
        if not order:
            messages.error(request, 'Không tìm thấy đơn hàng.')
            return self.response_post_save_change(request, order)

        valid_transitions = {
            'pending': 'processing',
            'processing': 'shipped',
            'shipped': 'delivered'
        }

        if order.status not in valid_transitions or valid_transitions[order.status] != new_status:
            messages.error(request, 'Không thể chuyển sang trạng thái này.')
            return self.response_post_save_change(request, order)

        order.status = new_status
        order.save()
        messages.success(request, f'Đã cập nhật trạng thái đơn hàng thành {order.get_status_display()}')
        return self.response_post_save_change(request, order)

    def cancel_order(self, request, object_id):
        order = self.get_object(request, object_id)
        if not order:
            messages.error(request, 'Không tìm thấy đơn hàng.')
            return self.response_post_save_change(request, order)

        if order.status in ['cancelled', 'delivered']:
            messages.error(request, 'Không thể hủy đơn hàng này.')
            return self.response_post_save_change(request, order)

        # Hoàn lại số lượng sản phẩm vào kho
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Đã hủy đơn hàng thành công.')
        return self.response_post_save_change(request, order)

    def has_delete_permission(self, request, obj=None):
        return False  # Không cho phép xóa đơn hàng

    def has_add_permission(self, request):
        return False  # Không cho phép thêm đơn hàng thủ công

admin.site.register(OrderItem)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']

class CommentImageInline(admin.TabularInline):
    model = CommentImage
    extra = 1
    readonly_fields = ('image',)
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'content_preview', 'created_at', 'has_images')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('user__username', 'product__name', 'content')
    readonly_fields = ('user', 'product', 'rating', 'content', 'created_at')
    inlines = [CommentImageInline]
    ordering = ('-created_at',)

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Nội dung'

    def has_images(self, obj):
        return obj.images.exists()
    has_images.boolean = True
    has_images.short_description = 'Có hình ảnh'

    def has_add_permission(self, request):
        return False  # Không cho phép thêm đánh giá từ admin

    def has_delete_permission(self, request, obj=None):
        return True  # Cho phép xóa đánh giá không phù hợp

