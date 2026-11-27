from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def order_notification(sender, instance, created, **kwargs):
    from core.telegram import notify_order_status
    try:
        if not created:
            # Уведомление об изменении статуса (не при создании)
            if hasattr(instance, '_original_status') and instance._original_status != instance.status:
                notify_order_status(instance)
    except Exception:
        pass  # Не ломаем сохранение из-за Telegram
