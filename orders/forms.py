# File: orders/forms.py

from django import forms
from .models import Order, City
from django.utils.translation import gettext_lazy as _
from products.models import Service, AdditionalService 


class OrderCreateForm(forms.ModelForm):
    city = forms.ModelChoiceField(
        queryset=City.objects.order_by('delivery_charge', 'name'),
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
        label=_("City")
    )
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_CHOICES, # Берем варианты прямо из модели
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_("Payment method")
    )

    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'city', 'street', 'postal_code', 'building_number', 
            'apartment_number', 'entrance', 'floor', 'intercom_code',
            'cleaning_date', 'cleaning_time',
            'comments',
            'payment_method'  # <-- 1. ДОБАВЛЕНО ПОЛЕ
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Your full name')}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+48 123 456 789'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Street')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Postal code')}),
            'building_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Building No.')}),
            'apartment_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Apartment No.')}),
            'entrance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Entrance')}),
            'floor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Floor')}),
            'intercom_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Intercom code')}),
            'cleaning_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'placeholder': _('Select date')}),
            'cleaning_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'text', 'placeholder': _('Select time')}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('e.g., parking details, how to find the entrance...')}),
            
            # --- 2. ДОБАВЛЕН ВИДЖЕТ ДЛЯ РАДИО-КНОПОК ---
            # Этот виджет превратит стандартный <select> в <input type="radio">,
            # что гораздо удобнее для пользователя при выборе из двух опций.
            'payment_method': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apartment_number'].required = False
        self.fields['entrance'].required = False
        self.fields['floor'].required = False
        self.fields['intercom_code'].required = False
        self.fields['comments'].required = False

# ... (OrderFullEditForm остается без изменений) ...
class OrderFullEditForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_window_service=False),
        label=_("Cleaning Type"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    additional_services = forms.ModelMultipleChoiceField(
        queryset=AdditionalService.objects.filter(is_active=True),
        label=_("Additional Services"),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Order
        fields = [
            'service', 'rooms_count', 'bathrooms_count', 'sqm',
            'additional_services', 'bring_vacuum_cleaner', 'is_private_house',
            'cleaning_date', 'cleaning_time', 'comments'
        ]
        widgets = {
            'rooms_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'bathrooms_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'sqm': forms.NumberInput(attrs={'class': 'form-control'}),
            'bring_vacuum_cleaner': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_private_house': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cleaning_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'text'}),
            'cleaning_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'text'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }