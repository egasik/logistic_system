from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Q, Count, Min, Max
from django.core.paginator import Paginator

from .models import Product, Category, CartItem, Order, OrderItem, User, Brand, Profile
from .forms import UserUpdateForm, ProfileUpdateForm

# =============================================================================
# 🏠 ГЛАВНАЯ И КАТАЛОГ
# =============================================================================
def index(request):
    """Главная страница"""
    products = Product.objects.filter(is_active=True)[:8]
    return render(request, 'core/index.html', {'products': products})

def catalog(request):
    """Каталог товаров с фильтрами"""
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    products = Product.objects.filter(is_active=True).select_related('category', 'brand').order_by('-id')
    
    # Фильтр по категории
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    # Фильтр по наличию
    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        products = products.filter(stock__gt=0)
    
    # Фильтр по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    # Пагинация
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    # Сохраняем параметры для пагинации
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    
    return render(request, 'core/catalog.html', {
        'products': products_page,
        'categories': categories,
        'current_category': category_slug,
        'current_in_stock': in_stock,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'current_search': search,
        'query_params': query_params.urlencode(),
    })

def product_detail(request, product_slug):
    """Страница товара"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    image_path = None
    # Keep compatibility with legacy DB where image is a column on core_product.
    with connection.cursor() as cursor:
        cursor.execute("SELECT image FROM core_product WHERE id = %s", [product.id])
        row = cursor.fetchone()
    if row and row[0]:
        image_path = row[0]
    return render(request, 'core/product_detail.html', {'product': product, 'image_path': image_path})

# =============================================================================
# 🛒 КОРЗИНА
# =============================================================================
@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def add_to_cart(request, product_id):
    """Добавить товар в корзину"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f'«{product.name}» добавлен в заявку')
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_item_id):
    """Удалить товар из корзины"""
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    cart_item.delete()
    return redirect('cart')

# =============================================================================
# 📦 ОФОРМЛЕНИЕ ЗАЯВКИ
# =============================================================================
@login_required
def checkout(request):
    """Оформление заявки"""
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items:
        messages.warning(request, 'Заявка пуста')
        return redirect('cart')
    
    if request.method == 'POST':
        total = sum(item.product.price * item.quantity for item in cart_items)
        try:
            with transaction.atomic():
                # Создаём заказ
                order = Order.objects.create(
                    user=request.user,
                    customer_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                    phone=request.user.phone or '',
                    email=request.user.email,
                    address=request.user.address or '',
                    total=total,
                    notes=request.POST.get('notes', '')
                )
                # Создаём позиции заказа и списываем остатки
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        unit_price=item.product.price,
                        quantity=item.quantity
                    )
                    # Списываем со склада
                    if item.product.stock >= item.quantity:
                        item.product.stock -= item.quantity
                        item.product.save()
                    else:
                        raise ValueError(f'Недостаточно товара «{item.product.name}» на складе')
                # Очищаем корзину
                cart_items.delete()
            messages.success(request, f'✅ Заявка #{order.id} успешно оформлена!')
            return redirect('order_success', order_id=order.id)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'core/checkout.html', {'cart_items': cart_items, 'total': total})

@login_required
def order_success(request, order_id):
    """Страница успеха после оформления"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_success.html', {'order': order})

# =============================================================================
# 👤 ЛИЧНЫЙ КАБИНЕТ
# =============================================================================
@login_required
def profile_view(request):
    """Профиль пользователя"""
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '✅ Профиль обновлён!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Последние 5 заказов для отображения в профиле
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'core/profile.html', {
        'u_form': u_form, 
        'p_form': p_form,
        'recent_orders': recent_orders
    })

@login_required
def orders_list(request):
    """История заявок клиента"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Детальная страница заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})

# =============================================================================
# 🔐 АВТОРИЗАЦИЯ
# =============================================================================
def register_view(request):
    """Регистрация"""
    if request.method == 'POST':
        from .forms import UserRegisterForm
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import login
            login(request, user)
            messages.success(request, '✅ Регистрация успешна!')
            return redirect('catalog')
    else:
        from .forms import UserRegisterForm
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    """Вход"""
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('catalog')
    else:
        from django.contrib.auth.forms import AuthenticationForm
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def logout_view(request):
    """Выход"""
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, '👋 Вы вышли из системы')
    return redirect('home')