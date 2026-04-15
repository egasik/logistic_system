from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

# ------------------ КАСТОМНЫЙ МЕНЕДЖЕР ПОЛЬЗОВАТЕЛЕЙ ------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Поле Email должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


# ------------------ ПОЛЬЗОВАТЕЛИ ------------------
class User(AbstractUser):
    objects = CustomUserManager()
    username = None
    email = models.EmailField('Email адрес', unique=True)
    role = models.CharField('Роль', max_length=20, choices=[
        ('client', 'Клиент'),
        ('manager', 'Менеджер'),
        ('warehouse', 'Кладовщик'),
        ('admin', 'Администратор'),
    ], default='client')
    phone = models.CharField('Телефон', max_length=20, blank=True, null=True)
    address = models.TextField('Адрес доставки', blank=True, null=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


# ------------------ КАТЕГОРИИ ------------------
class Category(models.Model):
    name = models.CharField('Название категории', max_length=100)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']


# ------------------ ТОВАРЫ ------------------
class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('inactive', 'Неактивен'),
        ('discontinued', 'Снят с производства'),
        ('out_of_stock', 'Нет в наличии'),
    ]
    
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Категория', related_name='products')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='active')
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']


# ------------------ СКЛАД ------------------
class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock', verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество на складе', default=0)
    reserved = models.PositiveIntegerField('Зарезервировано', default=0)
    min_threshold = models.PositiveIntegerField('Минимальный порог', default=5)

    def __str__(self):
        return f"{self.product.name} | Остаток: {self.quantity} | Резерв: {self.reserved}"

    class Meta:
        verbose_name = 'Складской остаток'
        verbose_name_plural = 'Складские остатки'


# ------------------ ПОСТАВЩИКИ И ПОСТАВКИ ------------------
class Supplier(models.Model):
    company_name = models.CharField('Название компании', max_length=150)
    contact_person = models.CharField('Контактное лицо', max_length=100)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)
    address = models.TextField('Адрес', blank=True)
    terms = models.TextField('Условия поставки', blank=True)

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'


class Supply(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидается'),
        ('received', 'Принята'),
        ('cancelled', 'Отменена'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='Поставщик')
    invoice_number = models.CharField('Номер накладной', max_length=50, unique=True)
    date = models.DateField('Дата поставки')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    def __str__(self):
        return f"Поставка #{self.invoice_number} от {self.supplier}"

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставки'


class SupplyItem(models.Model):
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество')
    purchase_price = models.DecimalField('Цена закупки', max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

DELIVERY_CHOICES = [
    ('standard', 'Стандартная (3-5 дней)'),
    ('express', 'Экспресс (1-2 дня)'),
    ('premium', 'Премиум (в день заказа)'),
    ('pickup', 'Самовывоз со склада'),
]

DELIVERY_PRICES = {
    'standard': 0,
    'express': 350,
    'premium': 750,
    'pickup': 0,
}
# ------------------ ЗАКАЗЫ ------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('paid', 'Оплачен'),
        ('processing', 'На комплектации'),
        ('shipped', 'Отгружен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
        ('returned', 'Возвращен'),
    ]
    
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders', verbose_name='Клиент')
    created_at = models.DateTimeField('Дата заказа', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    delivery_address = models.TextField('Адрес доставки')
    phone = models.CharField('Контактный телефон', max_length=20)
    email = models.EmailField('Email')
    comment = models.TextField('Комментарий', blank=True)
    delivery_method = models.CharField('Способ доставки', max_length=20, choices=DELIVERY_CHOICES, default='standard')
    delivery_cost = models.DecimalField('Стоимость доставки', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('Общая сумма', max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Заказ #{self.pk} от {self.created_at.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField('Количество')
    price = models.DecimalField('Цена на момент заказа', max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product} x {self.quantity}"


# ------------------ ТРАНЗАКЦИИ ------------------
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
    ]
    
    code = models.CharField('Код транзакции', max_length=30, unique=True)
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Клиент')
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Заказ')
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    def __str__(self):
        return f"Транзакция {self.code} | {self.amount} ₽"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'