import os
import django
import argparse

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_system.settings')
django.setup()

from core.models import User


def grant_admin(email: str) -> int:
    try:
        user = User.objects.get(email=email)
        user.is_staff = True
        user.is_superuser = True
        user.is_admin = True
        user.save(update_fields=["is_staff", "is_superuser", "is_admin"])
        print(f"OK: admin rights granted for {user.email}")
        return 0
    except User.DoesNotExist:
        print(f"ERROR: user with email {email} not found.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grant admin rights to a user by email.")
    parser.add_argument("--email", default="egasik112@yandex.ru", help="User email")
    args = parser.parse_args()
    raise SystemExit(grant_admin(args.email))