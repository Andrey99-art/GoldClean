# File: core/utils.py
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

def format_duration(total_minutes):
    if total_minutes is None or total_minutes < 1:
        return _("Not specified")
    hours = total_minutes // 60
    minutes = total_minutes % 60
    parts = []
    if hours > 0:
        if hours == 1: h_word = _('hour')
        elif 1 < hours < 5: h_word = _('hours_2_4')
        else: h_word = _('hours_5_plus')
        parts.append(f"{hours} {h_word}")
    if minutes > 0:
        parts.append(f"{minutes} {_('min')}")
    return " ".join(parts)

def send_gmail_message(subject, body, recipient_list):
    print(f"--- [DEBUG] Вызвана функция отправки почты ---")
    print(f"--- [DEBUG] Получатели: {recipient_list}")
    
    if not recipient_list:
        print("--- [DEBUG] ОШИБКА: Нет получателей")
        return False
        
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False, 
        )
        print("--- [DEBUG] send_mail отработал УСПЕШНО")
        return True
    except Exception as e:
        print(f"--- [DEBUG] КРИТИЧЕСКАЯ ОШИБКА send_mail: {e}")
        return False