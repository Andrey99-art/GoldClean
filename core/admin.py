# File: core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from solo.admin import SingletonModelAdmin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline # Используем специальные классы
from modeltranslation.translator import translator
from django.conf import settings
from deep_translator import GoogleTranslator

from .models import CleaningArea, FeaturePoint, SiteConfiguration

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