from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import Q, Sum, Count
from .models import (
    Product, Category, Carrier, CartItem, Order, OrderItem, User, Profile
)
from .forms import CustomUserCreationForm  
from django.contrib.auth.forms import AuthenticationForm


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def is_admin(user):
    return user.is_authenticated and user.is_admin


def handle_avatar_upload(avatar_file, user_id):
    """Сохраняет аватар и возвращает путь относительно media/"""
    if not avatar_file or not hasattr(avatar_file, 'name'):
        return None
    ext = os.path.splitext(avatar_file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return None
    filename = f"avatars/user_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(settings.MEDIA_ROOT, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb+') as destination:
        for chunk in avatar_file.chunks():
            destination.write(chunk)
    return filename


# ==================== ПУБЛИЧНЫЕ СТРАНИЦЫ ====================
def index(request):
    """Главная страница"""
    products = Product.objects.filter(is_active=True, stock__gt=0)[:8]
    categories = Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)
    return render(request, 'core/index.html', {'products': products, 'categories': categories})


def catalog(request):
    """Каталог с фильтрацией и поиском"""
    categories = Category.objects.all()
    carriers = Carrier.objects.all()
    products = Product.objects.filter(is_active=True).select_related('category', 'carrier')
    
    # Поиск
    if search := request.GET.get('q'):
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search) | Q(sku__icontains=search))
    
    # Фильтры
    if cat_slug := request.GET.get('category'):
        products = products.filter(category__slug=cat_slug)
    if carrier_slug := request.GET.get('carrier'):
        products = products.filter(carrier__slug=carrier_slug)
    if min_price := request.GET.get('min_price'):
        products = products.filter(price__gte=min_price)
    if max_price := request.GET.get('max_price'):
        products = products.filter(price__lte=max_price)
    if request.GET.get('in_stock') == 'on':
        products = products.filter(stock__gt=0)
    
    # Сортировка
    sort = request.GET.get('sort', '-created_at')
    if sort in ['price', '-price', 'name', '-name', 'stock', '-stock']:
        products = products.order_by(sort)
    
    return render(request, 'core/catalog.html', {
        'products': products, 'categories': categories, 'carriers': carriers,
        'current_category': request.GET.get('category'),
        'current_carrier': request.GET.get('carrier'),
        'query': request.GET.get('q', ''),
        'sort': sort
    })


def product_detail(request, slug):
    """Карточка товара"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    return render(request, 'core/product_detail.html', {
        'product': product, 'images': images, 'related_products': related
    })


# ==================== КОРЗИНА И ЗАКАЗЫ ====================
@login_required
def cart_view(request):
    """Корзина / черновик заявки"""
    items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(i.get_total_price() for i in items)
    return render(request, 'core/cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, product_id):
    """Добавить товар в корзину"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if product.stock < 1:
        messages.error(request, f'«{product.name}» нет в наличии')
        return redirect('product_detail', slug=product.slug)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created and item.quantity + 1 > product.stock:
        messages.error(request, f'Доступно только {product.stock} ед. «{product.name}»')
        return redirect('cart')
    item.quantity = item.quantity + 1 if not created else 1
    item.save()
    messages.success(request, f'«{product.name}» добавлен в заявку')
    return redirect('cart')


@login_required
def update_cart(request, item_id):
    """Обновить количество в корзине"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        if quantity <= 0:
            item.delete()
        elif quantity <= item.product.stock:
            item.quantity = quantity
            item.save()
        else:
            messages.error(request, f'Доступно только {item.product.stock} ед.')
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    """Удалить товар из корзины"""
    CartItem.objects.filter(id=item_id, user=request.user).delete()
    messages.success(request, 'Товар удалён из заявки')
    return redirect('cart')


@login_required
def checkout(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    if not items:
        return redirect('cart')
    
    if request.method == 'POST':
        # 🔹 Проверка имитации оплаты
        if request.POST.get('payment_confirmed') != '1':
            messages.error(request, 'Подтвердите оплату для оформления заявки')
            return render(request, 'core/checkout.html', {'items': items})
        
        total = sum(i.get_total_price() for i in items)
        try:
            with transaction.atomic():
                # ... существующий код создания заказа ...
                
                # 🔹 Сохраняем телефон/карту из формы в профиль (если изменились)
                user = request.user
                if request.POST.get('phone') and request.POST.get('phone') != user.phone:
                    user.phone = request.POST.get('phone')
                    user.save()
                if request.POST.get('card_number') and request.POST.get('card_number').replace(' ', '') != user.card_number:
                    user.card_number = request.POST.get('card_number').replace(' ', '')
                    user.save()
                
                # ... остальной код ...
        except ValueError as e:
            messages.error(request, str(e))
    
    return render(request, 'core/checkout.html', {'items': items})


@login_required
def order_detail(request, order_id):
    """Детали заказа (для клиента)"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.select_related('product')
    return render(request, 'core/order_detail.html', {'order': order, 'items': items})


@login_required
def my_orders(request):
    """История заказов пользователя"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/orders.html', {'orders': orders})


# ==================== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ====================
@login_required
def profile_view(request):
    """Страница профиля с загрузкой аватара"""
    if request.method == 'POST':
        user = request.user
        # Обновление данных пользователя
        user.name = request.POST.get('name', user.name)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.card_number = request.POST.get('card_number', '').replace(' ', '')  # 🔹 Сохраняем карту
        user.save()
        # Загрузка аватара
        if 'avatar' in request.FILES:
            avatar_path = handle_avatar_upload(request.FILES['avatar'], user.id)
            if avatar_path:
                user.profile.avatar = avatar_path
        
        user.save()
        user.profile.save(update_fields=['avatar'])
        messages.success(request, 'Профиль обновлён')
        return redirect('profile')
    
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:3]
    return render(request, 'core/profile.html', {'recent_orders': recent_orders})


# ==================== АУТЕНТИФИКАЦИЯ ====================
def login_view(request):
    """Вход в систему"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_blocked:
                messages.error(request, 'Ваш аккаунт заблокирован')
                return redirect('login')
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.name or user.email}!')
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('index')


def register_view(request):
    """Страница регистрации"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            user.phone = request.POST.get('phone', '')
            user.save()
            from django.contrib.auth import login
            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать.')
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


# ==================== АДМИН-ФУНКЦИИ (отчёты и управление) ====================
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Панель администратора: статистика"""
    stats = {
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'low_stock': Product.objects.filter(is_active=True, stock__lt=10).count(),
        'total_users': User.objects.filter(is_blocked=False).count(),
        'revenue': Order.objects.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0,
    }
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    low_stock_products = Product.objects.filter(is_active=True, stock__lt=10).select_related('category')[:10]
    return render(request, 'core/admin_dashboard.html', {
        'stats': stats, 'recent_orders': recent_orders, 'low_stock_products': low_stock_products
    })


@user_passes_test(is_admin)
def admin_orders(request):
    """Управление заказами (смена статусов)"""
    status_filter = request.GET.get('status')
    orders = Order.objects.select_related('user').all()
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
    orders = orders.order_by('-created_at')
    return render(request, 'core/admin_orders.html', {'orders': orders, 'current_status': status_filter})


@user_passes_test(is_admin)
def admin_order_update(request, order_id):
    """Обновление статуса заказа (AJAX)"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Статус заявки #{order.id} изменён на «{order.get_status_display()}»')
    return redirect('admin_orders')


@user_passes_test(is_admin)
def admin_products(request):
    """Управление товарами (список)"""
    products = Product.objects.select_related('category', 'carrier').all()
    return render(request, 'core/admin_products.html', {'products': products})


@user_passes_test(is_admin)
def admin_reports(request):
    """Отчёты: продажи, остатки, оборачиваемость"""
    # Продажи по статусам
    orders_by_status = Order.objects.values('status').annotate(
        count=Count('id'), total=Sum('total')
    ).order_by('status')
    
    # Топ товаров по продажам
    top_products = OrderItem.objects.values('product_name').annotate(
        sold=Sum('quantity'), revenue=Sum('unit_price')
    ).order_by('-sold')[:10]
    
    # Остатки по категориям
    stock_by_category = Product.objects.values('category__name').annotate(
        total_stock=Sum('stock')
    ).order_by('-total_stock')
    
    return render(request, 'core/admin_reports.html', {
        'orders_by_status': orders_by_status,
        'top_products': top_products,
        'stock_by_category': stock_by_category
    })