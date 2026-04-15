
import csv
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import re
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction, models
from .models import DELIVERY_PRICES
from .models import Product, Category, Stock, Order, User
from .forms import UserRegisterForm
from .decorators import admin_required
from .utils import Cart  # <-- Класс корзины
from .models import Product, Category, Stock, Order, OrderItem, User, DELIVERY_CHOICES, DELIVERY_PRICES
# ------------------ ПУБЛИЧНАЯ ЧАСТЬ ------------------

def catalog_view(request):
    products = Product.objects.select_related('category').filter(status='active')
    categories = Category.objects.annotate(product_count=models.Count('products')).all()
    
    # Фильтрация по категории
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        products = products.filter(status=status_filter)

    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query)

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'catalog.html', context)

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'client'
            user.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('catalog')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('catalog')

# ------------------ АДМИН: ТОВАРЫ ------------------

@admin_required
def admin_products_view(request):
    products = Product.objects.select_related('category', 'stock').all()
    categories = Category.objects.all()
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    if category_filter: products = products.filter(category_id=category_filter)
    if status_filter: products = products.filter(status=status_filter)
    if search: products = products.filter(name__icontains=search)
    return render(request, 'admin/products_list.html', {'products': products, 'categories': categories, 'active_tab': 'products'})

@admin_required
def admin_product_add_view(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    name=request.POST.get('name'),
                    description=request.POST.get('description', ''),
                    price=request.POST.get('price'),
                    category_id=request.POST.get('category'),
                    status=request.POST.get('status', 'active'),
                    image=request.FILES.get('image')
                )
                Stock.objects.create(
                    product=product,
                    quantity=int(request.POST.get('quantity', 0)),
                    min_threshold=int(request.POST.get('min_threshold', 5))
                )
                messages.success(request, f'Товар "{product.name}" добавлен!')
                return redirect('admin_products')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    return render(request, 'admin/product_form.html', {'categories': categories, 'action': 'add'})

@admin_required
def admin_product_edit_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    stock = product.stock if hasattr(product, 'stock') else None
    
    if request.method == 'POST':
        # === ОТЛАДКА ===
        print("="*50)
        print(f"🔍 POST данные: {request.POST}")
        print(f"💰 Цена из формы: '{request.POST.get('price')}'")
        print(f"📦 ID товара: {product_id}")
        print(f"📊 Старая цена: {product.price}")
        # ================
        
        try:
            with transaction.atomic():
                product.name = request.POST.get('name')
                product.description = request.POST.get('description', '')
                price_raw = request.POST.get('price', '0').replace(',', '.')
                product.price = Decimal(price_raw) if price_raw else Decimal('0')
                
                # === ОТЛАДКА ===
                print(f"💵 Новая цена: {product.price}")
                # ================
                
                product.category_id = request.POST.get('category')
                product.status = request.POST.get('status', 'active')
                if request.FILES.get('image'): product.image = request.FILES.get('image')
                product.save()
                
                # === ОТЛАДКА ===
                print(f"✅ После save(): {Product.objects.get(id=product_id).price}")
                print("="*50)
                # ================
                
                if stock:
                    stock.quantity = int(request.POST.get('quantity', stock.quantity))
                    stock.min_threshold = int(request.POST.get('min_threshold', stock.min_threshold))
                    stock.save()
                else:
                    Stock.objects.create(product=product, quantity=int(request.POST.get('quantity', 0)), min_threshold=int(request.POST.get('min_threshold', 5)))
                messages.success(request, 'Товар обновлён!')
                return redirect('admin_products')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
            print(f"❌ ОШИБКА: {e}")  # === ОТЛАДКА ===
    return render(request, 'admin/product_form.html', {'product': product, 'stock': stock, 'categories': categories, 'action': 'edit'})

@admin_required
def admin_product_delete_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар удалён.')
        return redirect('admin_products')
    return render(request, 'admin/product_confirm_delete.html', {'product': product})

# ------------------ АДМИН: ЗАКАЗЫ (МЕНЕДЖЕР) ------------------

@admin_required
def admin_orders_view(request):
    orders = Order.objects.select_related('client').all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter: orders = orders.filter(status=status_filter)
    return render(request, 'admin/orders_list.html', {'orders': orders, 'status_choices': Order.STATUS_CHOICES, 'active_tab': 'orders'})

@admin_required
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} изменен.')
            return redirect('admin_order_detail', order_id=order.id)
    return render(request, 'admin/order_detail.html', {'order': order, 'active_tab': 'orders'})

@admin_required
def admin_invoice_view(request, order_id):
    """Генерация товарной накладной (ТОРГ-12 упрощённая)"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    order = get_object_or_404(Order, id=order_id)
    
    # Получаем текущее время в UTC и конвертируем в UTC+5
    utc_now = timezone.now()
    msk5_now = utc_now + timedelta(hours=5)  # UTC+5
    
    context = {
        'order': order,
        'now': msk5_now,
        'invoice_date': msk5_now.strftime('%d.%m.%Y'),
        'invoice_time': msk5_now.strftime('%H:%M:%S'),
    }
    
    return render(request, 'admin/invoice.html', context)
# ------------------ КОРЗИНА И ЗАКАЗЫ (КЛИЕНТ) ------------------


@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})

def cart_add_view(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product, quantity)
    messages.success(request, f'Товар "{product.name}" добавлен в корзину')
    return redirect('cart_view')

def cart_remove_view(request, product_id):
    """Удаление товара из корзины"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    return redirect('cart_view')

def cart_update_view(request, product_id):
    """Обновление количества товара в корзине"""
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart.update_quantity(product, quantity)
    return redirect('cart_view')

@login_required
def checkout_view(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, 'Корзина пуста')
        return redirect('catalog')

    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method', 'standard')
        delivery_cost = DELIVERY_PRICES.get(delivery_method, 0)
        goods_total = cart.get_total_price()
        final_total = goods_total + delivery_cost

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    client=request.user,
                    delivery_address=request.POST.get('address') or request.user.address or '',
                    phone=request.POST.get('phone') or request.user.phone or '',
                    email=request.POST.get('email') or request.user.email,
                    comment=request.POST.get('comment', ''),
                    delivery_method=delivery_method,
                    delivery_cost=delivery_cost,
                    total_amount=final_total  # Товары + Доставка
                )
                
                for item in cart:
                    product = item['product']
                    if not hasattr(product, 'stock') or product.stock.quantity < item['quantity']:
                        raise ValueError(f'Недостаточно товара "{product.name}" на складе')
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=item['price']
                    )
                    product.stock.quantity -= item['quantity']
                    product.stock.save()
                
                cart.clear()
                messages.success(request, f'✅ Оплата прошла успешно! Заказ #{order.id} оформлен.')
                return redirect('my_orders')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка оформления: {e}')

    return render(request, 'cart/checkout.html', {'cart': cart, 'delivery_choices': DELIVERY_CHOICES})

@login_required
def my_orders_view(request):
    """История заказов клиента"""
    orders = Order.objects.filter(client=request.user).order_by('-created_at')
    return render(request, 'cart/my_orders.html', {'orders': orders})
# ------------------ АДМИН: УПРАВЛЕНИЕ КАТЕГОРИЯМИ ------------------

@admin_required
def admin_categories_view(request):
    """Панель администратора: список категорий"""
    categories = Category.objects.annotate(product_count=models.Count('products')).all()
    context = {
        'categories': categories,
        'active_tab': 'categories'
    }
    return render(request, 'admin/categories_list.html', context)


@admin_required
def admin_category_add_view(request):
    """Панель администратора: добавление категории"""
    if request.method == 'POST':
        try:
            category = Category.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', '')
            )
            messages.success(request, f'Категория "{category.name}" успешно добавлена!')
            return redirect('admin_categories')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    
    return render(request, 'admin/category_form.html', {'action': 'add'})


@admin_required
def admin_category_edit_view(request, category_id):
    """Панель администратора: редактирование категории"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.POST.get('name')
            category.description = request.POST.get('description', '')
            category.save()
            messages.success(request, f'Категория "{category.name}" обновлена!')
            return redirect('admin_categories')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    
    context = {'category': category, 'action': 'edit'}
    return render(request, 'admin/category_form.html', context)


@admin_required
def admin_category_delete_view(request, category_id):
    """Панель администратора: удаление категории"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Категория "{category_name}" удалена.')
        return redirect('admin_categories')
    
    context = {'category': category}
    return render(request, 'admin/category_confirm_delete.html', context)
# Добавьте в начало файла, если ещё нет:


# ------------------ КОРЗИНА И ЗАКАЗЫ ------------------

@login_required
def cart_view(request):
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})

def cart_add_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, status='active')
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart.add(product, quantity)
        messages.success(request, f'Товар "{product.name}" добавлен в корзину')
    return redirect('cart_view')

def cart_remove_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    return redirect('cart_view')

def cart_update_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart.add(product, quantity, override_quantity=True)
    else:
        cart.remove(product)
    return redirect('cart_view')
@login_required
def checkout_view(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, 'Корзина пуста')
        return redirect('catalog')

    if request.method == 'POST':
        # Серверная валидация телефона
        phone_raw = request.POST.get('phone', '')
        phone_digits = re.sub(r'\D', '', phone_raw)
        
        if len(phone_digits) != 11 or phone_digits[0] not in ['7', '8']:
            messages.error(request, 'Неверный формат номера телефона. Требуется 11 цифр.')
            return render(request, 'cart/checkout.html', {'cart': cart})

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    client=request.user,
                    delivery_address=request.POST.get('address'),
                    phone=phone_raw,  # Сохраняем отформатированный вид
                    email=request.POST.get('email'),
                    comment=request.POST.get('comment', ''),
                    total_amount=cart.get_total_price()
                )
                
                for item in cart:
                    product = item['product']
                    if not hasattr(product, 'stock') or product.stock.quantity < item['quantity']:
                        raise ValueError(f'Недостаточно товара "{product.name}" на складе')
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=item['price']
                    )
                    product.stock.quantity -= item['quantity']
                    product.stock.save()
                
                cart.clear()
                messages.success(request, f'✅ Оплата прошла успешно! Заказ #{order.id} оформлен.')
                return redirect('my_orders')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка оформления: {e}')

    return render(request, 'cart/checkout.html', {
    'cart': cart,
    'delivery_choices': DELIVERY_CHOICES  # ← Добавь эту строку!
})

@login_required
def my_orders_view(request):
    orders = Order.objects.filter(client=request.user).order_by('-created_at')
    return render(request, 'cart/my_orders.html', {'orders': orders})
@admin_required
def admin_order_delete_view(request, order_id):
    """Удаление заказа (только отмененные или новые)"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # Нельзя удалять доставленные/отгруженные заказы
        if order.status in ['delivered', 'shipped']:
            messages.error(request, 'Нельзя удалить доставленный или отгруженный заказ!')
            return redirect('admin_order_detail', order_id=order_id)
        
        order_id_temp = order.id
        order.delete()
        messages.success(request, f'Заказ #{order_id_temp} удалён.')
        return redirect('admin_orders')
    
    context = {'order': order}
    return render(request, 'admin/order_confirm_delete.html', context)
@admin_required
def export_orders_csv(request):
    """Экспорт заказов в CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="orders_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')  # BOM для корректного отображения кириллицы в Excel
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID заказа', 'Дата', 'Клиент', 'Email', 'Телефон', 'Адрес', 
                     'Статус', 'Товаров', 'Сумма', 'Комментарий'])
    
    orders = Order.objects.select_related('client').prefetch_related('items').all()
    for order in orders:
        writer.writerow([
            order.id,
            order.created_at.strftime('%d.%m.%Y %H:%M'),
            f'{order.client.first_name} {order.client.last_name}' if order.client else 'Гость',
            order.email,
            order.phone,
            order.delivery_address,
            order.get_status_display(),
            order.items.count(),
            f'{order.total_amount:.2f}',
            order.comment or ''
        ])
    
    return response


@admin_required
def export_products_csv(request):
    """Экспорт товаров в CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="products_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Название', 'Категория', 'Цена', 'Статус', 
                     'На складе', 'Зарезервировано', 'Описание', 'Дата создания'])
    
    products = Product.objects.select_related('category').all()
    for product in products:
        stock_qty = product.stock.quantity if hasattr(product, 'stock') else 0
        stock_reserved = product.stock.reserved if hasattr(product, 'stock') else 0
        
        writer.writerow([
            product.id,
            product.name,
            product.category.name if product.category else 'Без категории',
            f'{product.price:.2f}',
            product.get_status_display(),
            stock_qty,
            stock_reserved,
            product.description[:100] if product.description else '',
            product.created_at.strftime('%d.%m.%Y')
        ])
    
    return response


@admin_required
def export_stock_csv(request):
    """Экспорт складских остатков в CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="stock_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Товар', 'Категория', 'На складе', 'Зарезервировано', 
                     'Доступно', 'Мин. порог', 'Статус пополнения'])
    
    products = Product.objects.select_related('category', 'stock').all()
    for product in products:
        if hasattr(product, 'stock'):
            stock = product.stock
            available = stock.quantity - stock.reserved
            status = 'Требует пополнения' if stock.quantity < stock.min_threshold else 'OK'
            
            writer.writerow([
                product.name,
                product.category.name if product.category else 'Без категории',
                stock.quantity,
                stock.reserved,
                available,
                stock.min_threshold,
                status
            ])
    
    return response


@admin_required
def export_sales_report_csv(request):
    """Отчёт по продажам (за период)"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')
    
    # Получаем период из GET параметров (по умолчанию - 30 дней)
    days = int(request.GET.get('days', 30))
    date_from = timezone.now() - timedelta(days=days)
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ОТЧЁТ ПО ПРОДАЖАМ'])
    writer.writerow([f'Период: {date_from.strftime("%d.%m.%Y")} - {timezone.now().strftime("%d.%m.%Y")}'])
    writer.writerow([])
    writer.writerow(['Товар', 'Продано шт.', 'Выручка', 'Средняя цена'])
    
    # Агрегируем данные
    from django.db.models import Sum, Count
    orders = Order.objects.filter(created_at__gte=date_from, status__in=['paid', 'processing', 'shipped', 'delivered'])
    order_items = OrderItem.objects.filter(order__in=orders)
    
    # Группировка по товарам
    from django.db.models import F
    sales_by_product = order_items.values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price')),
        avg_price=Sum(F('quantity') * F('price')) / Sum('quantity')
    ).order_by('-total_revenue')
    
    for item in sales_by_product:
        writer.writerow([
            item['product__name'] or 'Удалённый товар',
            item['total_qty'] or 0,
            f'{item["total_revenue"]:.2f}' if item['total_revenue'] else '0.00',
            f'{item["avg_price"]:.2f}' if item['avg_price'] else '0.00'
        ])
    
    # Итого
    total_revenue = sum(item['total_revenue'] or 0 for item in sales_by_product)
    total_qty = sum(item['total_qty'] or 0 for item in sales_by_product)
    
    writer.writerow([])
    writer.writerow(['ИТОГО:', total_qty, f'{total_revenue:.2f}', ''])
    
    return response
# ------------------ АДМИН: ПОЛЬЗОВАТЕЛИ ------------------

@admin_required
def admin_users_view(request):
    """Список всех пользователей"""
    users = User.objects.all().order_by('-date_joined')
    
    # Фильтрация по роли
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Поиск
    search = request.GET.get('search')
    if search:
        users = users.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'active_tab': 'users',
        'role_choices': User._meta.get_field('role').choices
    }
    return render(request, 'admin/users_list.html', context)


@admin_required
def admin_user_detail_view(request, user_id):
    """Детали пользователя"""
    user = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(client=user).order_by('-created_at')[:10]
    
    context = {
        'user_obj': user,  # user - зарезервированное слово в Django
        'orders': orders,
        'active_tab': 'users'
    }
    return render(request, 'admin/user_detail.html', context)


@admin_required
def admin_user_edit_view(request, user_id):
    """Редактирование пользователя"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            user_obj.first_name = request.POST.get('first_name')
            user_obj.last_name = request.POST.get('last_name')
            user_obj.role = request.POST.get('role')
            user_obj.phone = request.POST.get('phone', '')
            user_obj.address = request.POST.get('address', '')
            
            # Смена пароля (если указан)
            new_password = request.POST.get('password')
            if new_password:
                user_obj.set_password(new_password)
            
            user_obj.save()
            messages.success(request, f'Пользователь {user_obj.first_name} обновлён!')
            return redirect('admin_users')
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')
    
    context = {
        'user_obj': user_obj,
        'role_choices': User._meta.get_field('role').choices,
        'action': 'edit'
    }
    return render(request, 'admin/user_form.html', context)