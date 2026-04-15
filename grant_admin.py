import os
import django

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from core.models import User

EMAIL = 'egasik112@yandex.ru'

try:
    user = User.objects.get(email=EMAIL)
    
    # Выдаём полные права
    user.is_staff = True      # Доступ в админку /panel/
    user.is_superuser = True  # Полный доступ ко всему
    user.role = 'admin'       # Роль для меню системы
    user.save()
    
    print(f"✅ Готово! Админские права выданы: {user.first_name} {user.last_name} ({user.email})")
    
except User.DoesNotExist:
    print(f"❌ Пользователь с почтой {EMAIL} не найден в базе.")
    print("💡 Проверь точный email в таблице core_user через Workbench.")