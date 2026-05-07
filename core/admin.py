from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, Profile, Category, Carrier, Product, ProductImage, CartItem, Order, OrderItem

admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('name', 'phone', 'address')}),
        ('Права', {'fields': ('is_active', 'is_admin', 'is_blocked')}),
        ('Даты', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2', 'name')}),)
    list_display = ('email', 'name', 'is_admin', 'is_blocked', 'created_at')
    list_filter = ('is_admin', 'is_blocked')
    search_fields = ('email', 'name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)  
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop('groups', None)
        form.base_fields.pop('user_permissions', None)
        return form

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_phone', 'get_address')
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('created_at', 'updated_at', 'avatar')
    
    @admin.display(description="Телефон")
    def get_phone(self, obj): return obj.user.phone or "—"
    @admin.display(description="Адрес")
    def get_address(self, obj): return obj.user.address or "—"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug'); search_fields = ('name',); prepopulated_fields = {'slug': ('name',)}

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug'); search_fields = ('name',); prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'carrier', 'price', 'stock', 'is_active')
    list_filter = ('category', 'carrier', 'is_active')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'path', 'sort_order'); list_filter = ('product__category',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity'); list_filter = ('user',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'phone', 'email', 'id')
    readonly_fields = ('created_at', 'updated_at', 'total')
    fieldsets = (
        ('Информация', {'fields': ('id', 'user', 'status', 'total')}),
        ('Контакты', {'fields': ('customer_name', 'phone', 'email', 'address')}),
        ('Дополнительно', {'fields': ('notes', 'created_at', 'updated_at')}),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'unit_price')
    list_filter = ('order__status',)