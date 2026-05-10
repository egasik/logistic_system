"""
Скрипт для создания суперпользователя в Django
Используется SQLite как основная БД
"""

import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Данные для создания суперпользователя
EMAIL = 'admin@logisticspro.ru'
FIRST_NAME = 'Администратор'
LAST_NAME = 'Системы'
PASSWORD = '123'

# Проверка существования пользователя
if User.objects.filter(email=EMAIL).exists():
    print(f"Пользователь с email '{EMAIL}' уже существует.")
    user = User.objects.get(email=EMAIL)
    print(f"ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Имя: {user.first_name}")
    print(f"Фамилия: {user.last_name}")
    print(f"Is Admin: {user.is_admin}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Is Superuser: {user.is_superuser}")
else:
    # Создание суперпользователя
    user = User.objects.create_superuser(
        email=EMAIL,
        password=PASSWORD,
        first_name=FIRST_NAME,
        last_name=LAST_NAME,
    )
    print("=" * 50)
    print("СУПЕРПОЛЬЗОВАТЕЛЬ УСПЕШНО СОЗДАН!")
    print("=" * 50)
    print(f"Email: {EMAIL}")
    print(f"Пароль: {PASSWORD}")
    print(f"Имя: {FIRST_NAME}")
    print(f"Фамилия: {LAST_NAME}")
    print(f"Is Admin: {user.is_admin}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Is Superuser: {user.is_superuser}")
    print("=" * 50)
    print("\nВы можете войти в админ-панель по адресу:")
    print("http://127.0.0.1:8000/admin/")
    print("\nИли в систему по адресу:")
    print("http://127.0.0.1:8000/login/")
