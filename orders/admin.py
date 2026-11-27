# File: orders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import Order, City, Cleaner
from core.utils import format_duration


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'delivery_charge_display')
    search_fields = ('name',)
    ordering = ('name',)

    @admin.display(description='Доставка')
    def delivery_charge_display(self, obj):
        return f"{obj.delivery_charge} zł"


@admin.register(Cleaner)
class CleanerAdmin(admin.ModelAdmin):
    list_display = ('photo_thumbnail', 'name', 'phone', 'status_colored', 'orders_today', 'orders_week', 'total_orders')
    list_filter = ('status',)
    search_fields = ('name', 'phone', 'email')
    ordering = ('name',)
    list_per_page = 25

    readonly_fields = ('created_at', 'orders_history', 'photo_preview')

    fieldsets = (
        ('\U0001f464 Сотрудник', {
            'fields': ('name', 'phone', 'email', 'photo', 'photo_preview', 'status')
        }),
        ('\U0001f4cb Заказы', {
            'fields': ('orders_history',),
        }),
        ('\U0001f4dd Заметки', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('\U0001f4c5 Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Фото')
    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" />', obj.photo.url)
        return format_html('<span style="display:inline-block;width:40px;height:40px;border-radius:50%;background:#e0e0e0;text-align:center;line-height:40px;font-size:18px;">\U0001f464</span>')

    @admin.display(description='Фото')
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-width:200px;max-height:200px;border-radius:10px;" />', obj.photo.url)
        return format_html('<em>Фото не загружено</em>')

    @admin.display(description='Статус')
    def status_colored(self, obj):
        colors = {'active': '#28a745', 'on_leave': '#ffc107', 'inactive': '#dc3545'}
        icons = {'active': '\u2713', 'on_leave': '\u23f8', 'inactive': '\u2717'}
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '?')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;">{} {}</span>',
            color, icon, obj.get_status_display()
        )

    @admin.display(description='Сегодня')
    def orders_today(self, obj):
        count = obj.orders.filter(cleaning_date=timezone.now().date()).count()
        if count > 0:
            return format_html('<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:10px;">{}</span>', count)
        return '0'

    @admin.display(description='На неделе')
    def orders_week(self, obj):
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        count = obj.orders.filter(cleaning_date__gte=today, cleaning_date__lte=week_end).count()
        if count > 0:
            return format_html('<span style="background:#007bff;color:white;padding:2px 8px;border-radius:10px;">{}</span>', count)
        return '0'

    @admin.display(description='Всего')
    def total_orders(self, obj):
        return obj.orders.count()

    @admin.display(description='История заказов')
    def orders_history(self, obj):
        orders = obj.orders.all().order_by('-cleaning_date')[:20]
        if not orders:
            return format_html('<em>Заказов пока нет</em>')
        rows = ''
        for o in orders:
            sc = {'new':'#ffc107','pending':'#ffc107','in_progress':'#007bff','confirmed':'#007bff','completed':'#28a745','canceled':'#dc3545'}
            color = sc.get(o.status, '#6c757d')
            dt = o.cleaning_date.strftime('%d.%m.%Y') if o.cleaning_date else '-'
            rows += '<tr>'
            rows += '<td style="padding:5px;"><a href="/admin/orders/order/{}/change/">#{}</a></td>'.format(o.pk, o.pk)
            rows += '<td style="padding:5px;">{}</td>'.format(o.customer_name)
            rows += '<td style="padding:5px;">{}</td>'.format(dt)
            rows += '<td style="padding:5px;"><span style="background:{};color:white;padding:2px 8px;border-radius:3px;">{}</span></td>'.format(color, o.get_status_display())
            rows += '<td style="padding:5px;"><strong>{:.0f} zl</strong></td>'.format(float(o.total_price or 0))
            rows += '</tr>'
        html = '<table style="width:100%;border-collapse:collapse;">'
        html += '<thead><tr style="background:#f0f0f0;">'
        html += '<th style="padding:6px;text-align:left;">ID</th>'
        html += '<th style="padding:6px;text-align:left;">Клиент</th>'
        html += '<th style="padding:6px;text-align:left;">Дата</th>'
        html += '<th style="padding:6px;text-align:left;">Статус</th>'
        html += '<th style="padding:6px;text-align:left;">Сумма</th>'
        html += '</tr></thead><tbody>' + rows + '</tbody></table>'
        return format_html(html)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'status_colored',
        'customer_info',
        'service',
        'cleaner',
        'city',
        'cleaning_datetime',
        'price_display',
        'payment_info',
        'created_short',
    )
    list_filter = (
        'status',
        'payment_status',
        'payment_method',
        'city',
        'cleaning_date',
        'frequency',
        'is_private_house',
        'cleaner',
    )
    search_fields = (
        'id',
        'customer_name',
        'customer_phone',
        'customer_email',
        'street'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'cleaning_date'
    list_per_page = 25

    readonly_fields = (
        'created_at',
        'updated_at',
        'total_price',
        'delivery_charge',
        'payment_status',
        'stripe_session_id',
        'get_additional_services_display'
    )

    fieldsets = (
        ('\U0001f4cb Основная информация', {
            'fields': ('service', 'cleaner', 'total_price', 'delivery_charge')
        }),
        ('\U0001f4ca Статус и Оплата', {
            'fields': ('status', 'payment_method', 'payment_status', 'stripe_session_id')
        }),
        ('\U0001f9f9 Детали уборки', {
            'fields': (
                'frequency',
                'rooms_count',
                'bathrooms_count',
                'sqm',
                'window_count',
                'get_additional_services_display',
                'is_private_house',
                'bring_vacuum_cleaner'
            )
        }),
        ('\U0001f464 Клиент', {
            'fields': ('customer_name', 'customer_phone', 'customer_email', 'user')
        }),
        ('\U0001f4cd Адрес', {
            'fields': (
                'city',
                'street',
                'building_number',
                'apartment_number',
                'entrance',
                'floor',
                'postal_code',
                'intercom_code'
            ),
            'classes': ('collapse',)
        }),
        ('\U0001f4c5 Дата и Время', {
            'fields': (
                'cleaning_date',
                'cleaning_time',
                'estimated_duration_minutes',
                'created_at',
                'updated_at'
            )
        }),
        ('\U0001f4ac Комментарии', {
            'fields': ('comments',),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if 'customer_name' in request.GET:
            initial['customer_name'] = request.GET['customer_name']
        if 'customer_phone' in request.GET:
            initial['customer_phone'] = request.GET['customer_phone']
        if 'customer_email' in request.GET:
            initial['customer_email'] = request.GET['customer_email']
        return initial

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            first_fields = list(fieldsets[0][1]['fields'])
            if 'id' not in first_fields:
                first_fields.insert(0, 'id')
                fieldsets[0][1]['fields'] = tuple(first_fields)
        return fieldsets

    @admin.display(description='Статус')
    def status_colored(self, obj):
        colors = {
            'new': ('#ffc107', '\U0001f195'),
            'in_progress': ('#007bff', '\U0001f504'),
            'completed': ('#28a745', '\u2705'),
            'canceled': ('#dc3545', '\u2717'),
        }
        color, icon = colors.get(obj.status, ('#6c757d', '?'))
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:4px; font-weight:500;">{} {}</span>',
            color, icon, obj.get_status_display()
        )

    @admin.display(description='Клиент')
    def customer_info(self, obj):
        name = obj.customer_name or 'Без имени'
        phone = obj.customer_phone or ''
        return format_html(
            '<strong>{}</strong><br><span style="color:#666;font-size:11px;">{}</span>',
            name, phone
        )

    @admin.display(description='Дата уборки')
    def cleaning_datetime(self, obj):
        if obj.cleaning_date:
            date_str = obj.cleaning_date.strftime('%d.%m.%Y')
            time_str = obj.cleaning_time.strftime('%H:%M') if obj.cleaning_time else ''
            today = timezone.now().date()
            if obj.cleaning_date == today:
                return format_html(
                    '<span style="background:#28a745;color:white;padding:2px 6px;border-radius:3px;">Сегодня</span> {}',
                    time_str
                )
            elif obj.cleaning_date == today + timedelta(days=1):
                return format_html(
                    '<span style="background:#ffc107;color:black;padding:2px 6px;border-radius:3px;">Завтра</span> {}',
                    time_str
                )
            return "{} {}".format(date_str, time_str)
        return '-'

    @admin.display(description='Сумма')
    def price_display(self, obj):
        price = float(obj.total_price) if obj.total_price else 0.0
        return format_html(
            '<strong style="color:#28a745;">{} zl</strong>',
            "{:.2f}".format(price)
        )

    @admin.display(description='Оплата')
    def payment_info(self, obj):
        payment_colors = {
            'pending': ('#ffc107', '\u23f3'),
            'paid': ('#28a745', '\u2713'),
            'failed': ('#dc3545', '\u2717'),
        }
        color, icon = payment_colors.get(obj.payment_status, ('#6c757d', '?'))
        method_icons = {'cash': '\U0001f4b5', 'card': '\U0001f4b3'}
        method_icon = method_icons.get(obj.payment_method, '')
        return format_html(
            '<span style="color:{};">{}</span> {}',
            color, icon, method_icon
        )

    @admin.display(description='Создан')
    def created_short(self, obj):
        return obj.created_at.strftime('%d.%m %H:%M')

    @admin.display(description='Длительность')
    def formatted_duration(self, obj):
        if obj.estimated_duration_minutes:
            return format_duration(obj.estimated_duration_minutes)
        return "N/A"

    actions = ['mark_in_progress', 'mark_completed', 'mark_canceled']

    @admin.action(description='\U0001f504 В работу')
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'Обновлено заказов: {updated}')

    @admin.action(description='\u2705 Отметить как выполненные')
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'Выполнено заказов: {updated}')

    @admin.action(description='\u2717 Отменить')
    def mark_canceled(self, request, queryset):
        updated = queryset.update(status='canceled')
        self.message_user(request, f'Отменено заказов: {updated}')
