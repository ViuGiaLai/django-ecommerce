# app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import uuid

class Category(models.Model):
    id = models.BigAutoField(primary_key=True)  # ID tự động tăng
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Thêm dòng này
    show_on_home = models.BooleanField(default=False)  # Thêm trường này
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=7)  # Mã màu, ví dụ như #FFFFFF

    def __str__(self):
        return self.name
class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/')
    sold_quantity = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    colors = models.ManyToManyField(Color, related_name='products', blank=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_sale = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sale_start_time = models.DateTimeField(null=True, blank=True)
    sale_end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    rating = models.FloatField(default=0.0)  # Điểm trung bình đánh giá
    review_count = models.PositiveIntegerField(default=0)  # Tổng số đánh giá
    review_count_1 = models.PositiveIntegerField(default=0)  # Số đánh giá 1 sao
    review_count_2 = models.PositiveIntegerField(default=0)  # Số đánh giá 2 sao
    review_count_3 = models.PositiveIntegerField(default=0)  # Số đánh giá 3 sao
    review_count_4 = models.PositiveIntegerField(default=0)  # Số đánh giá 4 sao
    review_count_5 = models.PositiveIntegerField(default=0)  # Số đánh giá 5 sao

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def display_price(self):
        """Hiển thị giá bán hiện tại với định dạng tiền tệ Việt Nam."""
        if self.sale_price:
            return f"{self.sale_price:,.0f}.000₫"
        return f"{self.price:,.0f}.000₫"

    @property
    def original_price(self):
        """Hiển thị giá gốc nếu có sale, với định dạng tiền tệ."""
        if self.sale_price:
            return f"{self.price:,.0f}.000₫"
        return None
# mã giảm giá

class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)  # Mã giảm giá
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Giảm theo phần trăm
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Giảm theo số tiền cố định
    start_date = models.DateField()  # Ngày bắt đầu áp dụng
    end_date = models.DateField()  # Ngày kết thúc áp dụng

    def __str__(self):
        return self.code
    
 # Đánh dấu thương hiệu nổi bật
class Brand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_featured = models.BooleanField(default=False)  # Đánh dấu thương hiệu nổi bật

    def __str__(self):
        return self.name

# Model để lưu trữ sản phẩm nổi bật
class FeaturedProduct(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    is_featured = models.BooleanField(default=True)

    def __str__(self):
        return f"Featured: {self.product.name}"
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"

class Slide(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='slides/')
    cta = models.CharField(max_length=100, blank=True, null=True)
    cta_link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Thêm dòng này

    def __str__(self):
        return self.title


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total(self):
        """Tính tổng tiền của item trong giỏ hàng"""
        if self.product.sale_price:
            return float(self.product.sale_price) * self.quantity * 1000
        return float(self.product.price) * self.quantity * 1000

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Nam'), ('F', 'Nữ')], default='male')
    image = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Profile"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class RecentlyViewedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100) 
    ward = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.full_name}'s address at {self.street_address}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to non-default
            Address.objects.filter(user=self.user).update(is_default=False)
        elif not Address.objects.filter(user=self.user).exists():
            # If this is the first address, make it default
            self.is_default = True
        super().save(*args, **kwargs)

class InstagramPost(models.Model):
    image = models.ImageField(upload_to='instagram_posts/')  # Để lưu trữ ảnh Instagram
    caption = models.CharField(max_length=255, blank=True, null=True)  # Thêm mô tả cho ảnh
    is_active = models.BooleanField(default=True)  # Trạng thái của ảnh (hiển thị hay không)
    created_at = models.DateTimeField(auto_now_add=True)  # Thời gian tạo bài đăng

    def __str__(self):
        return f"Instagram Post {self.id}"

class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, f'{i} sao') for i in range(1, 6)])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Đánh giá của {self.user.username} cho {self.product.name}'

class CommentImage(models.Model):
    comment = models.ForeignKey(Comment, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='comment_images/')

    def __str__(self):
        return f'Hình ảnh cho đánh giá {self.comment.id}'

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True, blank=True)  # Allow blank for initial creation
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    province = models.CharField(max_length=100)  # Ensure this stores the province name or ID
    district = models.CharField(max_length=100)  # Ensure this stores the district name or ID
    ward = models.CharField(max_length=100)      # Ensure this stores the ward name or ID
    payment_method = models.CharField(max_length=50, choices=[('cod', 'Thanh toán khi nhận hàng'), ('bank', 'Chuyển khoản ngân hàng')])
    bank_name = models.CharField(max_length=255, blank=True, null=True)  # Ensure this stores the bank name
    promo_code = models.CharField(max_length=50, blank=True, null=True)  # Add promo_code field
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=30000)
    discount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add this field if it doesn't exist
    status = models.CharField(max_length=50, choices=[('pending', 'Đang xử lý'), ('processing', 'Đang chuẩn bị hàng'), ('shipped', 'Đang giao hàng'), ('delivered', 'Đã giao hàng'), ('cancelled', 'Đã hủy')], default='pending')

    def save(self, *args, **kwargs):
        if not self.order_number:  # Generate a unique order number if not already set
            self.order_number = str(uuid.uuid4())[:12].replace('-', '').upper()  # Shortened to 12 characters
        # Ensure proper calculation of total
        self.total = self.subtotal + self.shipping_fee - self.discount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=3)
    size = models.CharField(max_length=10)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True)

    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (
            self.active and
            self.valid_from <= now <= self.valid_to and
            self.used_count < self.usage_limit
        )

    def apply_discount(self, total_amount):
        if not self.is_valid():
            return 0

        discount_amount = (total_amount * self.discount) / 100

        if self.min_purchase_amount and total_amount < self.min_purchase_amount:
            return 0

        if self.max_discount_amount and discount_amount > self.max_discount_amount:
            return self.max_discount_amount

        return discount_amount

