# File: config/admin_site.py
from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count


class GoldCleanAdminSite(admin.AdminSite):
    site_header = '🧹 Gold Clean - Админ панель'
    site_title = 'Gold Clean CRM'
    index_title = 'Управление бизнесом'
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Импортируем модели здесь чтобы избежать circular import
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
        
        # Выручка за месяц (только выполненные/подтверждённые)
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
        week_ahead = today + timedelta(days=7)
        upcoming_orders = Order.objects.filter(
            cleaning_date__gte=today,
            cleaning_date__lte=week_ahead
        ).select_related('service').order_by('cleaning_date', 'cleaning_time')
        
        # Группируем по дням
        from collections import OrderedDict
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
        
        return super().index(request, extra_context=extra_context)


# Создаём экземпляр
gold_clean_admin = GoldCleanAdminSite(name='gold_clean_admin')
