import os
import sys
import django
import urllib.request
from urllib.error import URLError

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from django.conf import settings
from pathlib import Path
from core.models import Category, Product, Stock

# === НАСТРОЙКИ ИЗОБРАЖЕНИЙ ===
# Сюда вставляй ссылки на картинки.
# Можно использовать прямые ссылки с GitHub (Raw) или любого хостинга.
# Если картинки нет, товар останется без фото.
PRODUCT_IMAGES = {
    "Смартфон NOTHING PHONE 3": "https://placehold.co/400x400/png?text=PHONE+3",
    "Ноутбук ASUS VivoBook 15": "https://placehold.co/400x400/png?text=LAPTOP",
    "Наушники Sony WH-1000XM5": "https://placehold.co/400x400/png?text=HEADPHONES",
    "Диван угловой 'Комфорт'": "https://placehold.co/400x400/png?text=SOFA",
    "Дрель-шуруповерт Bosch": "https://placehold.co/400x400/png?text=DRILL",
    "Умная лампа Philips": "https://placehold.co/400x400/png?text=LAMP",
    "Кроссовки Nike Air Max": "https://placehold.co/400x400/png?text=SNEAKERS",
    "Куртка зимняя мужская": "https://placehold.co/400x400/png?text=JACKET",
    "Рюкзак Xiaomi City": "https://placehold.co/400x400/png?text=BACKPACK",
    "Велосипед Stark Tanuki": "https://placehold.co/400x400/png?text=BIKE",
    "Гантели разборные 20кг": "https://placehold.co/400x400/png?text=DUMBBELLS",
    "Коврик для йоги Pro": "https://placehold.co/400x400/png?text=YOGA+MAT",
    "Конструктор LEGO City": "https://placehold.co/400x400/png?text=LEGO",
    "Коляска 2 в 1": "https://placehold.co/400x400/png?text=STROLLER",
    "Игра Монополия": "https://placehold.co/400x400/png?text=MONOPOLY",
}

# Данные для заполнения (Название, Описание, Цена, Категория)
PRODUCTS = [
    ("Смартфон NOTHING PHONE 3", "Мощный смартфон с прозрачным дизайном.", 40000, "Техника и электроника"),
    ("Ноутбук ASUS VivoBook 15", "Легкий ноутбук для работы и учебы.", 52900, "Техника и электроника"),
    ("Наушники Sony WH-1000XM5", "Топовое шумоподавление и звук.", 34990, "Техника и электроника"),
    ("Диван угловой 'Комфорт'", "Просторный диван с механизмом раскладки.", 45000, "Дом и сад"),
    ("Дрель-шуруповерт Bosch", "Надежный инструмент для дома.", 6500, "Дом и сад"),
    ("Умная лампа Philips", "Управление через приложение и свет.", 1890, "Дом и сад"),
    ("Кроссовки Nike Air Max", "Стильные и удобные кроссовки.", 12990, "Одежда и обувь"),
    ("Куртка зимняя мужская", "Теплая куртка для сильных морозов.", 8900, "Одежда и обувь"),
    ("Рюкзак Xiaomi City", "Вместительный рюкзак для ноутбука.", 2490, "Одежда и обувь"),
    ("Велосипед Stark Tanuki", "Горный велосипед для прогулок.", 18500, "Спорт и отдых"),
    ("Гантели разборные 20кг", "Набор гантелей для домашних тренировок.", 3200, "Спорт и отдых"),
    ("Коврик для йоги Pro", "Нескользящий коврик 6мм.", 1290, "Спорт и отдых"),
    ("Конструктор LEGO City", "Полицейский участок, 668 деталей.", 4590, "Детские товары"),
    ("Коляска 2 в 1", "Универсальная коляска для новорожденных.", 28900, "Детские товары"),
    ("Игра Монополия", "Классическая экономическая настолка.", 2190, "Детские товары"),
]

def download_and_rename_image(url, product_id):
    """
    Скачивает картинку по URL и сохраняет её как {product_id}.jpg
    """
    if not url:
        return None

    # Папка media/products
    media_dir = Path(settings.MEDIA_ROOT) / 'products'
    media_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{product_id}.jpg"
    filepath = media_dir / filename
    
    # Путь, который сохранится в БД (относительный)
    relative_path = f"products/{filename}"

    try:
        print(f"   📥 Скачивание картинки для товара #{product_id}...")
        urllib.request.urlretrieve(url, filepath)
        print(f"   ✅ Сохранено: {relative_path}")
        return relative_path
    except URLError as e:
        print(f"   ❌ Ошибка загрузки: {e}")
        return None

def fill_data():
    print("🚀 Начинаем заполнение базы демо-данными (с картинками)...")

    CATEGORIES = [
        ("Техника и электроника", "Смартфоны, ноутбуки и гаджеты."),
        ("Дом и сад", "Мебель, инструменты и товары для уюта."),
        ("Одежда и обувь", "Мужская и женская одежда, кроссовки."),
        ("Спорт и отдых", "Инвентарь, тренажеры и туризм."),
        ("Детские товары", "Игрушки, коляски и одежда для детей."),
    ]

    # 1. Категории
    cat_objects = {}
    for name, desc in CATEGORIES:
        cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
        cat_objects[name] = cat

    # 2. Товары + Остатки + Картинки
    for name, desc, price, cat_name in PRODUCTS:
        category = cat_objects.get(cat_name)
        if category:
            # Создаем или получаем товар
            prod, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'price': price,
                    'category': category,
                    'status': 'active'
                }
            )

            # Создаем остаток
            stock, stock_created = Stock.objects.get_or_create(
                product=prod,
                defaults={'quantity': 10, 'reserved': 0, 'min_threshold': 5}
            )

            # === ЛОГИКА КАРТИНОК ===
            # Получаем ссылку из словаря
            image_url = PRODUCT_IMAGES.get(name)
            
            if image_url:
                # Скачиваем и сохраняем как {id}.jpg
                saved_path = download_and_rename_image(image_url, prod.id)
                
                if saved_path:
                    # Обновляем поле image у товара
                    # Если файл уже был, мы его перезаписываем (т.к. имя id.jpg неизменно)
                    prod.image = saved_path
                    prod.save(update_fields=['image'])
                    print(f"   📸 Картинка прикреплена к {name}")

    print("-" * 30)
    print("✅ Готово! Все товары созданы с картинками.")
    print("💡 Картинки хранятся в media/products/{id}.jpg")

if __name__ == "__main__":
    fill_data()