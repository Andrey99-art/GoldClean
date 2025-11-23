import os
import django

# 1. Настраиваем окружение Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("\n--- ЗАПУСК ТЕСТА ПОЧТЫ ---")
print(f"Пользователь (из настроек): {settings.EMAIL_HOST_USER}")

# Проверка пароля
password = settings.EMAIL_HOST_PASSWORD
if password:
    print(f"Пароль: ЗАГРУЖЕН (длина {len(password)} символов)")
    # Проверка на пробелы (частая ошибка)
    if " " in password:
        print("!!! ВНИМАНИЕ: В пароле обнаружены пробелы! Удалите их в файле .env")
else:
    print("!!! ОШИБКА: Пароль не найден. Проверь файл .env и переменную EMAIL_HOST_PASSWORD")

print("Попытка отправки...")

try:
    send_mail(
        subject='Проверка связи Gold Clean',
        message='Ура! Если пришло это письмо, значит SMTP настроен верно.',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER], # Отправляем самому себе
        fail_silently=False,
    )
    print("\n✅ УСПЕХ! Письмо отправлено без ошибок.")
    print(f"Проверь входящие (или папку Спам) на почте: {settings.EMAIL_HOST_USER}")
except Exception as e:
    print("\n❌ ОШИБКА ОТПРАВКИ:")
    print(e)

print("--- КОНЕЦ ТЕСТА ---\n")