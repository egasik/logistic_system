import os
import django
import shutil
import re
from pathlib import Path

# === НАСТРОЙКА DJANGO ===
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from django.utils.text import slugify
from django.utils import timezone
from core.models import Category, Brand, Product

# === НАСТРОЙКИ ИЗОБРАЖЕНИЙ ===
# Скрипт ищет картинки в demo_images/ по частичному совпадению с названием товара
# Поддерживает форматы: jpg, jpeg, png, webp, gif
# Имена файлов могут содержать цифры и любые символы

DEMO_IMAGES_DIR = Path(__file__).resolve().parent / 'demo_images'


def find_image_for_product(product_name):
    """Ищет изображение для товара по частичному совпадению"""
    if not DEMO_IMAGES_DIR.exists():
        print(f"   ⚠️ Папка demo_images не найдена")
        return None

    # Нормализуем название - убираем специальные символы для поиска
    normalized_name = re.sub(r'[\'"()-]', '', product_name.lower())
    name_words = set(re.findall(r'\w+', normalized_name))

    # Поддерживаемые расширения
    extensions = ['jpg', 'jpeg', 'png', 'webp', 'gif']

    best_match = None
    best_score = -1

    for file in DEMO_IMAGES_DIR.iterdir():
        if not file.is_file():
            continue

        # Имя файла без расширения
        stem = file.stem.lower()
        ext = file.suffix.lower().lstrip('.')

        if ext not in extensions:
            continue

        stem_words = set(re.findall(r'\w+', stem))

        score = 0

        # 1. Приоритет: полное совпадение ключевых слов
        for word in name_words:
            if len(word) >= 3 and word in stem_words:
                score += 10  # Вес полного совпадения (повышен)

        # 2. Бонус за слово в начале файла (например, "nothing" в "nothing_phone.jpg")
        if stem_words & name_words:
            score += 3

        # 3. Если файл начинается с цифры и в названии тоже есть цифры - бонус
        if stem[0].isdigit():
            name_digits = re.findall(r'\d+', normalized_name)
            if name_digits:
                file_num = re.findall(r'\d+', stem)
                if file_num and file_num[0] == name_digits[0]:
                    score += 8  # Вес совпадения цифр (снижен с 10)

        # 4. Штраф за слишком много слов в файле (избегаем дублирования)
        if len(stem_words) > len(name_words) * 2:
            score -= 5  # Файл слишком "мусорный"

        # 5. Дополнительный бонус за содержание ключевых слов из названия
        matching_words = len(stem_words & name_words)
        score += matching_words * 2

        if score > best_score:
            best_score = score
            best_match = file

    # Если есть минимум 5 очков совпадения - возвращаем
    if best_score >= 5:
        return best_match

    # Если не нашли, ищем по номеру в конце имени (для файлов 1.png, 2.jpg и т.д.)
    # Только если в названии ровно одна цифра и она уникальна
    all_digits = re.findall(r'\d+', normalized_name)
    if len(all_digits) == 1:
        num = all_digits[0]
        for ext in extensions:
            file = DEMO_IMAGES_DIR / f"{num}.{ext}"
            if file.exists():
                return file

    return None


def copy_image_to_media(image_path, product_id):
    """Копирует изображение в media/products/{product_id}.jpg"""
    if not image_path:
        return None
    
    base_dir = Path(__file__).resolve().parent
    dst_dir = base_dir / 'media' / 'products'
    dst_file = dst_dir / f"{product_id}.jpg"
    
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.copy2(image_path, dst_file)
        return f"products/{product_id}.jpg"
    except Exception as e:
        print(f"   ❌ Ошибка копирования: {e}")
        return None

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
        image_file = find_image_for_product(name)
        if image_file:
            saved_path = copy_image_to_media(image_file, product.id)
            if saved_path:
                # Присваиваем изображение напрямую в product.image
                product.image = saved_path
                product.save()
                print(f"   🖼️ Картинка: {image_file.name} → products/{product.id}.jpg")
        else:
            print(f"   ⚠️ Картинка не найдена для {name}")

    print("\n" + "="*50)
    print("🎉 Демо-данные успешно загружены!")
    print(f"📁 Картинки сохранены в: media/products/")
    print("🔐 Админ: создай через `python manage.py createsuperuser`")
    print("="*50)


if __name__ == "__main__":
    fill_data()