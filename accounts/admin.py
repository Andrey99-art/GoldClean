
# File: accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import Profile


class ProfileInline(admin.StackedInline):
    """Инлайн профиля в карточке пользователя"""
    model = Profile
    can_delete = False
    verbose_name = 'Профиль клиента'
    verbose_name_plural = 'Профиль клиента'
    
    fields = (
        'is_new_client', 
        'penalty_balance', 
        'first_order_discount_used_at',
        'source_lead',
        'created_at'
    )
    readonly_fields = ('first_order_discount_used_at', 'created_at')


class UserAdmin(BaseUserAdmin):
    """Расширенная админка пользователей"""
    inlines = (ProfileInline,)
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name',
        'client_status',
        'orders_count',
        'total_spent',
        'is_active',
        'date_joined'
    )
    list_filter = (
        'is_active', 
        'is_staff', 
        'date_joined',
        'profile__is_new_client'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _orders_count=Count('orders'),
            _total_spent=Sum('orders__total_price')
        )
        return qs
    
    @admin.display(description='Статус')
    def client_status(self, obj):
        if hasattr(obj, 'profile'):
            if obj.profile.is_new_client:
                return format_html(
                    '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">🆕 Новый</span>'
                )
            else:
                return format_html(
                    '<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">Постоянный</span>'
                )
        return '-'
    
    @admin.display(description='Заказов', ordering='_orders_count')
    def orders_count(self, obj):
        count = getattr(obj, '_orders_count', 0)
        if count > 0:
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
                count
            )
        return '0'
    
    @admin.display(description='Потрачено (zł)', ordering='_total_spent')
    def total_spent(self, obj):
        total = getattr(obj, '_total_spent', 0) or 0
        if total > 0:
            return format_html(
                '<strong style="color: #28a745;">{:.2f} zł</strong>',
                float(total)
            )
        return '0 zł'


# Перерегистрируем User с новой админкой
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """CRM: Полноценный список клиентов"""
    list_display = (
        'client_name',
        'phone',
        'user_email',
        'client_status',
        'orders_count',
        'total_spent',
        'last_order_date',
        'penalty_status',
        'create_order_btn',
    )
    list_filter = ('is_new_client', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'first_order_discount_used_at', 'orders_count_detail', 'total_spent_detail', 'orders_history')
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ('\U0001f464 Клиент', {
            'fields': ('user', 'phone')
        }),
        ('\U0001f4ca Статистика', {
            'fields': ('orders_count_detail', 'total_spent_detail'),
        }),
        ('\U0001f4cb История заказов', {
            'fields': ('orders_history',),
        }),
        ('\U0001f3af Статус клиента', {
            'fields': ('is_new_client', 'first_order_discount_used_at')
        }),
        ('\U0001f4b0 Штрафы', {
            'fields': ('penalty_balance',)
        }),
        ('\U0001f517 Источник', {
            'fields': ('source_lead',),
            'classes': ('collapse',)
        }),
        ('\U0001f4c5 Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('user').annotate(
            _orders_count=Count('user__order'),
            _total_spent=Sum('user__order__total_price')
        )
        return qs

    @admin.display(description='Клиент')
    def client_name(self, obj):
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<strong>{}</strong>', name)

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email or '-'

    @admin.display(description='Статус')
    def client_status(self, obj):
        if obj.is_new_client:
            return format_html(
                '<span style="background:#28a745;color:white;padding:3px 8px;border-radius:3px;">\U0001f195 Новый</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:3px 8px;border-radius:3px;">Постоянный</span>'
        )

    @admin.display(description='Заказов', ordering='_orders_count')
    def orders_count(self, obj):
        count = getattr(obj, '_orders_count', 0) or 0
        if count > 0:
            return format_html(
                '<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:10px;">{}</span>',
                count
            )
        return '0'

    @admin.display(description='Потрачено')
    def total_spent(self, obj):
        total = getattr(obj, '_total_spent', 0) or 0
        if total > 0:
            return format_html('<strong style="color:#28a745;">{:.0f} zl</strong>', float(total))
        return '0 zl'

    @admin.display(description='Последний заказ')
    def last_order_date(self, obj):
        if obj.user:
            last = obj.user.order_set.order_by('-cleaning_date').first()
            if last and last.cleaning_date:
                return last.cleaning_date.strftime('%d.%m.%Y')
        return '-'

    @admin.display(description='Штраф')
    def penalty_status(self, obj):
        if obj.penalty_balance > 0:
            return format_html(
                '<span style="background:#dc3545;color:white;padding:3px 8px;border-radius:3px;">{:.0f} zl</span>',
                float(obj.penalty_balance)
            )
        return format_html('<span style="color:#28a745;">\u2713</span>')

    @admin.display(description='Действие')
    def create_order_btn(self, obj):
        return format_html(
            '<a href="/admin/orders/order/add/?user={}" style="background:#B89E40;color:white;padding:4px 12px;border-radius:4px;text-decoration:none;font-size:12px;white-space:nowrap;">+ Заказ</a>',
            obj.user.pk
        )

    @admin.display(description='Количество заказов')
    def orders_count_detail(self, obj):
        return obj.user.order_set.count() if obj.user else 0

    @admin.display(description='Сумма заказов')
    def total_spent_detail(self, obj):
        total = obj.user.order_set.aggregate(t=Sum('total_price'))['t'] or 0
        return '{:.0f} zl'.format(float(total))

    @admin.display(description='История заказов')
    def orders_history(self, obj):
        if not obj.user:
            return '-'
        orders = obj.user.order_set.all().order_by('-cleaning_date')
        if not orders.exists():
            return format_html('<em>Заказов пока нет</em>')
        rows = ''
        for o in orders:
            sc = {'new':'#ffc107','pending':'#ffc107','in_progress':'#007bff','confirmed':'#007bff','completed':'#28a745','canceled':'#dc3545'}
            color = sc.get(o.status, '#6c757d')
            dt = o.cleaning_date.strftime('%d.%m.%Y') if o.cleaning_date else '-'
            tm = str(o.cleaning_time or '-')
            svc = str(o.service or '-')
            rows += '<tr>'
            rows += '<td style="padding:5px;"><a href="/admin/orders/order/{}/change/">#{}</a></td>'.format(o.pk, o.pk)
            rows += '<td style="padding:5px;">{}</td>'.format(svc)
            rows += '<td style="padding:5px;">{}</td>'.format(dt)
            rows += '<td style="padding:5px;">{}</td>'.format(tm)
            rows += '<td style="padding:5px;"><span style="background:{};color:white;padding:2px 8px;border-radius:3px;">{}</span></td>'.format(color, o.get_status_display())
            rows += '<td style="padding:5px;"><strong>{:.0f} zl</strong></td>'.format(float(o.total_price or 0))
            rows += '</tr>'
        html = '<table style="width:100%;border-collapse:collapse;">'
        html += '<thead><tr style="background:#f0f0f0;">'
        html += '<th style="padding:6px;text-align:left;">ID</th>'
        html += '<th style="padding:6px;text-align:left;">Услуга</th>'
        html += '<th style="padding:6px;text-align:left;">Дата</th>'
        html += '<th style="padding:6px;text-align:left;">Время</th>'
        html += '<th style="padding:6px;text-align:left;">Статус</th>'
        html += '<th style="padding:6px;text-align:left;">Сумма</th>'
        html += '</tr></thead><tbody>' + rows + '</tbody></table>'
        return format_html(html)
