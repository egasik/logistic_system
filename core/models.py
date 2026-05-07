from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

# =============================================================================
# 👤 МЕНЕДЖЕР ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

# =============================================================================
# 👤 ПОЛЬЗОВАТЕЛЬ (Таблица 7)
# =============================================================================
class User(AbstractUser):
    username = None  # Отключаем стандартное поле username
    objects = UserManager()
    
    name = models.CharField('ФИО', max_length=255, blank=True)
    email = models.EmailField('Email', unique=True)
    # password наследуется от AbstractUser, не переопределяем
    is_admin = models.BooleanField('Администратор', default=False)
    is_blocked = models.BooleanField('Заблокирован', default=False)
    phone = models.CharField('Телефон', max_length=32, blank=True, null=True)
    address = models.CharField('Адрес доставки', max_length=500, blank=True, null=True)
    remember_token = models.CharField('Токен запоминания', max_length=100, blank=True, null=True)
    
    # Поля timestamps добавляем явно, так как отключаем username
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return self.email or self.name

# =============================================================================
# 👤 ПРОФИЛЬ (расширение пользователя)
# =============================================================================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    bio = models.TextField('О себе', blank=True)
    # 🔧 Аватар хранится как путь, но загружается через форму
    avatar = models.CharField('Аватар (путь)', max_length=255, blank=True, null=True, editable=False)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.email}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)  

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
# =============================================================================
# 📦 КАТЕГОРИЯ (Таблица 8)
# =============================================================================
class Category(models.Model):
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-код', unique=True, help_text='Латиницей, без пробелов')
    description = models.TextField('Описание', blank=True, null=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

# =============================================================================
# 🚚 ПЕРЕВОЗЧИК / БРЕНД (Таблица 9)
# =============================================================================
class Carrier(models.Model):
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-код', unique=True, help_text='Латиницей, без пробелов')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Перевозчик'
        verbose_name_plural = 'Перевозчики'
        ordering = ['name']

    def __str__(self):
        return self.name

# =============================================================================
# 📦 ТОВАР / ГРУЗ (Таблица 10)
# =============================================================================
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    carrier = models.ForeignKey(Carrier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='Перевозчик')
    name = models.CharField('Название', max_length=255)
    slug = models.SlugField('URL-код', unique=True, help_text='Латиницей, без пробелов')
    description = models.TextField('Описание', blank=True, null=True)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    sku = models.CharField('Артикул', max_length=64, blank=True, null=True)
    is_active = models.BooleanField('Активен', default=True)
    deleted_at = models.DateTimeField('Удалён (мягкое удаление)', null=True, blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.name

# =============================================================================
# 🖼️ ИЗОБРАЖЕНИЕ ТОВАРА (Таблица 11)
# =============================================================================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    path = models.CharField('Путь к файлу', max_length=255, help_text='Относительно media/, например: products/item.jpg')
    sort_order = models.PositiveSmallIntegerField('Порядок сортировки', default=0)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'Изображение для {self.product.name}'

# =============================================================================
# 🛒 ЭЛЕМЕНТ КОРЗИНЫ / ЧЕРНОВИК ЗАЯВКИ (Таблица 12)
# =============================================================================
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items', verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество', default=1)
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} × {self.quantity}'

    def get_total_price(self):
        return self.product.price * self.quantity

# =============================================================================
# 📋 ЗАЯВКА / ЗАКАЗ (Таблица 13)
# =============================================================================
class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлена'),
        ('delivered', 'Доставлена'),
        ('cancelled', 'Отменена'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Клиент')
    status = models.CharField('Статус', max_length=32, choices=STATUS_CHOICES, default='new')
    total = models.DecimalField('Итого', max_digits=12, decimal_places=2, default=0.00)
    customer_name = models.CharField('ФИО заказчика', max_length=255)
    phone = models.CharField('Телефон', max_length=32)
    email = models.EmailField('Email')
    address = models.CharField('Адрес доставки', max_length=500)
    notes = models.TextField('Примечания', blank=True, null=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заявка #{self.id} — {self.customer_name} ({self.get_status_display()})'

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

# =============================================================================
# 📦 ПОЗИЦИЯ ЗАЯВКИ (Таблица 14)
# =============================================================================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заявка')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Товар')
    product_name = models.CharField('Название на момент заказа', max_length=255)
    unit_price = models.DecimalField('Цена за ед.', max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество')
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Позиция заявки'
        verbose_name_plural = 'Позиции заявок'

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

    def get_total_price(self):
        return self.unit_price * self.quantity