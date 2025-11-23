from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Order

def send_cleaning_reminders():
    print("--- Running cleaning reminder job ---")
    
    # Даты, которые нас интересуют
    today = date.today()
    three_days_from_now = today + timedelta(days=3)

    # Ищем заказы, которые нужно напомнить за 3 дня
    orders_for_3_day_reminder = Order.objects.filter(
        cleaning_date=three_days_from_now,
        status__in=['new', 'in_progress']
    )
    
    for order in orders_for_3_day_reminder:
        user = order.user
        if user and user.email:
            context = {
                'user_name': user.get_full_name() or user.username,
                'service_name': order.service.name,
                'cleaning_date': order.cleaning_date.strftime('%d.%m.%Y'),
                'cleaning_time': order.cleaning_time.strftime('%H:%M'),
                'address': f"{order.city}, {order.street} {order.building_number}"
            }
            message = render_to_string('emails/three_day_reminder.txt', context)
            send_mail(
                'Напоминание об уборке через 3 дня',
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            print(f"Sent 3-day reminder for order #{order.id} to {user.email}")

    # Ищем заказы, которые нужно напомнить сегодня
    orders_for_same_day_reminder = Order.objects.filter(
        cleaning_date=today,
        status__in=['new', 'in_progress']
    )

    for order in orders_for_same_day_reminder:
        user = order.user
        if user and user.email:
            context = {
                'user_name': user.get_full_name() or user.username,
                'service_name': order.service.name,
                'cleaning_time': order.cleaning_time.strftime('%H:%M'),
                'address': f"{order.city}, {order.street} {order.building_number}"
            }
            message = render_to_string('emails/same_day_reminder.txt', context)
            send_mail(
                'Напоминание: уборка сегодня!',
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            print(f"Sent same-day reminder for order #{order.id} to {user.email}")
            
    print("--- Reminder job finished ---")