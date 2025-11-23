# File: orders/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from products.models import Service, AdditionalService

class City(models.Model):
    name = models.CharField(_("City name"), max_length=100, unique=True)
    delivery_charge = models.DecimalField(_("Delivery charge"), max_digits=10, decimal_places=2, default=0.00)
    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")
        ordering = ['name']
    def __str__(self):
        return f"{self.name} (+{self.delivery_charge} zł)"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("User"))
    
    # HINT: ИЗМЕНЕНИЕ ЗДЕСЬ. Добавляем related_name, чтобы разрешить конфликт.
    service = models.ForeignKey(
        Service, 
        on_delete=models.PROTECT, 
        verbose_name=_("Service"),
        related_name='orders' # <-- ВОТ РЕШЕНИЕ
    )

    rooms_count = models.PositiveIntegerField(verbose_name=_("Number of rooms"), null=True, blank=True)
    bathrooms_count = models.PositiveIntegerField(verbose_name=_("Number of bathrooms"), null=True, blank=True)
    sqm = models.PositiveIntegerField(_("Area (sqm)"), null=True, blank=True)
    window_count = models.PositiveIntegerField(_("Number of windows"), null=True, blank=True)
    additional_services_details = models.JSONField( default=list,  blank=True,  verbose_name=_("Additional Services Details"))
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total price"))
    delivery_charge = models.DecimalField(_("Delivery charge"), max_digits=10, decimal_places=2, default=0.00)
    frequency = models.CharField(_("Frequency"), max_length=20, default='one_time', blank=True)
    bring_vacuum_cleaner = models.BooleanField(_("Bring vacuum cleaner"), default=False)
    is_private_house = models.BooleanField(_("Private house"), default=False)
    estimated_duration_minutes = models.PositiveIntegerField(_("Estimated duration (minutes)"), null=True, blank=True)
    customer_name = models.CharField(max_length=100, verbose_name=_("Full name"))
    customer_phone = models.CharField(max_length=20, verbose_name=_("Phone number"))
    customer_email = models.EmailField(verbose_name=_("Email address"))
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("City"))
    street = models.CharField(_("Street"), max_length=255)
    postal_code = models.CharField(_("Postal code"), max_length=10)
    building_number = models.CharField(_("Building number"), max_length=10)
    apartment_number = models.CharField(_("Apartment number"), max_length=10, blank=True)
    entrance = models.CharField(_("Entrance"), max_length=10, blank=True)
    floor = models.CharField(_("Floor"), max_length=10, blank=True)
    intercom_code = models.CharField(_("Intercom code"), max_length=20, blank=True)
    comments = models.TextField(_("Additional comments"), blank=True, null=True)
    cleaning_date = models.DateField(verbose_name=_("Desired cleaning date"))
    cleaning_time = models.TimeField(verbose_name=_("Desired time"))
    STATUS_CHOICES = [('new', _('New')), ('in_progress', _('In Progress')), ('completed', _('Completed')), ('canceled', _('Canceled')),]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_("Order Status"))
    PAYMENT_CHOICES = [('cash', _('Cash')), ('card', _('Card Online')),]
    payment_method = models.CharField(_("Payment method"), max_length=20, choices=PAYMENT_CHOICES, default='cash')
    PAYMENT_STATUS_CHOICES = [('pending', _('Pending')), ('paid', _('Paid')), ('failed', _('Failed')),]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name=_("Payment Status"))
    stripe_session_id = models.CharField(max_length=255, blank=True, verbose_name=_("Stripe Session ID"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Creation date"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Update date"))


    def get_additional_services_display(self):
        """Возвращает отформатированную строку с доп. услугами для админки и писем."""
        if not self.additional_services_details:
            return "---"

        lines = []
        for item in self.additional_services_details:
            quantity_str = f" x {item['quantity']}" if item.get('quantity', 1) > 1 else ""
            lines.append(f"{item['name']}{quantity_str}")
        return ", ".join(lines)

    get_additional_services_display.short_description = _("Additional Services")

    def __str__(self):
        return f"Order #{self.pk} for {self.customer_name}"

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created_at']