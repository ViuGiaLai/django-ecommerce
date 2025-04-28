# ecommerce/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product, Slide, CartItem, Category, Profile, Brand, InstagramPost, Comment, Order, OrderItem, DiscountCode, Coupon, Color, Size, CommentImage
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
# login
from .models import RecentlyViewedProduct,Favorite
from .forms import ProfileUpdateForm
# thêm sửa xóa địa chỉ
from .models import Address
from .forms import AddressForm

from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, CustomAuthenticationForm

from django.db.models import Q
import logging
from django.utils import timezone
from django.views.decorators.http import require_POST
import json
from datetime import date
import requests
import random
from django.conf import settings
from django.db import transaction
from django.urls import reverse
import jwt  # Import the PyJWT library for decoding tokens

logger = logging.getLogger(__name__)  # Add this line to define the logger

# Thêm context processor để truyền dữ liệu giỏ hàng vào tất cả các template
def cart_context_processor(request):
    cart_items = []
    cart_items_count = 0
    total_price = 0
    
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        cart_items_count = cart_items.count()
        
        # Tính tổng tiền
        for item in cart_items:
            price = float(item.product.sale_price) if item.product.sale_price else float(item.product.price)
            total_price += item.quantity * price
    
    # Format tổng tiền
    formatted_total = f"{total_price:,.0f}.000" if total_price > 0 else "0.000"
    
    return {
        'cart_items': [{'item': item} for item in cart_items],
        'cart_items_count': cart_items_count,
        'total_price': formatted_total,
        'sizes': ["S", "M", "L", "XL"],  # Add available sizes
    }

def home(request):
    # Get slides
    slides = Slide.objects.filter(is_active=True)
    
    # Get categories that are marked to show on home
    categories = Category.objects.filter(is_active=True, show_on_home=True)
    
    # Get featured products
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    
    # Get new arrivals
    new_arrivals = Product.objects.filter(is_new=True, is_active=True).order_by('-created_at')[:8]
    
    # Get brands
    brands = Brand.objects.filter(is_featured=True)
    
    # Get Instagram posts
    instagram_posts = InstagramPost.objects.all()[:6]
    
    context = {
        'slides': slides,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'brands': brands,
        'instagram_posts': instagram_posts,
    }
    
    return render(request, 'app/home.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Xử lý sản phẩm đã xem gần đây
    if not request.session.get('recently_viewed'):
        request.session['recently_viewed'] = []
    recently_viewed = request.session['recently_viewed']
    
    # Xóa sản phẩm nếu đã tồn tại trong danh sách
    if product.id in recently_viewed:
        recently_viewed.remove(product.id)
    
    # Thêm sản phẩm vào đầu danh sách
    recently_viewed.insert(0, product.id)
    
    # Giới hạn số lượng sản phẩm đã xem
    if len(recently_viewed) > 20:
        recently_viewed = recently_viewed[:20]
    
    request.session['recently_viewed'] = recently_viewed
    request.session.modified = True
    
    comments = Comment.objects.filter(product=product).order_by('-created_at')
    cart_item_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    # Add size list to the context
    sizes = ["S", "M", "L", "XL"]  # Ensure this list is defined
    
    context = {
        'product': product,
        'comments': comments,
        'cart_item_count': cart_item_count,
        'sizes': sizes,  # Pass sizes to the template
    }
    
    return render(request, 'app/product_detail.html', context)

@login_required
@require_POST
def add_to_cart(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
        
        # Parse the request body
        try:
            data = json.loads(request.body)
            quantity = int(data.get("quantity", 1))
            size = data.get("size", "M")
            is_buy_now = data.get("buy_now", False)
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "message": "Dữ liệu không hợp lệ"
            }, status=400)
        
        # Validate quantity
        if quantity < 1:
            return JsonResponse({
                "success": False,
                "message": "Số lượng phải lớn hơn 0"
            }, status=400)
            
        # Check stock availability
        if product.stock < quantity:
            return JsonResponse({
                "success": False,
                "message": f"Chỉ còn {product.stock} sản phẩm trong kho"
            }, status=400)

        with transaction.atomic():
            # If this is a buy now request, clear the cart first
            if is_buy_now:
                CartItem.objects.filter(user=request.user).delete()
                # Create new cart item with exact quantity
                cart_item = CartItem.objects.create(
                    user=request.user,
                    product=product,
                    size=size,
                    quantity=quantity
                )
            else:
                # For regular add to cart, update existing or create new
                try:
                    cart_item = CartItem.objects.select_for_update().get(
                        user=request.user,
                        product=product,
                        size=size
                    )
                    new_quantity = cart_item.quantity + quantity
                    if new_quantity > product.stock:
                        return JsonResponse({
                            "success": False,
                            "message": f"Tổng số lượng trong giỏ ({new_quantity}) vượt quá số lượng trong kho ({product.stock})"
                        }, status=400)
                    cart_item.quantity = new_quantity
                    cart_item.save()
                except CartItem.DoesNotExist:
                    cart_item = CartItem.objects.create(
                        user=request.user,
                        product=product,
                        size=size,
                        quantity=quantity
                    )

        # Verify the quantity was saved correctly
        cart_item.refresh_from_db()
        if cart_item.quantity != quantity and is_buy_now:
            logger.error(f"Quantity mismatch: expected {quantity}, got {cart_item.quantity}")
            cart_item.quantity = quantity
            cart_item.save()

        # Get updated cart count
        cart_count = CartItem.objects.filter(user=request.user).count()

        return JsonResponse({
            "success": True,
            "message": "Sản phẩm đã được thêm vào giỏ hàng!",
            "cart_count": cart_count
        })

    except Product.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Không tìm thấy sản phẩm"
        }, status=404)
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": f"Có lỗi xảy ra: {str(e)}"
        }, status=500)

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_items_with_total = []
    total_price = 0
    
    for item in cart_items:
        # Use sale price if available, otherwise use the original price
        price = float(item.product.sale_price) if item.product.sale_price else float(item.product.price)
        item_total = item.quantity * price
        cart_items_with_total.append({
            'item': item,
            'total': item_total
        })
        total_price += item_total
    
    return render(request, 'app/addcart.html', {
        'cart_items': cart_items_with_total,
        'total_price': total_price,
        'sizes': ["S", "M", "L", "XL"],  # Add available sizes
    })

@login_required
@require_POST
def update_cart_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        data = json.loads(request.body)
        new_quantity = int(data.get("quantity", cart_item.quantity))

        # Validate quantity
        if new_quantity < 1:
            return JsonResponse({
                "success": False,
                "message": "Số lượng phải lớn hơn 0"
            })

        # Check stock availability
        if new_quantity > cart_item.product.stock:
            return JsonResponse({
                "success": False,
                "message": f"Chỉ còn {cart_item.product.stock} sản phẩm trong kho"
            })

        # Update quantity
        cart_item.quantity = new_quantity
        cart_item.save()

        # Recalculate cart totals
        cart_items = CartItem.objects.filter(user=request.user)
        subtotal = 0
        for item in cart_items:
            if item.product.sale_price:
                subtotal += float(item.product.sale_price) * item.quantity * 1000
            else:
                subtotal += float(item.product.price) * item.quantity * 1000

        shipping_fee = 30000  # Fixed shipping fee
        total = subtotal + shipping_fee

        # Format numbers for display
        formatted_subtotal = f"{subtotal:,.0f}"
        formatted_total = f"{total:,.0f}"

        return JsonResponse({
            "success": True,
            "message": "Cập nhật số lượng thành công",
            "subtotal": formatted_subtotal,
            "total": formatted_total
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Không tìm thấy sản phẩm trong giỏ hàng"
        })
    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": f"Có lỗi xảy ra: {str(e)}"
        })

@login_required
@require_POST
def delete_cart_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.delete()
        
        # Get updated cart count
        cart_items_count = CartItem.objects.filter(user=request.user).count()
        
        # Calculate new total price
        cart_items = CartItem.objects.filter(user=request.user)
        total_price = 0
        for item in cart_items:
            if item.product.sale_price:
                total_price += float(item.product.sale_price) * item.quantity
            else:
                total_price += float(item.product.price) * item.quantity
        
        return JsonResponse({
            "success": True, 
            "message": "Sản phẩm đã được xóa khỏi giỏ hàng",
            "cart_count": cart_items_count,
            "total_price": f"{total_price:,.0f}"
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            "success": False, 
            "message": "Không tìm thấy sản phẩm trong giỏ hàng"
        })
    except Exception as e:
        logger.error(f"Error deleting cart item: {str(e)}")
        return JsonResponse({
            "success": False, 
            "message": "Có lỗi xảy ra khi xóa sản phẩm"
        })

# View để thiết lập CSRF cookie
@ensure_csrf_cookie
def set_csrf_token(request):
    return HttpResponse("CSRF cookie set")


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, 'Giỏ hàng của bạn đang trống')
        return redirect('cart')
        
    # Calculate cart total
    cart_total = 0
    cart_items_list = []
    
    for cart_item in cart_items:
        if cart_item.product.sale_price:
            item_price = float(cart_item.product.sale_price)
            item_total = item_price * cart_item.quantity * 1000
        else:
            item_price = float(cart_item.product.price)
            item_total = item_price * cart_item.quantity * 1000
            
        cart_total += item_total
        cart_items_list.append({
            'item': cart_item,
            'total': item_total,
            'unit_price': item_price
        })
    
    shipping_fee = 30000  # Fixed shipping fee
    total_with_shipping = cart_total + shipping_fee
    
    context = {
        'cart_items': cart_items_list,
        'cart_total': cart_total,
        'shipping_fee': shipping_fee,
        'total_with_shipping': total_with_shipping,
    }
    
    return render(request, 'app/checkout.html', context)

@login_required
@require_POST
def cancel_order(request, order_number):
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Chỉ cho phép hủy đơn hàng ở trạng thái "pending" hoặc "processing"
        if order.status not in ['pending', 'processing']:
            return JsonResponse({
                'success': False,
                'message': 'Không thể hủy đơn hàng ở trạng thái này'
            })
        
        # Cập nhật trạng thái đơn hàng
        order.status = 'cancelled'
        order.save()
        
        # Hoàn lại số lượng sản phẩm vào kho
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
            
        # Xóa đơn hàng khỏi danh sách hiển thị
        order.is_deleted = True
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đơn hàng đã được hủy thành công',
            'redirect': '/my-orders/'  # Thêm redirect URL
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Không tìm thấy đơn hàng'
        })
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi hủy đơn hàng'
        })

@login_required
@require_POST  # Ensure only POST requests are accepted
def process_checkout(request):
    try:
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        province = request.POST.get('province')
        district = request.POST.get('district')
        ward = request.POST.get('ward')
        payment_method = request.POST.get('payment_method')
        province_name = request.POST.get('province_name')
        district_name = request.POST.get('district_name')
        ward_name = request.POST.get('ward_name')

        # Validate required fields
        required_fields = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'address': address,
            'province': province,
            'district': district,
            'ward': ward,
            'payment_method': payment_method
        }

        for field_name, value in required_fields.items():
            if not value or not str(value).strip():
                return JsonResponse({
                    'success': False,
                    'message': f'Vui lòng điền đầy đủ thông tin: {field_name}'
                })

        # Get cart items
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Giỏ hàng của bạn đang trống'
            })

        # Calculate totals
        subtotal = sum(
            float(item.product.sale_price or item.product.price) * item.quantity * 1000 
            for item in cart_items
        )
        shipping_fee = 30000  # Fixed shipping fee
        discount = 0

        # Apply discount if promo code exists and is valid
        promo_code = request.POST.get('promo_code')
        if promo_code:
            try:
                discount_obj = DiscountCode.objects.get(code__iexact=promo_code)
                today = timezone.now().date()
                
                # Check if promo code is valid
                if not discount_obj.start_date <= today <= discount_obj.end_date:
                    return JsonResponse({
                        'success': False,
                        'message': 'Mã giảm giá đã hết hạn.'
                    })
                    
                # Calculate discount
                if discount_obj.discount_percentage:
                    discount = subtotal * (float(discount_obj.discount_percentage) / 100)
                elif discount_obj.discount_amount:
                    discount = float(discount_obj.discount_amount) * 1000
                    
            except DiscountCode.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Mã giảm giá không hợp lệ.'
                })

        # Calculate total
        total = subtotal + shipping_fee - discount

        # Validate payment method specific requirements
        if payment_method == 'bank':
            bank_name = request.POST.get('bank_name')
            bank_bin = request.POST.get('bank_bin')
            if not bank_name or not bank_bin:
                return JsonResponse({
                    'success': False,
                    'message': 'Vui lòng chọn ngân hàng'
                })

        # Create order with transaction
        try:
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    province=province_name,
                    district=district_name,
                    ward=ward_name,
                    payment_method=payment_method,
                    subtotal=subtotal,
                    shipping_fee=shipping_fee,
                    discount=discount,
                    total=total,
                    promo_code=promo_code if promo_code else None
                )

                # Add bank information if bank payment is selected
                if payment_method == 'bank':
                    bank_name = request.POST.get('bank_name')
                    bank_bin = request.POST.get('bank_bin')
                    order.bank_name = bank_name
                    order.bank_bin = bank_bin
                    order.save()

                # Create order items and update stock
                for cart_item in cart_items:
                    # Check stock availability
                    if cart_item.quantity > cart_item.product.stock:
                        raise ValueError(f'Sản phẩm {cart_item.product.name} không đủ số lượng trong kho')

                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.sale_price if cart_item.product.sale_price else cart_item.product.price,
                        size=cart_item.size,
                        color=cart_item.color if hasattr(cart_item, 'color') else None
                    )

                    # Update product stock
                    product = cart_item.product
                    product.stock -= cart_item.quantity
                    product.sold_quantity += cart_item.quantity
                    product.save()

                # Clear cart
                cart_items.delete()

                return JsonResponse({
                    'success': True,
                    'message': 'Đặt hàng thành công!',
                    'redirect_url': reverse('order_success', args=[order.order_number])
                })

        except ValueError as ve:
            return JsonResponse({
                'success': False,
                'message': str(ve)
            })
        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Có lỗi xảy ra khi xử lý đơn hàng. Vui lòng thử lại sau.'
            })

    except Exception as e:
        logger.error(f"Unexpected error in checkout: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra. Vui lòng thử lại sau.'
        })

@login_required
def my_orders(request):
    status = request.GET.get('status')
    search_query = request.GET.get('search')
    
    # Get all orders except cancelled ones by default
    orders = Order.objects.filter(user=request.user).exclude(status='cancelled').order_by('-created_at')
    
    # If status is specifically requested, show those orders
    if status:
        orders = Order.objects.filter(user=request.user, status=status).order_by('-created_at')
    
    if search_query:
        orders = orders.filter(Q(id__icontains=search_query) | Q(order_number__icontains=search_query))
    
    # Calculate total for each order
    for order in orders:
        order.calculated_total = float(order.subtotal) + float(order.shipping_fee) - float(order.discount)
    
    context = {
        'orders': orders,
        'current_status': status,
        'search_query': search_query
    }
    return render(request, 'app/my_orders.html', context)

def format_address(address, ward, district, province):
    parts = []
    if address and address.strip():
        parts.append(address.strip())
    if ward and ward.strip():
        parts.append(ward.strip())
    if district and district.strip():
        parts.append(district.strip())
    if province and province.strip():
        parts.append(province.strip())
    return ", ".join(filter(None, parts))

@login_required
def my_order_detail(request, order_number):
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Fetch address details using API
        province_name = district_name = ward_name = None
        try:
            if order.province:
                province_response = requests.get(f"https://provinces.open-api.vn/api/p/{order.province}")
                if province_response.status_code == 200:
                    province_data = province_response.json()
                    province_name = province_data.get('name', order.province)

            if order.district:
                district_response = requests.get(f"https://provinces.open-api.vn/api/d/{order.district}")
                if district_response.status_code == 200:
                    district_data = district_response.json()
                    district_name = district_data.get('name', order.district)

            if order.ward:
                ward_response = requests.get(f"https://provinces.open-api.vn/api/w/{order.ward}")
                if ward_response.status_code == 200:
                    ward_data = ward_response.json()
                    ward_name = ward_data.get('name', order.ward)
        except Exception as e:
            logger.error(f"Error fetching address details: {e}")
            province_name = order.province
            district_name = order.district
            ward_name = order.ward

        # Format full address
        full_address = format_address(order.address, ward_name, district_name, province_name)

        # Calculate total
        total = float(order.subtotal) + float(order.shipping_fee) - float(order.discount)

        context = {
            'order': order,
            'province_name': province_name,
            'district_name': district_name,
            'ward_name': ward_name,
            'total': total,
            'full_address': full_address
        }
        return render(request, 'app/my_order_detail.html', context)
    except Order.DoesNotExist:
        raise Http404("Order not found")

@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Fetch address details using API
    province_name = district_name = ward_name = None
    try:
        if order.province:
            province_response = requests.get(f"https://provinces.open-api.vn/api/p/{order.province}")
            if province_response.status_code == 200:
                province_name = province_response.json().get('name')

        if order.district:
            district_response = requests.get(f"https://provinces.open-api.vn/api/d/{order.district}")
            if district_response.status_code == 200:
                district_name = district_response.json().get('name')

        if order.ward:
            ward_response = requests.get(f"https://provinces.open-api.vn/api/w/{order.ward}")
            if ward_response.status_code == 200:
                ward_name = ward_response.json().get('name')
    except Exception as e:
        logger.error(f"Error fetching address details: {e}")

    # Calculate total
    order.calculated_total = float(order.subtotal) + float(order.shipping_fee) - float(order.discount)

    # Pass the resolved names to the template
    context = {
        'order': order,
        'province_name': province_name or order.province,
        'district_name': district_name or order.district,
        'ward_name': ward_name or order.ward,
    }
    return render(request, 'app/order_success.html', context)

def san_pham(request):
    query = request.GET.get('q', '')
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')  # Default max price
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Start with all products
    products = Product.objects.filter(is_active=True)

    if query:
        products = products.filter(name__icontains=query)

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    # Apply price filter
    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Get all categories and colors from database
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    # Prepare selected filter tags
    filter_tags = []
    
    # Add search query tag if present
    if query:
        filter_tags.append({
            'type': 'search',
            'value': query,
            'display': f'Tìm kiếm: {query}'
        })
    
    # Add category tags
    if selected_categories:
        category_names = Category.objects.filter(id__in=selected_categories).values_list('name', flat=True)
        for cat_name in category_names:
            filter_tags.append({
                'type': 'category',
                'value': cat_name,
                'display': cat_name
            })
    
    # Add color tags
    if selected_colors:
        for color in selected_colors:
            filter_tags.append({
                'type': 'color',
                'value': color,
                'display': color
            })

    # Add size tags
    if selected_sizes:
        for size in selected_sizes:
            filter_tags.append({
                'type': 'size',
                'value': size,
                'display': size
            })

    # Add price range tag if filtered
    if min_price or max_price != '3000000':
        price_display = f"Giá: {int(float(min_price or 0)):,}đ - {int(float(max_price)):,}đ"
        filter_tags.append({
            'type': 'price',
            'value': f"{min_price}-{max_price}",
            'display': price_display
        })

    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0

    context = {
        'products': products,
        'categories': categories,
        'selected_categories': selected_categories,
        'min_price': min_price,
        'max_price': max_price,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'sort_by': sort_by,
        'view_mode': view_mode,
        'colors': colors,
        'sizes': sizes,
        'filter_tags': filter_tags,
        'cart_items_count': cart_items_count,
        'query': query
    }

    return render(request, 'app/all_items.html', context)

def giay_dep(request):
    subcategory = request.GET.get('subcategory', '')
    products = Product.objects.filter(category__name="Giày dép", is_active=True)
    
    if subcategory:
        products = products.filter(name__icontains=subcategory)
    
    # Get filter parameters
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    # Get all categories and colors
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    # Prepare filter tags
    filter_tags = []
    if subcategory:
        filter_tags.append({
            'type': 'subcategory',
            'value': subcategory,
            'display': subcategory
        })

    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    context = {
        'products': products,
        'cart_items_count': cart_items_count,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'filter_tags': filter_tags,
        'view_mode': view_mode,
        'sort_by': sort_by,
        'selected_categories': selected_categories,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'app/all_items.html', context)

def tui_vi(request):
    subcategory = request.GET.get('subcategory', '')
    products = Product.objects.filter(category__name="Túi ví", is_active=True)
    
    if subcategory:
        products = products.filter(name__icontains=subcategory)
    
    # Get filter parameters
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    # Get all categories and colors
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    # Prepare filter tags
    filter_tags = []
    if subcategory:
        filter_tags.append({
            'type': 'subcategory',
            'value': subcategory,
            'display': subcategory
        })

    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    context = {
        'products': products,
        'cart_items_count': cart_items_count,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'filter_tags': filter_tags,
        'view_mode': view_mode,
        'sort_by': sort_by,
        'selected_categories': selected_categories,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'app/all_items.html', context)

def phu_kien(request):
    subcategory = request.GET.get('subcategory', '')
    products = Product.objects.filter(category__name="Phụ kiện", is_active=True)
    
    if subcategory:
        products = products.filter(name__icontains=subcategory)
    
    # Get filter parameters
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    # Get all categories and colors
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    # Prepare filter tags
    filter_tags = []
    if subcategory:
        filter_tags.append({
            'type': 'subcategory',
            'value': subcategory,
            'display': subcategory
        })

    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    context = {
        'products': products,
        'cart_items_count': cart_items_count,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'filter_tags': filter_tags,
        'view_mode': view_mode,
        'sort_by': sort_by,
        'selected_categories': selected_categories,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'app/all_items.html', context)

def giam_gia(request):
    products = Product.objects.filter(is_sale=True, is_active=True)
    
    # Get filter parameters
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    # Get all categories and colors
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    context = {
        'products': products,
        'cart_items_count': cart_items_count,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'view_mode': view_mode,
        'sort_by': sort_by,
        'selected_categories': selected_categories,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'app/all_items.html', context)

def about(request):
    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    return render(request, 'app/about.html', {'cart_items_count': cart_items_count})

# đăng ký
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Đăng ký thành công!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'app/register.html', {'form': form})

# tìm kiếm
def search_products(request):
    query = request.GET.get('q', '')  # Lấy giá trị tìm kiếm từ thanh search
    
    # Get filter parameters
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')  # Default max price
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Start with all products
    products = Product.objects.filter(is_active=True)
    
    # Apply search query if provided
    if query:
        products = products.filter(name__icontains=query)

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    # Apply price filter
    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        products = paginator.page(paginator.num_pages)

    # Get all categories and colors from database
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    # Prepare selected filter tags
    filter_tags = []
    
    # Add search query tag if present
    if query:
        filter_tags.append({
            'type': 'search',
            'value': query,
            'display': f'Tìm kiếm: {query}'
        })
    
    # Add category tags
    if selected_categories:
        category_names = Category.objects.filter(id__in=selected_categories).values_list('name', flat=True)
        for cat_name in category_names:
            filter_tags.append({
                'type': 'category',
                'value': cat_name,
                'display': cat_name
            })
    
    # Add color tags
    if selected_colors:
        for color in selected_colors:
            filter_tags.append({
                'type': 'color',
                'value': color,
                'display': color
            })

    # Add size tags
    if selected_sizes:
        for size in selected_sizes:
            filter_tags.append({
                'type': 'size',
                'value': size,
                'display': size
            })

    # Add price range tag if filtered
    if min_price or max_price != '3000000':
        price_display = f"Giá: {int(float(min_price or 0)):,}đ - {int(float(max_price)):,}đ"
        filter_tags.append({
            'type': 'price',
            'value': f"{min_price}-{max_price}",
            'display': price_display
        })

    context = {
        'query': query,
        'products': products,
        'categories': categories,
        'selected_categories': selected_categories,
        'min_price': min_price,
        'max_price': max_price,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'sort_by': sort_by,
        'view_mode': view_mode,
        'colors': colors,
        'sizes': sizes,
        'filter_tags': filter_tags,
        'is_search': True,
    }
    return render(request, 'app/all_items.html', context)

@login_required
@require_POST
def add_comment(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
        rating = int(request.POST.get('rating', 0))
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng nhập nội dung bình luận!'
            })
            
        if rating < 1 or rating > 5:
            return JsonResponse({
                'success': False,
                'message': 'Đánh giá không hợp lệ!'
            })
            
        # Tạo bình luận mới
        comment = Comment.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            content=content
        )
        
        # Xử lý nhiều hình ảnh
        images = request.FILES.getlist('images[]')
        for image in images:
            CommentImage.objects.create(
                comment=comment,
                image=image
            )
        
        # Cập nhật đánh giá trung bình của sản phẩm
        product.review_count += 1
        if rating == 1:
            product.review_count_1 += 1
        elif rating == 2:
            product.review_count_2 += 1
        elif rating == 3:
            product.review_count_3 += 1
        elif rating == 4:
            product.review_count_4 += 1
        elif rating == 5:
            product.review_count_5 += 1
            
        # Tính lại đánh giá trung bình
        total_rating = (
            product.review_count_1 * 1 +
            product.review_count_2 * 2 +
            product.review_count_3 * 3 +
            product.review_count_4 * 4 +
            product.review_count_5 * 5
        )
        product.rating = total_rating / product.review_count
        product.save()
        
        # Trả về thông tin đánh giá mới để cập nhật UI
        comment_data = {
            'id': comment.id,
            'user': {
                'username': comment.user.username,
                'avatar': comment.user.profile.image.url if hasattr(comment.user, 'profile') and comment.user.profile.image else '/static/images/No_images.png'
            },
            'rating': rating,
            'content': content,
            'created_at': comment.created_at.strftime('%d/%m/%Y'),
            'images': [image.image.url for image in comment.images.all()]
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Cảm ơn bạn đã đánh giá sản phẩm!',
            'comment': comment_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })

@csrf_exempt
@require_POST
def validate_promo(request):
    try:
        data = json.loads(request.body)
        promo_code = data.get('promo_code', '').strip().upper()
        
        if not promo_code:
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng nhập mã giảm giá'
            })
            
        try:
            # Try to find the code in both Coupon and DiscountCode models
            try:
                discount = Coupon.objects.get(code__iexact=promo_code, active=True)
                discount_percent = discount.discount
                discount_amount = None
            except Coupon.DoesNotExist:
                try:
                    discount = DiscountCode.objects.get(code__iexact=promo_code)
                    discount_percent = discount.discount_percentage
                    discount_amount = discount.discount_amount
                except DiscountCode.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Mã giảm giá không hợp lệ'
                    })

            # Check validity period
            today = timezone.now()
            if hasattr(discount, 'valid_from') and hasattr(discount, 'valid_to'):
                if not (discount.valid_from <= today <= discount.valid_to):
                    return JsonResponse({
                        'success': False,
                        'message': 'Mã giảm giá đã hết hạn'
                    })
            elif hasattr(discount, 'start_date') and hasattr(discount, 'end_date'):
                if not (discount.start_date <= today.date() <= discount.end_date):
                    return JsonResponse({
                        'success': False,
                        'message': 'Mã giảm giá đã hết hạn'
                    })
            
            # Get cart total
            cart_items = CartItem.objects.filter(user=request.user)
            subtotal = sum(item.quantity * float(item.product.price) for item in cart_items)
            
            # Calculate discount
            if discount_percent:
                discount_value = float(subtotal) * (float(discount_percent) / 100)
            elif discount_amount:
                discount_value = float(discount_amount)
            else:
                discount_value = 0
                
            shipping_fee = 30000  # Fixed shipping fee
            new_total = float(subtotal) + shipping_fee - discount_value
            
            return JsonResponse({
                'success': True,
                'subtotal': subtotal,
                'discount_amount': discount_value,
                'shipping_fee': shipping_fee,
                'new_total': new_total,
                'message': 'Áp dụng mã giảm giá thành công!'
            })
            
        except (Coupon.DoesNotExist, DiscountCode.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Mã giảm giá không hợp lệ'
            })
            
    except Exception as e:
        print(f"Error in validate_promo: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })

logger = logging.getLogger(__name__)

# your_app/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.conf import settings

logger = logging.getLogger(__name__)

@csrf_exempt
def social_login(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        uid = data.get('uid')
        email = data.get('email')
        display_name = data.get('displayName')
        photo_url = data.get('photoURL')

        if not (uid and email):
            return JsonResponse({'success': False, 'message': 'Missing required fields (uid or email)'}, status=400)

        username = email  # Dùng email làm username

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None
                )
                if display_name:
                    names = display_name.split(' ')
                    user.first_name = names[0] if names else ''
                    user.last_name = names[-1] if len(names) > 1 else ''
                user.save()
            except IntegrityError:
                return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        return JsonResponse({'success': True, 'message': 'Login successful'})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500)

def all_items(request):
    # Get filter parameters
    selected_categories = request.GET.getlist('category', [])
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '3000000')  # Default max price
    selected_colors = request.GET.getlist('color', [])
    selected_sizes = request.GET.getlist('size', [])
    sort_by = request.GET.get('sort', 'newest')
    view_mode = request.GET.get('view', 'grid')

    # Start with all products
    products = Product.objects.filter(is_active=True)

    # Apply filters
    if selected_categories:
        products = products.filter(category_id__in=selected_categories)

    # Apply price filter
    if min_price:
        try:
            min_price_value = float(min_price)
            products = products.filter(price__gte=min_price_value)
        except ValueError:
            pass

    if max_price:
        try:
            max_price_value = float(max_price)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass

    if selected_colors:
        products = products.filter(colors__name__in=selected_colors)

    if selected_sizes:
        products = products.filter(size__name__in=selected_sizes)

    # Apply sorting
    if sort_by == 'price-asc':
        products = products.order_by('price')
    elif sort_by == 'price-desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    else:  # newest
        products = products.order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        products = paginator.page(paginator.num_pages)

    # Get all categories and colors from database
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.values_list('name', flat=True)

    # Prepare selected filter tags
    filter_tags = []
    
    # Add category tags
    if selected_categories:
        category_names = Category.objects.filter(id__in=selected_categories).values_list('name', flat=True)
        for cat_name in category_names:
            filter_tags.append({
                'type': 'category',
                'value': cat_name,
                'display': cat_name
            })
    
    # Add color tags
    if selected_colors:
        for color in selected_colors:
            filter_tags.append({
                'type': 'color',
                'value': color,
                'display': color
            })

    # Add size tags
    if selected_sizes:
        for size in selected_sizes:
            filter_tags.append({
                'type': 'size',
                'value': size,
                'display': size
            })

    # Add price range tag if filtered
    if min_price or max_price != '3000000':
        price_display = f"Giá: {int(float(min_price or 0)):,}đ - {int(float(max_price)):,}đ"
        filter_tags.append({
            'type': 'price',
            'value': f"{min_price}-{max_price}",
            'display': price_display
        })

    context = {
        'products': products,
        'categories': categories,
        'selected_categories': selected_categories,
        'min_price': min_price,
        'max_price': max_price,
        'selected_colors': selected_colors,
        'selected_sizes': selected_sizes,
        'sort_by': sort_by,
        'view_mode': view_mode,
        'colors': colors,
        'sizes': sizes,
        'filter_tags': filter_tags,
    }
    return render(request, 'app/all_items.html', context)

# Trang cá nhân
@login_required
def profile_view(request):
    user = request.user
    # Ensure Profile exists
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect('profile')
        else:
            # Log form errors for debugging
            print(profile_form.errors)
            messages.error(request, "Có lỗi xảy ra, vui lòng kiểm tra lại.")
    else:
        profile_form = ProfileUpdateForm(instance=profile)

    # Get user's orders excluding cancelled ones
    orders = Order.objects.filter(user=user).exclude(status='cancelled').order_by('-created_at')
    
    # Calculate total for each order
    for order in orders:
        order.calculated_total = float(order.subtotal) + float(order.shipping_fee) - float(order.discount)

    favorites = Favorite.objects.filter(user=user)
    recently_viewed = RecentlyViewedProduct.objects.filter(user=user).select_related('product').order_by('-viewed_at')[:10]
    addresses = Address.objects.filter(user=user)  # Get addresses for the logged-in user
    address_form = AddressForm()  # Initialize an empty address form

    context = {
        'profile_form': profile_form,
        'favorites': favorites,
        'recently_viewed': recently_viewed,
        'addresses': addresses,  # Add addresses to the context
        'address_form': address_form,  # Add address form to the context
        'orders': orders,  # Add orders to the context
    }
    return render(request, 'app/profile.html', context)

# yêu thích
@login_required
@require_POST
def add_to_favorites(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if created:
            message = "Sản phẩm đã được thêm vào danh sách yêu thích!"
        else:
            message = "Sản phẩm đã có trong danh sách yêu thích!"
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'})

@login_required
def remove_from_favorites(request, slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        Favorite.objects.filter(user=request.user, product=product).delete()
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa khỏi danh sách yêu thích'
        })
    return JsonResponse({
        'success': False,
        'message': 'Phương thức không được hỗ trợ'
    })

@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    
    # Lấy sản phẩm đã xem gần đây từ session
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = []
    if recently_viewed_ids:
        recently_viewed = Product.objects.filter(id__in=recently_viewed_ids[:8])
        # Sắp xếp theo thứ tự trong session
        recently_viewed = sorted(
            recently_viewed,
            key=lambda x: recently_viewed_ids.index(x.id)
        )
    
    context = {
        'favorites': favorites,
        'recently_viewed': recently_viewed
    }
    return render(request, 'app/favorites.html', context)

# thêm sửa xóa địa chỉ
@login_required
@require_POST
def add_address(request):
    try:
        # Get form data
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        street_address = request.POST.get('street_address')
        province = request.POST.get('province')
        district = request.POST.get('district')
        ward = request.POST.get('ward')

        # Validate required fields
        if not all([full_name, phone, street_address, province, district, ward]):
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng điền đầy đủ thông tin địa chỉ'
            })

        # Create new address
        address = Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            street_address=street_address,
            province=province,
            district=district,
            ward=ward
        )

        # If this is the first address, make it default
        if Address.objects.filter(user=request.user).count() == 1:
            address.is_default = True
            address.save()

        return JsonResponse({
            'success': True,
            'message': 'Thêm địa chỉ mới thành công!',
            'address': {
                'id': address.id,
                'full_name': address.full_name,
                'phone': address.phone,
                'street_address': address.street_address,
                'province': address.province,
                'district': address.district,
                'ward': address.ward,
                'is_default': address.is_default
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'GET':
        return JsonResponse({
            'full_name': address.full_name,
            'phone': address.phone,
            'street_address': address.street_address,
            'province': address.province,
            'district': address.district,
            'ward': address.ward
        })
    
    elif request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            street_address = request.POST.get('street_address')
            province = request.POST.get('province')
            district = request.POST.get('district')
            ward = request.POST.get('ward')

            # Validate required fields
            if not all([full_name, phone, street_address, province, district, ward]):
                return JsonResponse({
                    'success': False,
                    'message': 'Vui lòng điền đầy đủ thông tin địa chỉ'
                })

            # Update address
            address.full_name = full_name
            address.phone = phone
            address.street_address = street_address
            address.province = province
            address.district = district
            address.ward = ward
            address.save()

            return JsonResponse({
                'success': True,
                'message': 'Cập nhật địa chỉ thành công!',
                'address': {
                    'id': address.id,
                    'full_name': address.full_name,
                    'phone': address.phone,
                    'street_address': address.street_address,
                    'province': address.province,
                    'district': address.district,
                    'ward': address.ward,
                    'is_default': address.is_default
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })

@login_required
@require_POST
def delete_address(request, address_id):
    try:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.delete()
        return JsonResponse({
            'success': True,
            'message': 'Xóa địa chỉ thành công!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })

def category_detail(request, category_id):
    """
    View to display products from a specific category
    """
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_active=True)
    
    # Get cart items count for the user if authenticated
    cart_items_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    context = {
        'category': category,
        'products': products,
        'cart_items_count': cart_items_count,
    }
    return render(request, 'app/category_detail.html', context)

@login_required
def update_order_status(request, order_number):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, order_number=order_number)
            new_status = request.POST.get('status')
            
            # Validate the status transition
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered']
            current_status_index = valid_statuses.index(order.status)
            new_status_index = valid_statuses.index(new_status)
            
            # Only allow moving to the next status
            if new_status_index != current_status_index + 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Không thể chuyển sang trạng thái này'
                })
            
            # Update the status
            order.status = new_status
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cập nhật trạng thái đơn hàng thành công'
            })
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Không tìm thấy đơn hàng'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    return JsonResponse({
        'success': False,
        'message': 'Phương thức không được hỗ trợ'
    })

@login_required
@require_POST
def review_order(request, order_number):
    try:
        data = json.loads(request.body)
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        if order.status != 'delivered':
            return JsonResponse({
                'success': False,
                'message': 'Chỉ có thể đánh giá đơn hàng đã giao'
            })
            
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        if not rating or not (1 <= int(rating) <= 5):
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng chọn số sao đánh giá (1-5)'
            })
            
        # Lưu đánh giá cho từng sản phẩm trong đơn hàng
        for order_item in order.items.all():
            Comment.objects.create(
                user=request.user,
                product=order_item.product,
                rating=int(rating),
                content=comment
            )
            
            # Cập nhật đánh giá trung bình của sản phẩm
            product = order_item.product
            product.review_count += 1
            if rating == '1':
                product.review_count_1 += 1
            elif rating == '2':
                product.review_count_2 += 1
            elif rating == '3':
                product.review_count_3 += 1
            elif rating == '4':
                product.review_count_4 += 1
            elif rating == '5':
                product.review_count_5 += 1
                
            # Tính lại đánh giá trung bình
            total_rating = (
                product.review_count_1 * 1 +
                product.review_count_2 * 2 +
                product.review_count_3 * 3 +
                product.review_count_4 * 4 +
                product.review_count_5 * 5
            )
            product.rating = total_rating / product.review_count
            product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cảm ơn bạn đã đánh giá!'
        })
        
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Không tìm thấy đơn hàng'
        })
    except Exception as e:
        logger.error(f"Error reviewing order: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi gửi đánh giá'
        })

@login_required
@require_POST
def rebuy_order(request, order_number):
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Kiểm tra xem có thể mua lại không
        if order.status != 'delivered':
            return JsonResponse({
                'success': False,
                'message': 'Chỉ có thể mua lại đơn hàng đã giao'
            })
            
        # Thêm các sản phẩm vào giỏ hàng
        success_count = 0
        error_messages = []
        
        for order_item in order.items.all():
            try:
                # Kiểm tra tồn kho
                if order_item.product.stock < order_item.quantity:
                    error_messages.append(f"{order_item.product.name}: Không đủ số lượng trong kho")
                    continue
                    
                # Thêm vào giỏ hàng
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user,
                    product=order_item.product,
                    size=order_item.size,
                    defaults={'quantity': order_item.quantity}
                )
                
                if not created:
                    # Nếu sản phẩm đã có trong giỏ, cộng thêm số lượng
                    cart_item.quantity += order_item.quantity
                    if cart_item.quantity > order_item.product.stock:
                        error_messages.append(f"{order_item.product.name}: Tổng số lượng vượt quá hàng tồn kho")
                        continue
                    cart_item.save()
                    
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"{order_item.product.name}: {str(e)}")
                
        if success_count > 0:
            message = "Đã thêm sản phẩm vào giỏ hàng"
            if error_messages:
                message += f". Lưu ý: {', '.join(error_messages)}"
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f"Không thể thêm sản phẩm vào giỏ hàng: {', '.join(error_messages)}"
            })
            
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Không tìm thấy đơn hàng'
        })
    except Exception as e:
        logger.error(f"Error rebuying order: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi thêm vào giỏ hàng'
        })

@login_required
def get_address(request, address_id):
    try:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        return JsonResponse({
            'full_name': address.full_name,
            'phone': address.phone,
            'street_address': address.street_address,
            'province': address.province,
            'district': address.district,
            'ward': address.ward
        })
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Địa chỉ không tồn tại'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def google_signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("token")
            if not token:
                logger.error("Missing token in request body.")
                return JsonResponse({"success": False, "message": "Token không hợp lệ."})

            # Decode the token using PyJWT
            try:
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                email = decoded_token.get("email")
                if not email:
                    logger.error("Email not found in decoded token.")
                    return JsonResponse({"success": False, "message": "Không tìm thấy email trong token."})
            except jwt.DecodeError as e:
                logger.error(f"Token decode error: {str(e)}")
                return JsonResponse({"success": False, "message": "Token không hợp lệ."})

            # Get or create the user
            user, created = User.objects.get_or_create(email=email, defaults={"username": email})
            login(request, user)

            return JsonResponse({"success": True, "redirect_url": "/"})
        except Exception as e:
            logger.error(f"Error in google_signup: {str(e)}")
            return JsonResponse({"success": False, "message": f"Lỗi: {str(e)}"})
    return JsonResponse({"success": False, "message": "Phương thức không được hỗ trợ."})
