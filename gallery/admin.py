from django.contrib import admin
from .models import GalleryImage
from modeltranslation.admin import TranslationAdmin

@admin.register(GalleryImage)
class GalleryImageAdmin(TranslationAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)