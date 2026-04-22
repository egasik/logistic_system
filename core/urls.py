from django.urls import path
from . import views


urlpatterns = [
    # === ПУБЛИЧНЫЕ МАРШРУТЫ ===
    path('', views.catalog_view, name='catalog'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # === КОРЗИНА И ЗАКАЗЫ (КЛИЕНТ) ===
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update_view, name='cart_update'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.my_orders_view, name='my_orders'),
    
    # === ПАНЕЛЬ УПРАВЛЕНИЯ (АДМИН/МЕНЕДЖЕР) ===
    # 🔧 Используем 'panel/' вместо 'admin/' чтобы не конфликтовать с Django Admin
    # Товары
    path('panel/products/', views.admin_products_view, name='admin_products'),
    path('panel/products/add/', views.admin_product_add_view, name='admin_product_add'),
    path('panel/products/<int:product_id>/edit/', views.admin_product_edit_view, name='admin_product_edit'),
    path('panel/products/<int:product_id>/delete/', views.admin_product_delete_view, name='admin_product_delete'),
    
    # Заказы
    path('panel/orders/', views.admin_orders_view, name='admin_orders'),
    path('panel/orders/<int:order_id>/', views.admin_order_detail_view, name='admin_order_detail'),
    path('panel/orders/<int:order_id>/invoice/', views.admin_invoice_view, name='admin_invoice'),
     path('panel/orders/<int:order_id>/delete/', views.admin_order_delete_view, name='admin_order_delete'),  # ← НОВЫЙ
        # Управление категориями (админ)
    path('panel/categories/', views.admin_categories_view, name='admin_categories'),
    path('panel/categories/add/', views.admin_category_add_view, name='admin_category_add'),
    path('panel/categories/<int:category_id>/edit/', views.admin_category_edit_view, name='admin_category_edit'),
    path('panel/categories/<int:category_id>/delete/', views.admin_category_delete_view, name='admin_category_delete'),

        # Экспорт отчётов
    path('panel/export/orders/', views.export_orders_csv, name='export_orders'),
    path('panel/export/products/', views.export_products_csv, name='export_products'),
    path('panel/export/stock/', views.export_stock_csv, name='export_stock'),
    path('panel/export/sales/', views.export_sales_report_csv, name='export_sales'),
    
    # Пользователи
    path('panel/users/', views.admin_users_view, name='admin_users'),
    path('panel/users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('panel/users/<int:user_id>/edit/', views.admin_user_edit_view, name='admin_user_edit'),
    
        #профиль
    path('profile/', views.profile_view, name='profile'),





]