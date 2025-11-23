from django.contrib import admin
from .models import Review
from modeltranslation.admin import TranslationAdmin

@admin.register(Review)
class ReviewAdmin(TranslationAdmin):
    list_display = ('author_name', 'rating', 'is_active', 'created_at', 'order', 'show_date')  # Added show_date
    list_editable = ('is_active', 'order', 'show_date')  # Made show_date editable in list view
    list_filter = ('is_active', 'rating', 'show_date')  # Added filter for show_date
    
    # Display created_at as read-only in the change form
    readonly_fields = ('created_at',)