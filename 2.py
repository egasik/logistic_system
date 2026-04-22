import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

# ВАЖНО: Импортируем твою кастомную модель User из core, а не из django.contrib.auth
from core.models import User, Profile

print("🔍 Проверка профилей пользователей...")
created_count = 0

for u in User.objects.all():
    # Проверяем, есть ли у пользователя профиль
    if not hasattr(u, 'profile'):
        Profile.objects.create(user=u)
        created_count += 1
        print(f"   ✅ Создан профиль для: {u.email}") # Используем email, так как username может не быть

if created_count == 0:
    print("   ℹ️ У всех пользователей уже есть профили.")
else:
    print(f"\n✅ Готово! Создано {created_count} новых профилей.")