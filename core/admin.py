# File: core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from solo.admin import SingletonModelAdmin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from modeltranslation.translator import translator
from django.conf import settings
from deep_translator import GoogleTranslator

from .models import CleaningArea, FeaturePoint, SiteConfiguration, PromoBanner

# Используем TranslationTabularInline для правильного отображения вкладок
class FeaturePointInline(TranslationTabularInline):
    model = FeaturePoint
    extra = 1
    # Указываем только оригинальные имена полей.
    # modeltranslation сам позаботится о полях для каждого языка.
    fields = ('description', 'position_x', 'position_y')
    # Указываем, какой язык является "главным" для инлайна
    base_language = settings.MODELTRANSLATION_PRIMARY_LANGUAGE

@admin.register(CleaningArea)
class CleaningAreaAdmin(TabbedTranslationAdmin):
    list_display = ('order', 'title', 'image_preview')
    list_editable = ('order',)
    list_display_links = ('title',) 
    inlines = [FeaturePointInline]
    readonly_fields = ('hotspot_helper',)
    
    fieldsets = (
        (None, {'fields': ('title', 'image', 'order')}),
        ('Hotspot Helper', {
            'fields': ('hotspot_helper',),
            'description': 'Кликните на изображение ниже, чтобы получить координаты для новой точки.'
        }),
    )

    # ... (остальные методы остаются без изменений) ...
    # ... (save_model, save_formset и т.д.) ...
    
    @admin.display(description="Image Preview")
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" height="100" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    
    @admin.display(description="Image to Click")
    def hotspot_helper(self, obj):
        if obj.image:
            return format_html('<img id="hotspot-image-preview" src="{}" width="600" style="cursor: crosshair;" />', obj.image.url)
        return "Сначала загрузите изображение и сохраните объект."
    
    class Media:
        js = ('js/admin_hotspot_helper.js',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if '_autotranslate' in request.POST:
            self._translate_model(obj, request)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if '_autotranslate' in request.POST:
            self._translate_formset(formset, request)

    def _translate_model(self, obj, request):
        original_lang = settings.MODELTRANSLATION_PRIMARY_LANGUAGE
        other_langs = [lang[0] for lang in settings.LANGUAGES if lang[0] != original_lang]
        
        translation_options = translator.get_options_for_model(type(obj))
        translated_fields = translation_options.fields

        try:
            google_translator = GoogleTranslator()
            for field_name in translated_fields:
                original_value = getattr(obj, f"{field_name}_{original_lang}")
                if original_value:
                    for lang_code in other_langs:
                        if not getattr(obj, f"{field_name}_{lang_code}"):
                            translated_value = google_translator.translate(original_value, source=original_lang, target=lang_code)
                            setattr(obj, f"{field_name}_{lang_code}", translated_value)
            obj.save()
            self.message_user(request, "Автоперевод основного объекта выполнен.")
        except Exception as e:
            self.message_user(request, f"Ошибка перевода основного объекта: {e}", level='error')
    
    def _translate_formset(self, formset, request):
        original_lang = settings.MODELTRANSLATION_PRIMARY_LANGUAGE
        other_langs = [lang[0] for lang in settings.LANGUAGES if lang[0] != original_lang]

        try:
            google_translator = GoogleTranslator()
            for form in formset:
                if hasattr(form, 'instance') and form.instance.pk:
                    instance = form.instance
                    translation_options = translator.get_options_for_model(type(instance))
                    translated_fields = translation_options.fields
                    
                    should_save = False
                    for field_name in translated_fields:
                        original_value = getattr(instance, f"{field_name}_{original_lang}")
                        if original_value:
                            for lang_code in other_langs:
                                if not getattr(instance, f"{field_name}_{lang_code}"):
                                    translated_value = google_translator.translate(original_value, source=original_lang, target=lang_code)
                                    setattr(instance, f"{field_name}_{lang_code}", translated_value)
                                    should_save = True
                    if should_save:
                        instance.save()
            self.message_user(request, "Автоперевод связанных объектов выполнен.")
        except Exception as e:
            self.message_user(request, f"Ошибка перевода связанных объектов: {e}", level='error')

    change_form_template = 'admin/autotranslate_change_form.html'


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonModelAdmin):
    pass

@admin.register(PromoBanner)
class PromoBannerAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'content_type', 'is_active', 'is_currently_visible', 'priority', 'date_range', 'preview_thumbnail')
    list_filter = ('is_active', 'content_type', 'border_style')
    list_editable = ('is_active', 'priority')
    search_fields = ('name', 'title', 'description')
    ordering = ['-priority', '-created_at']
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('name', 'is_active', 'priority')
        }),
        (_('Content Type'), {
            'fields': ('content_type',),
            'description': _('Choose what type of content to display')
        }),
        (_('Media Content'), {
            'fields': ('image', 'video_file', 'lottie_json'),
            'classes': ('collapse',),
            'description': _('Upload media based on selected content type')
        }),
        (_('Text Content'), {
            'fields': ('title', 'description'),
        }),
        (_('Link Settings'), {
            'fields': ('link', 'link_text'),
            'classes': ('collapse',),
        }),
        (_('Display Period'), {
            'fields': ('start_date', 'end_date'),
            'description': _('Leave empty to show always (when active)')
        }),
        (_('Appearance'), {
            'fields': ('show_border', 'border_style', 'background_color'),
            'classes': ('collapse',),
        }),
    )
    
    @admin.display(description=_("Currently Visible"), boolean=True)
    def is_currently_visible(self, obj):
        return obj.is_visible()
    
    @admin.display(description=_("Display Period"))
    def date_range(self, obj):
        start = obj.start_date.strftime('%d.%m.%Y') if obj.start_date else '∞'
        end = obj.end_date.strftime('%d.%m.%Y') if obj.end_date else '∞'
        return f"{start} — {end}"
    
    @admin.display(description=_("Preview"))
    def preview_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 60px; object-fit: contain; border-radius: 4px;" />',
                obj.image.url
            )
        elif obj.content_type == 'video':
            return format_html('<span style="color: #666;">🎬 Video</span>')
        elif obj.content_type == 'lottie':
            return format_html('<span style="color: #666;">✨ Lottie</span>')
        elif obj.content_type == 'text_only':
            return format_html('<span style="color: #666;">📝 Text</span>')
        return '-'