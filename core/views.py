from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test  # ← ДОБАВЛЕНО user_passes_test
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Q, Count, Min, Max, Sum  # ← ДОБАВЛЕНО Sum
from django.core.paginator import Paginator
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Category, CartItem, Order, OrderItem, User, Brand, Profile
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from django.http import HttpResponse
import io


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
    images = product.images.all().order_by('sort_order', 'id')
    
    return render(request, 'core/product_detail.html', {
        'product': product,
        'images': images  # ← Обязательно должно быть!
    })

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
    """Профиль: раздельная обработка аватара и текстовых данных"""
    if request.method == 'POST':
        # 1. Если загружают аватар (отдельная форма в шаблоне)
        if 'avatar' in request.FILES:
            avatar_file = request.FILES['avatar']
            # Используем вашу функцию handle_avatar_upload (она есть в вашем views.py)
            avatar_path = handle_avatar_upload(avatar_file, request.user.id)
            if avatar_path:
                request.user.profile.avatar = avatar_path
                request.user.profile.save()
                messages.success(request, '✅ Аватар успешно обновлён!')
            else:
                messages.error(request, '❌ Неверный формат файла аватара')
            return redirect('profile')
        
        # 2. Если сохраняют текстовые данные профиля
        else:
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.phone = request.POST.get('phone', '').strip()
            request.user.address = request.POST.get('address', '').strip()
            
            # Сохраняем номер карты (убедитесь, что поле card_number есть в модели User)
            if hasattr(request.user, 'card_number'):
                request.user.card_number = request.POST.get('card_number', '').replace(' ', '')
            
            request.user.save()
            messages.success(request, '✅ Данные профиля успешно обновлены!')
            return redirect('profile')
    
    # GET-запрос: просто отображаем страницу (Django сам подставит {{ user.phone }} в шаблон)
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'core/profile.html', {'recent_orders': recent_orders})

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
    """Регистрация с сохранением телефона, имени и адреса (без ошибки username)"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # 1. Простая валидация
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким Email уже существует')
            return redirect('register')
        
        # 2. Создаём объект пользователя напрямую (в обход create_user)
        user = User(
            email=email,
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            address=request.POST.get('address', '').strip()
        )
        
        # 3. Правильно хешируем пароль и сохраняем
        user.set_password(password1)
        user.save()
        
        # 4. Автоматический вход после регистрации
        from django.contrib.auth import login
        login(request, user)
        messages.success(request, '✅ Регистрация успешна! Добро пожаловать.')
        return redirect('catalog')
    
    return render(request, 'core/register.html')

def login_view(request):
    """Вход в систему с проверкой на блокировку"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # 🔹 ПРОВЕРКА НА БЛОКИРОВКУ
            if user.is_blocked:
                messages.error(request, '⛔ Ваш аккаунт заблокирован администрацией. Обратитесь в поддержку.')
                return redirect('login')
            
            # Если всё хорошо, выполняем вход
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.email}!')
            next_url = request.GET.get('next', 'catalog')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
        
    return render(request, 'core/login.html', {'form': form})

@login_required
def logout_view(request):
    """Выход из системы"""
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, '👋 Вы вышли из системы')
    return redirect('index')  # Исправлено с 'home' на 'index' (или 'catalog')


# =============================================================================
# ⚙️ АДМИН-ФУНКЦИИ И ОТЧЁТЫ
# =============================================================================
# =============================================================================
# ⚙️ АДМИН-ФУНКЦИИ И ОТЧЁТЫ
# =============================================================================
def is_admin(user):
    """Проверка: является ли пользователь администратором"""
    return user.is_authenticated and (user.is_admin or user.is_superuser)


@user_passes_test(is_admin)
def admin_dashboard(request):
    """Панель администратора: базовая статистика"""
    stats = {
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'low_stock': Product.objects.filter(is_active=True, stock__lt=10).count(),
        'total_users': User.objects.filter(is_blocked=False).count(),
        'total_revenue': Order.objects.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0,
    }
    
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    low_stock_products = Product.objects.filter(is_active=True, stock__lt=10).select_related('category')[:10]
    
    return render(request, 'core/admin_dashboard.html', {
        'stats': stats, 
        'recent_orders': recent_orders, 
        'low_stock_products': low_stock_products
    })


@user_passes_test(is_admin)
def admin_reports(request):
    """Генерация отчётов по совершённым заказам"""
    orders = Order.objects.filter(status='delivered').select_related('user').prefetch_related('items__product__category').order_by('-created_at')
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category_id = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')

    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    if category_id:
        orders = orders.filter(items__product__category_id=category_id).distinct()
    if price_min:
        orders = orders.filter(total__gte=price_min)
    if price_max:
        orders = orders.filter(total__lte=price_max)

    total_revenue = orders.aggregate(Sum('total'))['total__sum'] or 0
    total_count = orders.count()
    categories = Category.objects.all()

    return render(request, 'core/admin_reports.html', {
        'orders': orders,
        'categories': categories,
        'total_revenue': total_revenue,
        'total_count': total_count,
        'date_from': date_from,
        'date_to': date_to,
        'category_id': category_id,
        'price_min': price_min,
        'price_max': price_max,
    })
# =============================================================================
# ⚙️ АДМИН-ФУНКЦИИ И ОТЧЁТЫ
# =============================================================================
def is_admin(user):
    """Проверка: является ли пользователь администратором"""
    return user.is_authenticated and (user.is_admin or user.is_superuser)


@user_passes_test(is_admin)
def admin_dashboard(request):
    """Панель администратора: базовая статистика"""
    stats = {
        'total_orders': Order.objects.count(),
        'new_orders': Order.objects.filter(status='new').count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'low_stock': Product.objects.filter(is_active=True, stock__lt=10).count(),
        'total_users': User.objects.filter(is_blocked=False).count(),
        'total_revenue': Order.objects.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0,
    }
    
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    low_stock_products = Product.objects.filter(is_active=True, stock__lt=10).select_related('category')[:10]
    
    return render(request, 'core/admin_dashboard.html', {
        'stats': stats, 
        'recent_orders': recent_orders, 
        'low_stock_products': low_stock_products
    })


@user_passes_test(is_admin)
def admin_reports(request):
    """Генерация отчётов по совершённым заказам"""
    orders = Order.objects.filter(status='delivered').select_related('user').prefetch_related('items__product__category').order_by('-created_at')
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category_id = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')

    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    if category_id:
        orders = orders.filter(items__product__category_id=category_id).distinct()
    if price_min:
        orders = orders.filter(total__gte=price_min)
    if price_max:
        orders = orders.filter(total__lte=price_max)

    total_revenue = orders.aggregate(Sum('total'))['total__sum'] or 0
    total_count = orders.count()
    categories = Category.objects.all()

    return render(request, 'core/admin_reports.html', {
        'orders': orders,
        'categories': categories,
        'total_revenue': total_revenue,
        'total_count': total_count,
        'date_from': date_from,
        'date_to': date_to,
        'category_id': category_id,
        'price_min': price_min,
        'price_max': price_max,
    })
# =============================================================================
# 📄 ГЕНЕРАЦИЯ PDF ОТЧЁТА (КИРИЛЛИЦА + ДИНАМИЧЕСКИЕ ФИЛЬТРЫ)
# =============================================================================
import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 🔹 ИСПОЛЬЗУЕМ ВСТРОЕННЫЙ ШРИФТ WINDOWS (ГАРАНТИРОВАННО ПОДДЕРЖИВАЕТ РУССКИЙ)
font_path = r'C:\Windows\Fonts\arial.ttf'
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('ArialCyr', font_path))
    CYRILLIC_FONT = 'ArialCyr'
else:
    # Запасной вариант (на случай других ОС)
    CYRILLIC_FONT = 'Helvetica'

@user_passes_test(is_admin)
def admin_reports_pdf(request):
    """Генерация PDF-отчёта с учётом текущих фильтров"""
    # 1. Получаем фильтры из URL
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category_id = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')

    # 2. Базовый запрос
    orders = Order.objects.filter(status='delivered').select_related('user').order_by('-created_at')

    if date_from: orders = orders.filter(created_at__date__gte=date_from)
    if date_to: orders = orders.filter(created_at__date__lte=date_to)
    if category_id: orders = orders.filter(items__product__category_id=category_id).distinct()
    if price_min: orders = orders.filter(total__gte=price_min)
    if price_max: orders = orders.filter(total__lte=price_max)

    # 3. Формируем умный заголовок на основе применённых фильтров
    filter_parts = []
    if date_from or date_to:
        filter_parts.append(f"период: {date_from or 'начало'} — {date_to or 'сейчас'}")
    
    if category_id:
        try:
            cat = Category.objects.get(id=category_id)
            filter_parts.append(f"категория: {cat.name}")
        except Category.DoesNotExist:
            pass
            
    if price_min or price_max:
        filter_parts.append(f"сумма: от {price_min or '0'} до {price_max or '∞'} ₽")

    main_title = "Отчёт по доставленным заявкам"
    if filter_parts:
        main_title += f"\n({', '.join(filter_parts).capitalize()})"

    # 4. Создаём PDF в памяти
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=2.5*cm)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Создаём стиль заголовка с кириллическим шрифтом
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontName=CYRILLIC_FONT, # 🔹 Применяем наш шрифт
        fontSize=14,
        alignment=1,  # По центру
        spaceAfter=1*cm,
        leading=18
    )
    
    # Разбиваем заголовок на строки, если он слишком длинный (из-за \n)
    for line in main_title.split('\n'):
        elements.append(Paragraph(line, title_style))
        
    elements.append(Spacer(1, 0.5*cm))
    
    # 5. Формируем таблицу
    data = [['№', 'Дата', 'Клиент', 'Телефон', 'Сумма']]
    for o in orders:
        data.append([
            f"#{o.id}", 
            o.created_at.strftime('%d.%m.%Y') if o.created_at else '', 
            o.customer_name, 
            o.phone, 
            f"{o.total} ₽"
        ])
    
    t = Table(data, colWidths=[1.5*cm, 3.5*cm, 5*cm, 3.5*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT), # 🔹 ВАЖНО: шрифт для всей таблицы
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
    ]))
    elements.append(t)
    
    # 6. Отдаём файл
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="logistics_report.pdf"'
    return response