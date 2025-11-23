from modeltranslation.translator import register, TranslationOptions
from .models import GalleryImage

@register(GalleryImage)
class GalleryImageTranslationOptions(TranslationOptions):
    fields = ('title',)