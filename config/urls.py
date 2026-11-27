# ПУТЬ: config/urls.py
from django.contrib import admin
from django.urls import path, include 
from orders.views import stripe_webhook
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap 
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

sitemaps = {
    'static': StaticViewSitemap,
}

# === КАСТОМИЗАЦИЯ АДМИНКИ ===
admin.site.site_header = '🧹 Gold Clean - Админ панель'
admin.site.site_title = 'Gold Clean CRM'
admin.site.index_title = 'Управление бизнесом'

# Сохраняем оригинальный метод index
_original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    """Кастомный дашборд со статистикой"""
    extra_context = extra_context or {}
    
    try:
        from orders.models import Order
        from core.models import Lead
        from accounts.models import Profile
        from django.contrib.auth.models import User
        
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Статистика заказов
        orders_today = Order.objects.filter(cleaning_date=today).count()
        orders_tomorrow = Order.objects.filter(cleaning_date=tomorrow).count()
        orders_week = Order.objects.filter(cleaning_date__gte=week_start).count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        # Выручка за месяц
        revenue_month = Order.objects.filter(
            created_at__gte=month_start,
            status__in=['completed', 'confirmed']
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Лиды
        new_leads = Lead.objects.filter(status='new').count()
        
        # Клиенты
        total_clients = User.objects.filter(is_staff=False).count()
        new_clients = Profile.objects.filter(created_at__gte=month_start).count()
        
        extra_context['stats'] = {
            'orders_today': orders_today,
            'orders_tomorrow': orders_tomorrow,
            'orders_week': orders_week,
            'pending_orders': pending_orders,
            'revenue_month': f"{revenue_month:.0f}",
            'new_leads': new_leads,
            'total_clients': total_clients,
            'new_clients': new_clients,
        }
        # Уборки на ближайшие 7 дней
        from collections import OrderedDict
        week_ahead = today + timedelta(days=7)
        upcoming_orders = Order.objects.filter(
            cleaning_date__gte=today,
            cleaning_date__lte=week_ahead
        ).select_related('service').order_by('cleaning_date', 'cleaning_time')
        days_orders = OrderedDict()
        for d in range(8):
            day = today + timedelta(days=d)
            days_orders[day] = []
        for order in upcoming_orders:
            if order.cleaning_date in days_orders:
                days_orders[order.cleaning_date].append(order)
        extra_context['upcoming_days'] = [
            {'date': day, 'orders': orders, 'is_today': day == today}
            for day, orders in days_orders.items()
        ]
        
        extra_context['today'] = today.isoformat()
        extra_context['tomorrow'] = tomorrow.isoformat()
        extra_context['week_start'] = week_start.isoformat()
        extra_context['week_end'] = (week_start + timedelta(days=6)).isoformat()
        extra_context['current_month'] = today.month
        extra_context['current_year'] = today.year
    except Exception as e:
        # Если что-то пошло не так, показываем нули
        extra_context['stats'] = {
            'orders_today': 0,
            'orders_tomorrow': 0,
            'orders_week': 0,
            'pending_orders': 0,
            'revenue_month': '0',
            'new_leads': 0,
            'total_clients': 0,
            'new_clients': 0,
        }
        extra_context['today'] = timezone.now().date().isoformat()
        extra_context['tomorrow'] = (timezone.now().date() + timedelta(days=1)).isoformat()
        extra_context['week_start'] = timezone.now().date().isoformat()
        extra_context['week_end'] = timezone.now().date().isoformat()
        extra_context['current_month'] = timezone.now().date().month
        extra_context['current_year'] = timezone.now().date().year
    
    return _original_index(request, extra_context=extra_context)

# Подменяем метод
admin.site.index = custom_admin_index


from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse

@staff_member_required
def calendar_view(request):
    return TemplateResponse(request, 'admin/calendar.html', {
        'title': 'Календарь уборок',
        'site_header': admin.site.site_header,
    })

@staff_member_required
def calendar_api(request):
    from orders.models import Order
    start = request.GET.get('start', '')
    end = request.GET.get('end', '')
    
    orders = Order.objects.all()
    if start:
        orders = orders.filter(cleaning_date__gte=start[:10])
    if end:
        orders = orders.filter(cleaning_date__lte=end[:10])
    
    events = []
    for o in orders:
        status_colors = {
            'new': '#ffc107', 'pending': '#ffc107',
            'in_progress': '#007bff', 'confirmed': '#007bff',
            'completed': '#28a745', 'canceled': '#dc3545',
        }
        color = status_colors.get(o.status, '#6c757d')
        time_str = o.cleaning_time.strftime('%H:%M') if o.cleaning_time else '00:00'
        events.append({
            'id': o.pk,
            'title': '{} - {}'.format(time_str, o.customer_name),
            'start': '{}T{}'.format(o.cleaning_date.isoformat(), time_str),
            'url': '/admin/orders/order/{}/change/'.format(o.pk),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'service': str(o.service or '-'),
                'price': '{:.0f} zl'.format(float(o.total_price or 0)),
                'status': o.get_status_display(),
                'phone': o.customer_phone or '',
            }
        })
    
    return JsonResponse(events, safe=False)

urlpatterns = [
    path('admin/calendar/', calendar_view, name='admin_calendar'),
    path('admin/calendar/api/', calendar_api, name='calendar_api'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('i18n/', include('django.conf.urls.i18n')),
    # Stripe Webhook (без языкового префикса для Stripe)
    path('order/webhook/', stripe_webhook, name='stripe_webhook_direct'),
]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('order/', include('orders.urls', namespace='orders')),
    path('reviews/', include('reviews.urls')),
    path('accounts/', include('accounts.urls')),
    prefix_default_language=True,
)

# --- БЛОК DEBUG ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
