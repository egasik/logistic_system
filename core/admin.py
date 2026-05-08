# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import User, Profile, Category, Carrier, Product, ProductImage, CartItem, Order, OrderItem

# Безопасно убираем Group
try:
    admin.site.unregister(Group)
except Exception:
    pass

# =============================================================================
# 👤 Пользователи
# =============================================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('name', 'phone', 'address')}),
        ('Статус', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 'is_blocked')}),
        ('Даты', {'fields': ('created_at', 'updated_at', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'phone'),
        }),
    )
    list_display = ('email', 'name', 'is_staff', 'is_superuser', 'is_admin', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_admin', 'is_blocked')
    search_fields = ('email', 'name')
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    ordering = ('-created_at',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop('groups', None)
        form.base_fields.pop('user_permissions', None)
        return form

# =============================================================================
# Остальные модели (стандартная регистрация)
# =============================================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_active')
    list_filter = ('is_active',)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'path')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total')
    list_filter = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity')