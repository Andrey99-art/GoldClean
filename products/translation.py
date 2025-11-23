# File: products/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Service, AdditionalService, KitchenCleaningFeature, ServiceFeature

@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    # ИЗМЕНЕНИЕ: Добавляем новое поле для перевода
    fields = ('name', 'short_description')

@register(AdditionalService)
class AdditionalServiceTranslationOptions(TranslationOptions):
    # ИЗМЕНЕНИЕ: Добавляем поле price_description в кортеж fields
    fields = ('name', 'price_description')

@register(KitchenCleaningFeature)
class KitchenCleaningFeatureTranslationOptions(TranslationOptions):
    fields = ('title',)

@register(ServiceFeature)
class ServiceFeatureTranslationOptions(TranslationOptions):
    fields = ('description',)