# File: products/admin.py

from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from .models import Service, AdditionalService, KitchenCleaningFeature, ServiceFeature

class ServiceFeatureInline(TranslationTabularInline):
    model = ServiceFeature
    extra = 1
    ordering = ('order',)
    fields = ('order', 'description')

@admin.register(Service)
class ServiceAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'base_price', 'order') 
    list_filter = ('is_window_service',)
    ordering = ('order',)
    prepopulated_fields = {'slug': ('name_pl',)}
    fieldsets = (
        (None, {'fields': ('name', 'short_description', 'slug', 'base_price', 'order')}),
        ('Pricing Details', {'fields': ('price_per_room', 'price_per_bathroom', 'is_sqm_based', 'price_per_sqm')}),
        ('Configuration', {'fields': ('base_duration_minutes', 'is_window_service')}),
    )
    inlines = [ServiceFeatureInline]

@admin.register(AdditionalService)
class AdditionalServiceAdmin(TabbedTranslationAdmin):
    # ИЗМЕНЕНИЕ: Добавляем новое поле в отображение и редактирование
    list_display = ('name', 'price', 'is_active', 'order', 'is_for_kitchen', 'is_quantity_based')
    list_filter = ('is_active', 'is_for_kitchen', 'is_quantity_based')
    list_editable = ('price', 'order', 'is_active', 'is_for_kitchen', 'is_quantity_based')
    ordering = ('order',)
    actions = ['make_active', 'make_inactive']
    
    @admin.action(description='Сделать выбранные услуги активными (показать на сайте)')
    def make_active(self, request, queryset): queryset.update(is_active=True)
    
    @admin.action(description='Сделать выбранные услуги неактивными (скрыть с сайта)')
    def make_inactive(self, request, queryset): queryset.update(is_active=False)

@admin.register(KitchenCleaningFeature)
class KitchenCleaningFeatureAdmin(TabbedTranslationAdmin):
    list_display = ('get_title_with_fallback', 'category', 'order')
    list_filter = ('category',)
    list_editable = ('category', 'order')    
    ordering = ('order',)
    
    @admin.display(description="Название (Title)")
    def get_title_with_fallback(self, obj): return obj.title or f"Запись #{obj.id} (пусто)"