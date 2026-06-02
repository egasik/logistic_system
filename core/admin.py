from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, Profile, Category, Brand, Product, ProductImage, CartItem, Order, OrderItem

# =============================================================================
# 🔧 Безопасно убираем стандартные группы
# =============================================================================
try:
    admin.site.unregister(Group)
except Exception:
    pass

# =============================================================================
# 👤 Пользователи (ИСПРАВЛЕНО: используем date_joined вместо created_at)
# =============================================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Поля в списке (заменено created_at на date_joined)
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_blocked', 'is_admin', 'date_joined')
    list_filter = ('is_active', 'is_blocked', 'is_admin', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    # Поля в форме редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'phone', 'address')}),
        ('Статус и права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 'is_blocked')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone'),
        }),
    )

    # Убираем лишние поля из формы
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop('groups', None)
        form.base_fields.pop('user_permissions', None)
        return form

    # Массовые действия для блокировки
    actions = ['block_users', 'unblock_users']

    @admin.action(description='🚫 Заблокировать выбранных пользователей')
    def block_users(self, request, queryset):
        updated = queryset.update(is_blocked=True)
        self.message_user(request, f'⛔ Заблокировано пользователей: {updated}')

    @admin.action(description='✅ Разблокировать выбранных пользователей')
    def unblock_users(self, request, queryset):
        updated = queryset.update(is_blocked=False)
        self.message_user(request, f'✅ Разблокировано пользователей: {updated}')


# =============================================================================
# 👤 Профиль пользователя
# =============================================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


# =============================================================================
# 📦 Категории и Бренды
# =============================================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


# =============================================================================
# 📦 Товары
# =============================================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'is_active')
    list_filter = ('is_active', 'category', 'brand')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


# =============================================================================
# ️ Изображения товаров
# =============================================================================
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'path', 'sort_order')
    list_filter = ('product__category',)
    readonly_fields = ('created_at', 'updated_at')


# =============================================================================
#  Корзина и Заказы
# =============================================================================
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'unit_price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'customer_name', 'email')
    readonly_fields = ('created_at', 'updated_at', 'user')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'unit_price')
    readonly_fields = ('order', 'product', 'product_name', 'unit_price', 'quantity', 'created_at', 'updated_at')