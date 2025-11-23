# File: products/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _

class Service(models.Model):    
    # ... (эта модель остается без изменений)
    name = models.CharField(max_length=100, verbose_name=_("Service Name"))
    short_description = models.TextField(_("Short Description"), max_length=200, blank=True, help_text=_("A brief description for service cards, max 200 characters."))
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, null=True, blank=True, help_text=_("A unique slug for the service URL, e.g., 'kitchen-cleaning'"))
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Base Price"))
    price_per_room = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price per extra room"))
    price_per_bathroom = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price per extra bathroom"))
    base_duration_minutes = models.PositiveIntegerField(default=60, verbose_name=_("Base duration (minutes)"))
    is_sqm_based = models.BooleanField(default=False, verbose_name=_("Is Sqm Based?"))
    price_per_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Price Per Sqm / Per Window"))
    is_window_service = models.BooleanField(default=False, verbose_name=_("Is Window Cleaning Service?"))
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    def __str__(self): return self.name
    class Meta:
        verbose_name = _("Основная услуга")
        verbose_name_plural = _("Основные услуги")
        ordering = ['order']

class AdditionalService(models.Model):
    # ... (поля name, price, etc. остаются)
    name = models.CharField(max_length=100, verbose_name=_("Service Name"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    
    # --- НОВОЕ ПОЛЕ ---
    price_description = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Price Description"),
        help_text=_("Ex: 'per item', 'per hour'. Leave empty if not needed.")
    )
    
    is_quantity_based = models.BooleanField(
        default=False, 
        verbose_name=_("Is quantity-based?"),
        help_text=_("If checked, a quantity selector will be shown instead of a checkbox.")
    )

    is_for_kitchen = models.BooleanField(_("For Kitchen Cleaning Page"), default=False, help_text=_("Check this if the service should be displayed on the Kitchen Cleaning page."))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"), help_text=_("Services with a lower number will be displayed first."))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    duration_minutes = models.PositiveIntegerField(_("Duration (minutes)"), default=0, help_text=_("How many minutes does this service add to the total cleaning time?"))
    icon = models.ImageField(upload_to='service_icons/', blank=True, null=True, verbose_name=_("Icon"))
    def __str__(self): return self.name
    class Meta:
        verbose_name = _("Дополнительная услуга")
        verbose_name_plural = _("Дополнительные услуги")
        ordering = ['order']

class KitchenCleaningFeature(models.Model):
    # ... (эта модель без изменений)
    CATEGORY_CHOICES = [('wash', _('Wash inside and out')), ('wipe', _('Wipe and clean')),]
    title = models.CharField(_("Title"), max_length=100)
    icon = models.FileField(_("Icon"), upload_to='kitchen_features_icons/')
    category = models.CharField(_("Category"), max_length=10, choices=CATEGORY_CHOICES, default='wash')
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    def __str__(self): return self.title
    class Meta:
        verbose_name = _("Kitchen Cleaning Feature")
        verbose_name_plural = _("Kitchen Cleaning Features")
        ordering = ['category', 'order']

class ServiceFeature(models.Model):
    # ... (эта модель без изменений)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='features', verbose_name=_("Service"))
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    def __str__(self): return self.description
    class Meta:
        verbose_name = _("Service Feature")
        verbose_name_plural = _("Service Features")
        ordering = ['order']