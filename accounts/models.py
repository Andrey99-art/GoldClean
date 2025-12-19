# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Profile(models.Model):
    """
    Профиль пользователя с информацией о штрафах и скидках.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name=_("User")
    )
    
    # Существующее поле штрафов
    penalty_balance = models.DecimalField(
        _("Penalty Balance"),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    # === НОВЫЕ ПОЛЯ ДЛЯ СКИДКИ НОВОГО КЛИЕНТА ===
    
    is_new_client = models.BooleanField(
        _('Is New Client'),
        default=True,
        help_text=_('New clients get 25% discount on first order')
    )
    
    first_order_discount_used_at = models.DateTimeField(
        _('First Order Discount Used'),
        null=True,
        blank=True
    )
    
    # Связь с Lead (если пользователь пришёл через pop-up форму)
    source_lead = models.ForeignKey(
        'core.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_profiles',
        verbose_name=_('Source Lead')
    )
    
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        status = "NEW" if self.is_new_client else ""
        return f"Profile for {self.user.username} {status}".strip()
    
    def use_new_client_discount(self):
        """
        Отмечает использование скидки нового клиента.
        Вызывать после первого заказа.
        """
        if self.is_new_client:
            self.is_new_client = False
            self.first_order_discount_used_at = timezone.now()
            self.save(update_fields=['is_new_client', 'first_order_discount_used_at', 'updated_at'])
            return True
        return False
    
    def get_new_client_discount(self):
        """Возвращает размер скидки для нового клиента (0.25 = 25%)."""
        from decimal import Decimal
        return Decimal('0.25') if self.is_new_client else Decimal('0.00')
    
    def has_penalty(self):
        """Проверяет, есть ли непогашенный штраф."""
        return self.penalty_balance > 0


# === СИГНАЛЫ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ПРОФИЛЯ ===

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создаёт профиль при регистрации пользователя."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль при сохранении пользователя."""
    if hasattr(instance, 'profile'):
        instance.profile.save()