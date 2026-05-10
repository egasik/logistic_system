from django.contrib import admin
from django.contrib.auth.models import Group
from .models import (
    User, Profile, Category, Brand,
    Product, ProductImage, CartItem,
    Order, OrderItem
)

# Убираем встроенный раздел "Группы"
admin.site.unregister(Group)

# Регистрируем только наши модели
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)