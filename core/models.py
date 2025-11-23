# File: core/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

class CleaningArea(models.Model):
    title = models.CharField(_("Title"), max_length=100, help_text=_("e.g., 'Bathroom', 'Kitchen'"))
    image = models.ImageField(_("Image"), upload_to='cleaning_areas/')
    order = models.PositiveIntegerField(_("Display Order"), default=0, help_text=_("Lower numbers are displayed first."))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Cleaning Area")
        verbose_name_plural = _("Cleaning Areas")
        ordering = ['order']

class FeaturePoint(models.Model):
    area = models.ForeignKey(
        CleaningArea, 
        on_delete=models.CASCADE, 
        related_name='feature_points', 
        verbose_name=_("Cleaning Area")
    )
    description = models.CharField(_("Description"), max_length=200)
    position_x = models.FloatField(
        _("Position X (%)"), 
        default=50.0, 
        help_text=_("Horizontal position from left to right, in percent (e.g., 25.5)")
    )
    position_y = models.FloatField(
        _("Position Y (%)"), 
        default=50.0, 
        help_text=_("Vertical position from top to bottom, in percent (e.g., 70)")
    )

    def __str__(self):
        return self.description

class SiteConfiguration(SingletonModel):
    cancellation_fee = models.DecimalField(
        _("Cancellation Fee (zł)"),
        max_digits=10,
        decimal_places=2,
        default=50.00,
        help_text=_("The fee charged for cancellations made less than 24 hours in advance.")
    )
    services_page_enabled = models.BooleanField(
        _("Показывать страницу 'Услуги'"),
        default=True,
        help_text=_("Если флаг выключен, ссылка на страницу 'Услуги' исчезнет из навигации сайта.")
    )
    telegram_link = models.URLField(
        _("Telegram Link"),
        max_length=255, 
        blank=True,     
        null=True, 
        help_text=_("Full URL to the Telegram account, e.g., https://t.me/your_account")
    )

    def __str__(self):
        # --- ИСПРАВЛЕНИЕ ---
        # Оборачиваем ленивый перевод в str(), чтобы вернуть реальную строку
        return str(_("Site Configuration"))

    class Meta:
        verbose_name = _("Site Configuration")