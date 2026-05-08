import os
import django

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from core.models import User

# 👇 МЕНЯЙ EMAIL ЗДЕСЬ ПЕРЕД ЗАПУСКОМ
TARGET_EMAIL = "1234@1234.com"

try:
    user = User.objects.get(email=TARGET_EMAIL)
    if user.is_admin:
        print(f"⚠️ Пользователь {TARGET_EMAIL} уже является администратором.")
    else:
        user.is_admin = True
        user.is_staff = True  
        user.is_active = True
        user.save()
        print(f"✅ Права администратора успешно выданы: {TARGET_EMAIL}")
except User.DoesNotExist:
    print(f"❌ Пользователь с email {TARGET_EMAIL} не найден в базе.")