# File: orders/admin.py

from django.contrib import admin
from .models import Order, City
from core.utils import format_duration

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'delivery_charge')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'city', 'total_price', 'status', 
        'payment_method', 'payment_status', 'cleaning_date', 
        'formatted_duration', 'created_at'
    )
    list_filter = (
        'status', 'payment_status', 'payment_method', 'cleaning_date', 
        'city', 'is_private_house', 'bring_vacuum_cleaner', 'frequency'
    )
    search_fields = ('id', 'customer_name', 'customer_phone', 'customer_email', 'street', 'stripe_session_id')
    ordering = ('-created_at',)
    
    readonly_fields = (
        'created_at', 'updated_at', 'total_price', 'delivery_charge',
        'payment_status', 'stripe_session_id', 'get_additional_services_display' # NEW: Добавляем наш метод
    )

    fieldsets = (
        ('Основная информация', {'fields': ('id', 'service', 'total_price', 'delivery_charge')}),
        ('Статус и Оплата', {'fields': ('status', 'payment_method', 'payment_status', 'stripe_session_id')}),
        ('Детали уборки', {
            # ИЗМЕНЕНИЕ: Заменяем поле на наш метод
            'fields': ('frequency', 'rooms_count', 'bathrooms_count', 'sqm', 'window_count', 'get_additional_services_display', 'is_private_house', 'bring_vacuum_cleaner')
        }),
        ('Клиент и Адрес', {'fields': ('customer_name', 'customer_phone', 'customer_email', 'city', 'street', 'postal_code', 'building_number', 'apartment_number', 'entrance', 'floor', 'intercom_code')}),
        ('Дата и Время', {'fields': ('cleaning_date', 'cleaning_time', 'estimated_duration_minutes', 'created_at', 'updated_at')}),
        ('Дополнительно', {'fields': ('comments', 'user')}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields

    @admin.display(description='Длительность')
    def formatted_duration(self, obj):
        if obj.estimated_duration_minutes:
            return format_duration(obj.estimated_duration_minutes)
        return "N/A"