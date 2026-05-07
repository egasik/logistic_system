from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import User, Profile, Category, Carrier, Product, ProductImage, CartItem, Order, OrderItem

# =============================================================================
# 🔧 ИСПРАВЛЕНИЕ ОШИБКИ: Безопасно убираем Group
# =============================================================================
# Группа "Группы" (Groups) нам не нужна по ТЗ, но удалять её нужно безопасно,
# чтобы Django не падал с ошибкой NotRegistered при запуске.
try:
    admin.site.unregister(Group)
except Exception:
    pass

# =============================================================================
# 👤 Пользователи (таблица 7 ПЗ)
# =============================================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Поля в форме редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('name', 'phone', 'address')}),
        ('Статус', {'fields': ('is_active', 'is_admin', 'is_blocked')}),
        ('Даты', {'fields': ('created_at', 'updated_at')}),
    )
    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'phone'),
        }),
    )
        # Добавь это в класс UserAdmin:
    actions = ['make_admin_bulk']

    @admin.action(description='🔑 Выдать права администратора (массово)')
    def make_admin_bulk(self, request, queryset):
        updated = queryset.update(is_admin=True)
        self.message_user(request, f'✅ Администраторами назначено: {updated} пользователей.')
    # Список в админке
    list_display = ('email', 'name', 'phone', 'is_admin', 'is_blocked', 'created_at')
    list_filter = ('is_admin', 'is_blocked', 'created_at')
    search_fields = ('email', 'name', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    ordering = ('-created_at',)
    
    # Убираем лишние поля: groups, user_permissions, is_superuser
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop('groups', None)
        form.base_fields.pop('user_permissions', None)
        form.base_fields.pop('is_superuser', None)
        return form

# =============================================================================
# 👤 Профиль пользователя
# =============================================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_phone', 'get_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('created_at', 'updated_at', 'avatar')
    
    @admin.display(description='Телефон', ordering='user__phone')
    def get_phone(self, obj):
        return obj.user.phone or '—'
    
    @admin.display(description='Адрес', ordering='user__address')
    def get_address(self, obj):
        return obj.user.address or '—'

# =============================================================================
# 📦 Категории (таблица 8 ПЗ)
# =============================================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    @admin.display(description='Товаров', ordering='-product_count')
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()

# =============================================================================
# 🚚 Перевозчики / Бренды (таблица 9 ПЗ)
# =============================================================================
@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    list_filter = ('created_at',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    @admin.display(description='Товаров', ordering='-product_count')
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()

# =============================================================================
# 📦 Товары / Грузы (таблица 10 ПЗ)
# =============================================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'carrier', 'price', 'stock', 'is_active', 'sku')
    list_filter = ('category', 'carrier', 'is_active', 'stock')
    search_fields = ('name', 'sku', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    
    fieldsets = (
        ('Основное', {'fields': ('name', 'slug', 'sku', 'description')}),
        ('Классификация', {'fields': ('category', 'carrier')}),
        ('Цена и остатки', {'fields': ('price', 'stock', 'is_active')}),
        ('Служебное', {'fields': ('created_at', 'updated_at', 'deleted_at')}),
    )
    
    # Действия: массовое изменение статуса
    actions = ['make_active', 'make_inactive', 'low_stock_alert']
    
    @admin.action(description='✓ Активировать выбранные')
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано товаров: {updated}')
    
    @admin.action(description='✗ Деактивировать выбранные')
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано товаров: {updated}')
    
    @admin.action(description='⚠️ Товары с низким остатком (<10)')
    def low_stock_alert(self, request, queryset):
        low = queryset.filter(stock__lt=10)
        if low:
            self.message_user(request, f'Внимание! Низкий остаток у {low.count()} товаров', 'warning')
        else:
            self.message_user(request, 'Все товары в наличии', 'success')

# =============================================================================
# 🖼️ Изображения товаров (таблица 11 ПЗ)
# =============================================================================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('path', 'sort_order')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'path', 'sort_order', 'created_at')
    list_filter = ('product__category', 'created_at')
    search_fields = ('product__name', 'path')
    readonly_fields = ('created_at', 'updated_at')

# =============================================================================
# 🛒 Корзина (таблица 12 ПЗ) — только просмотр
# =============================================================================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'get_total')
    list_filter = ('user', 'product__category')
    search_fields = ('user__email', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    
    @admin.display(description='Сумма', ordering='quantity')
    def get_total(self, obj):
        return f'{obj.product.price * obj.quantity:.2f} ₽'
    
    # Запрет редактирования: корзина — временная сущность
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return True

# =============================================================================
# 📋 Заявки / Заказы (таблица 13 ПЗ)
# =============================================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'quantity', 'unit_price', 'get_total')
    readonly_fields = ('product_name', 'quantity', 'unit_price', 'get_total')
    
    @admin.display(description='Сумма')
    def get_total(self, obj):
        return f'{obj.unit_price * obj.quantity:.2f} ₽'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status_badge', 'total', 'customer_name', 'created_at')
    list_filter = ('status', 'created_at', 'user__is_admin')
    search_fields = ('id', 'customer_name', 'phone', 'email', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total', 'user')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Информация', {'fields': ('id', 'user', 'status', 'total')}),
        ('Контакты', {'fields': ('customer_name', 'phone', 'email', 'address')}),
        ('Дополнительно', {'fields': ('notes', 'created_at', 'updated_at')}),
    )
    
    # Кастомный бейдж статуса
    @admin.display(description='Статус', ordering='status')
    def status_badge(self, obj):
        colors = {
            'new': 'gray', 'processing': 'blue', 'shipped': 'orange',
            'delivered': 'green', 'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background:#{};color:white;padding:3px 8px;border-radius:4px;font-size:0.85em">{}</span>',
            color, obj.get_status_display()
        )
    
    # Действия: массовая смена статуса
    actions = ['mark_processing', 'mark_shipped', 'mark_delivered', 'mark_cancelled']
    
    @admin.action(description='🔄 В обработку')
    def mark_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'Обновлено заявок: {updated}')
    
    @admin.action(description='🚚 Отправлено')
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'Обновлено заявок: {updated}')
    
    @admin.action(description='✅ Доставлено')
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'Обновлено заявок: {updated}')
    
    @admin.action(description='❌ Отменено')
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'Обновлено заявок: {updated}')

# =============================================================================
# 📦 Позиции заявки (таблица 14 ПЗ) — только просмотр
# =============================================================================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'unit_price', 'get_total')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('product_name', 'order__id')
    readonly_fields = ('order', 'product', 'product_name', 'unit_price', 'quantity', 'created_at', 'updated_at')
    
    @admin.display(description='Сумма', ordering='unit_price')
    def get_total(self, obj):
        return f'{obj.unit_price * obj.quantity:.2f} ₽'
    
    # Запрет редактирования: история заказа не меняется
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

# =============================================================================
# 🎛️ Настройки админ-панели
# =============================================================================
admin.site.site_header = 'Администрирование'
admin.site.site_title = 'LogisticsPro Admin'
admin.site.index_title = 'Панель управления'