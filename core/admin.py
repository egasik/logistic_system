from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Category, Product, Stock, Supplier, Supply, SupplyItem, 
    Order, OrderItem, Transaction
)

# ------------------ ПОЛЬЗОВАТЕЛИ ------------------
# Переопределяем отображение пользователя, чтобы видеть роль и email
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'phone', 'address', 'avatar', 'role')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    ordering = ('email',)


# ------------------ ТОВАРЫ И СКЛАД ------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ProductStockInline(admin.StackedInline):
    model = Stock
    can_delete = False
    verbose_name_plural = 'Остатки на складе'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('name', 'description')
    inlines = [ProductStockInline]  # Показываем остатки прямо в карточке товара


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'reserved', 'min_threshold')
    list_filter = ('min_threshold',)
    search_fields = ('product__name',)


# ------------------ ПОСТАВЩИКИ И ПОСТАВКИ ------------------
class SupplyItemInline(admin.TabularInline):
    model = SupplyItem
    extra = 1  # Сколько пустых строк добавлять по умолчанию


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'phone')
    search_fields = ('company_name',)


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'supplier', 'date', 'status')
    list_filter = ('status', 'date')
    inlines = [SupplyItemInline]  # Позволяет добавлять товары прямо в поставку


# ------------------ ЗАКАЗЫ ------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('price',)  # Цену меняем только через товар


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('client__email', 'delivery_address')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]  # Позволяет видеть состав заказа


# ------------------ ТРАНЗАКЦИИ ------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('code', 'client', 'order', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('code',)
    readonly_fields = ('created_at',)