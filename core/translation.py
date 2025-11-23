# core/translation.py

from modeltranslation.translator import register, TranslationOptions
from .models import CleaningArea, FeaturePoint

@register(CleaningArea)
class CleaningAreaTranslationOptions(TranslationOptions):
    fields = ('title',)
    required_languages = ('pl',)

@register(FeaturePoint)
class FeaturePointTranslationOptions(TranslationOptions):
    fields = ('description',)
    required_languages = ('pl',)