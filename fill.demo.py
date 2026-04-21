import os
import sys
import django
import shutil
from pathlib import Path

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from django.conf import settings
from core.models import Category, Product, Stock

# === НАСТРОЙКИ ИЗОБРАЖЕНИЙ ===
# Здесь указываем ПУТИ к картинкам внутри репозитория.
# Скрипт скопирует их из demo_images/ в media/products/
PRODUCT_IMAGES = {
    "Смартфон NOTHING PHONE 3": "media/products/6.png",
    "Ноутбук ASUS VivoBook 15": "media/products/7.png",
    "Наушники Sony WH-1000XM5": "media/products/3.png",
    "Диван угловой 'Комфорт'": "media/products/8.png",
    "Дрель-шуруповерт Bosch": "media/products/9.png",
    "Умная лампа Philips": "media/products/10.png",
    "Кроссовки Nike Air Max": "media/products/11.png",
    "Куртка зимняя мужская": "media/products/12.png",
    "Рюкзак Xiaomi City": "media/products/13.png",
    "Велосипед Stark Tanuki": "media/products/14.png",
    "Гантели разборные 20кг": "media/products/15.png",
    "Коврик для йоги Pro": "media/products/16.png",
    "Конструктор LEGO City": "media/products/17.png",
    "Коляска 2 в 1": "media/products/18.png",
    "Игра Монополия": "media/products/19.png",
}

# Данные для заполнения
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

def copy_and_rename_image(relative_src_path, product_id):
    """
    Копирует картинку из репозитория (demo_images/) в media/products/
    и переименовывает её в {product_id}.jpg
    """
    if not relative_src_path:
        return None

    # Пути
    base_dir = Path(settings.BASE_DIR)
    src_file = base_dir / relative_src_path
    dst_dir = base_dir / 'media' / 'products'
    dst_file = dst_dir / f"{product_id}.png"
    
    # Создаём папку назначения, если нет
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Проверяем, существует ли исходный файл
    if not src_file.exists():
        print(f"   ⚠️ Файл не найден: {src_file}")
        return None

    try:
        # Копируем файл (перезаписываем, если уже есть)
        shutil.copy2(src_file, dst_file)
        print(f"   ✅ Скопировано: {relative_src_path} → products/{product_id}.png")
        return f"products/{product_id}.png"
    except Exception as e:
        print(f"   ❌ Ошибка копирования: {e}")
        return None

def fill_data():
    print("🚀 Начинаем заполнение базы демо-данными (с локальными картинками)...")

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
            image_path = PRODUCT_IMAGES.get(name)
            
            if image_path:
                # Копируем и переименовываем в {id}.jpg
                saved_path = copy_and_rename_image(image_path, prod.id)
                
                if saved_path:
                    # Обновляем поле image у товара
                    prod.image = saved_path
                    prod.save(update_fields=['image'])
                    print(f"   📸 Картинка прикреплена к {name} (ID: {prod.id})")

    print("-" * 30)
    print("✅ Готово! Все товары созданы с картинками.")
    print("💡 Картинки хранятся в media/products/{id}.png")
    print("📦 Не забудь добавить media/products/ в Git, чтобы они попали в репозиторий!")

if __name__ == "__main__":
    fill_data()