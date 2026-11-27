# File: core/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from solo.admin import SingletonModelAdmin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from modeltranslation.translator import translator
from django.conf import settings
from deep_translator import GoogleTranslator

from .models import CleaningArea, FeaturePoint, SiteConfiguration, PromoBanner, Lead

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
    fieldsets = (
        ('🏢 Основные настройки', {
            'fields': ('cancellation_fee', 'services_page_enabled', 'is_new_year_theme')
        }),
        ('💰 Скидки', {
            'fields': (
                'new_client_discount_enabled',
                'new_client_discount_percent',
                'subscription_discount_enabled',
                'discount_weekly',
                'discount_bi_weekly',
                'discount_monthly',
                'max_combined_discount',
            ),
            'description': 'Управление системой скидок. Все значения в процентах.',
        }),
        ('🔗 Социальные сети', {
            'fields': ('telegram_link', 'whatsapp_link', 'instagram_link'),
            'classes': ('collapse',)
        }),
    )

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



@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'phone',
        'email',
        'service_name',
        'status_colored',
        'processing_status',
        'order_status',
        'source',
        'platform',
        'lead_received_at',
        'convert_btn',
    ]
    list_filter = ['status', 'processing_status', 'order_status', 'source', 'platform', 'created_at']
    search_fields = ['name', 'phone', 'email', 'message', 'service_name', 'campaign']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent', 'sheets_row_id']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('👤 Контактная информация', {
            'fields': ('name', 'phone', 'email', 'message')
        }),
        ('🧹 Услуга', {
            'fields': ('service_name', 'order_amount')
        }),
        ('📊 Статус', {
            'fields': ('status', 'processing_status', 'order_status', 'processing_time', 'admin_notes', 'converted_user')
        }),
        ('📢 Рекламная информация', {
            'fields': ('source', 'platform', 'audience', 'campaign', 'ad_group', 'lead_received_at'),
        }),
        ('🔍 Мета-данные', {
            'fields': ('created_at', 'updated_at', 'ip_address', 'user_agent', 'sheets_row_id'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['export_to_excel', 'mark_contacted', 'mark_converted', 'mark_cancelled']
    
    @admin.display(description='Статус')
    def status_colored(self, obj):
        colors = {
            'new': ('#28a745', '🆕'),
            'contacted': ('#ffc107', '📞'), 
            'converted': ('#17a2b8', '✅'),
            'cancelled': ('#dc3545', '✗'),
        }
        color, icon = colors.get(obj.status, ('#6c757d', '?'))
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    
    @admin.display(description='Источник')
    def source_display(self, obj):
        return format_html(
            '<span style="color: #666; font-size: 11px;">Pop-up форма</span>'
        )
    
    # === ЭКСПОРТ В EXCEL ===
    @admin.action(description='📥 Экспорт в Excel')
    def export_to_excel(self, request, queryset):
        import openpyxl
        from django.http import HttpResponse
        from openpyxl.styles import Font, Fill, PatternFill, Alignment
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Лиды'
        
        # Заголовки
        headers = ['ID', 'Имя', 'Телефон', 'Email', 'Сообщение', 'Статус', 'Дата создания']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='B89E40', end_color='B89E40', fill_type='solid')
            cell.alignment = Alignment(horizontal='center')
        
        # Данные
        for row, lead in enumerate(queryset, 2):
            ws.cell(row=row, column=1, value=lead.id)
            ws.cell(row=row, column=2, value=lead.name)
            ws.cell(row=row, column=3, value=lead.phone)
            ws.cell(row=row, column=4, value=lead.email)
            ws.cell(row=row, column=5, value=lead.message or '')
            ws.cell(row=row, column=6, value=lead.get_status_display())
            ws.cell(row=row, column=7, value=lead.created_at.strftime('%d.%m.%Y %H:%M'))
        
        # Автоширина колонок
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column].width = min(max_length + 2, 50)
        
        # Ответ
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="leads_export.xlsx"'
        wb.save(response)
        
        return response
    
    # === БЫСТРЫЕ ДЕЙСТВИЯ ===
    @admin.action(description='📞 Отметить как "Связались"')
    def mark_contacted(self, request, queryset):
        updated = queryset.update(status='contacted')
        self.message_user(request, f'Обновлено лидов: {updated}')
    
    @admin.action(description='✅ Отметить как "Конвертирован"')
    def mark_converted(self, request, queryset):
        updated = queryset.update(status='converted')
        self.message_user(request, f'Конвертировано лидов: {updated}')
    
    @admin.action(description='✗ Отметить как "Отменён"')
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'Отменено лидов: {updated}')

    @admin.display(description='Действие')
    def convert_btn(self, obj):
        if obj.status == 'converted':
            return format_html('<span style="color:#28a745;">\u2713 Конвертирован</span>')
        return format_html(
            '<a href="/admin/orders/order/add/?customer_name={}&customer_phone={}&customer_email={}" '
            'style="background:#B89E40;color:white;padding:4px 12px;border-radius:4px;'
            'text-decoration:none;font-size:12px;white-space:nowrap;">+ Заказ</a>',
            obj.name or '', obj.phone or '', obj.email or ''
        )
