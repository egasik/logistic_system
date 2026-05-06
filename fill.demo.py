import os
import django
import shutil
from pathlib import Path

# === НАСТРОЙКА DJANGO ===
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from django.utils.text import slugify
from django.utils import timezone
from core.models import Category, Brand, Product, ProductImage

# === НАСТРОЙКИ ИЗОБРАЖЕНИЙ ===
# Пути к картинкам внутри проекта (относительно корня)
# Скрипт скопирует их в media/products/{id}.jpg
PRODUCT_IMAGES = {
    "Смартфон NOTHING PHONE 3": "demo_images/7704811119_Exgc77V.webp",
    "Ноутбук ASUS VivoBook 15": "demo_images/7.png",
    "Наушники Sony WH-1000XM5": "demo_images/3.png",
    "Диван угловой 'Комфорт'": "demo_images/8.png",
    "Дрель-шуруповерт Bosch": "demo_images/9.png",
    "Умная лампа Philips": "demo_images/10.png",
    "Кроссовки Nike Air Max": "demo_images/11.png",
    "Куртка зимняя мужская": "demo_images/12.png",
    "Рюкзак Xiaomi City": "demo_images/13.png",
    "Велосипед Stark Tanuki": "demo_images/14.png",
    "Гантели разборные 20кг": "demo_images/15.png",
    "Коврик для йоги Pro": "demo_images/16.png",
    "Конструктор LEGO City": "demo_images/17.png",
    "Коляска 2 в 1": "demo_images/18.png",
    "Игра Монополия": "demo_images/19.png",
}

# Данные для заполнения (товары, как в оригинале)
PRODUCTS = [
    ("Смартфон NOTHING PHONE 3", "Мощный смартфон с прозрачным дизайном.", 40000, "Техника и электроника", "Nothing"),
    ("Ноутбук ASUS VivoBook 15", "Легкий ноутбук для работы и учебы.", 52900, "Техника и электроника", "ASUS"),
    ("Наушники Sony WH-1000XM5", "Топовое шумоподавление и звук.", 34990, "Техника и электроника", "Sony"),
    ("Диван угловой 'Комфорт'", "Просторный диван с механизмом раскладки.", 45000, "Дом и сад", "Мебель-Про"),
    ("Дрель-шуруповерт Bosch", "Надежный инструмент для дома.", 6500, "Дом и сад", "Bosch"),
    ("Умная лампа Philips", "Управление через приложение и свет.", 1890, "Дом и сад", "Philips"),
    ("Кроссовки Nike Air Max", "Стильные и удобные кроссовки.", 12990, "Одежда и обувь", "Nike"),
    ("Куртка зимняя мужская", "Теплая куртка для сильных морозов.", 8900, "Одежда и обувь", "WinterWear"),
    ("Рюкзак Xiaomi City", "Вместительный рюкзак для ноутбука.", 2490, "Одежда и обувь", "Xiaomi"),
    ("Велосипед Stark Tanuki", "Горный велосипед для прогулок.", 18500, "Спорт и отдых", "Stark"),
    ("Гантели разборные 20кг", "Набор гантелей для домашних тренировок.", 3200, "Спорт и отдых", "FitPro"),
    ("Коврик для йоги Pro", "Нескользящий коврик 6мм.", 1290, "Спорт и отдых", "YogaLife"),
    ("Конструктор LEGO City", "Полицейский участок, 668 деталей.", 4590, "Детские товары", "LEGO"),
    ("Коляска 2 в 1", "Универсальная коляска для новорожденных.", 28900, "Детские товары", "BabyCare"),
    ("Игра Монополия", "Классическая экономическая настолка.", 2190, "Детские товары", "Hasbro"),
]

CATEGORIES = [
    ("Техника и электроника", "Смартфоны, ноутбуки и гаджеты."),
    ("Дом и сад", "Мебель, инструменты и товары для уюта."),
    ("Одежда и обувь", "Мужская и женская одежда, кроссовки."),
    ("Спорт и отдых", "Инвентарь, тренажеры и туризм."),
    ("Детские товары", "Игрушки, коляски и одежда для детей."),
]

BRANDS = [
    ("Nothing", "nothing"),
    ("ASUS", "asus"),
    ("Sony", "sony"),
    ("Мебель-Про", "mebel-pro"),
    ("Bosch", "bosch"),
    ("Philips", "philips"),
    ("Nike", "nike"),
    ("WinterWear", "winterwear"),
    ("Xiaomi", "xiaomi"),
    ("Stark", "stark"),
    ("FitPro", "fitpro"),
    ("YogaLife", "yogalife"),
    ("LEGO", "lego"),
    ("BabyCare", "babycare"),
    ("Hasbro", "hasbro"),
]


def get_unique_slug(model, base_value):
    """Генерирует уникальный slug"""
    base = slugify(base_value) or "item"
    candidate = base
    idx = 2
    while model.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{idx}"
        idx += 1
    return candidate


def copy_image_to_media(relative_src_path, product_id):
    """Копирует изображение в media/products/{id}.jpg"""
    if not relative_src_path:
        return None
    
    base_dir = Path(__file__).resolve().parent.parent
    src_file = base_dir / relative_src_path
    dst_dir = base_dir / 'media' / 'products'
    dst_file = dst_dir / f"{product_id}.jpg"
    
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    if not src_file.exists():
        print(f"   ⚠️ Файл не найден: {src_file}")
        return None
    
    try:
        shutil.copy2(src_file, dst_file)
        print(f"   ✅ Картинка: {relative_src_path} → products/{product_id}.jpg")
        return f"products/{product_id}.jpg"
    except Exception as e:
        print(f"   ❌ Ошибка копирования: {e}")
        return None


def fill_data():
    print("🛒 Начинаем заполнение базы демо-данными (товары)...")

    # 1. Создаём категории
    print("📁 Создаю категории...")
    cat_objects = {}
    for name, desc in CATEGORIES:
        slug = get_unique_slug(Category, name)
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'description': desc}
        )
        cat_objects[name] = cat
        print(f"   + Категория: {name}")

    # 2. Создаём бренды
    print("🏷️ Создаю бренды...")
    brand_objects = {}
    for name, slug in BRANDS:
        brand, _ = Brand.objects.get_or_create(
            slug=slug,
            defaults={'name': name}
        )
        brand_objects[name] = brand
        print(f"   + Бренд: {name}")

    # 3. Создаём товары
    print("📦 Создаю товары...")
    for name, desc, price, cat_name, brand_name in PRODUCTS:
        category = cat_objects.get(cat_name)
        brand = brand_objects.get(brand_name)
        
        if not category:
            print(f"   ⚠️ Категория '{cat_name}' не найдена, пропускаю '{name}'")
            continue
        
        # Генерируем slug и создаём/обновляем товар
        slug = get_unique_slug(Product, name)
        product, created = Product.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'description': desc,
                'price': price,
                'category': category,
                'brand': brand,
                'stock': 10,
                'sku': f"SKU-{slug[:10].upper()}",
                'is_active': True,  # ← правильное поле (не status!)
            }
        )
        
        if not created:
            # Обновляем существующий товар
            product.description = desc
            product.price = price
            product.category = category
            product.brand = brand
            product.stock = 10
            product.is_active = True
            product.save()
            print(f"   ✏️ Обновлён: {name}")
        else:
            print(f"   ✅ Создан: {name}")
        
        # === ПРИКРЕПЛЕНИЕ КАРТИНКИ ===
        image_path = PRODUCT_IMAGES.get(name)
        if image_path:
            saved_path = copy_image_to_media(image_path, product.id)
            if saved_path:
                # Создаём запись в ProductImage (многие картинки на товар)
                ProductImage.objects.get_or_create(
                    product=product,
                    defaults={'path': saved_path, 'sort_order': 0}
                )
                print(f"   🖼️ Картинка прикреплена к {name}")

    print("\n" + "="*50)
    print("🎉 Демо-данные успешно загружены!")
    print(f"📁 Картинки сохранены в: media/products/")
    print("🔐 Админ: создай через `python manage.py createsuperuser`")
    print("="*50)


if __name__ == "__main__":
    fill_data()