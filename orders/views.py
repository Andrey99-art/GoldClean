# ПУТЬ: orders/views.py
# КОНТЕКСТ: Исправление логики сохранения услуг (Snapshot Pattern) для прохождения тестов

import logging
import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.http import HttpResponse
from accounts.models import Profile
from core.utils import format_duration, send_gmail_message
from products.models import Service, AdditionalService
from .forms import OrderCreateForm
from .models import Order, City

# --- НАСТРОЙКА STRIPE ---
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

def _send_order_confirmation_email(order):
    """Отправляет подтверждение клиенту и уведомление администратору."""
    try:
        if order.customer_email:
            subject_client = f"Ваш заказ №{order.id} на сайте Gold Clean принят"
            full_address = f"{order.street} {order.building_number}"
            if order.apartment_number: full_address += f", кв. {order.apartment_number}"
            full_address += f", {order.postal_code}, {order.city.name}"
            message_body_client = (
                f"Здравствуйте, {order.customer_name}!\n\n"
                f"Спасибо за ваш заказ! Мы получили вашу заявку №{order.id} и скоро свяжемся с вами для подтверждения всех деталей.\n"
                f"\n**Детали вашего заказа:**\n"
                f"  Услуга: {order.service.name}\n"
                f"  Итоговая стоимость: {order.total_price} zł\n"
                f"  Желаемая дата и время: {order.cleaning_date.strftime('%d.%m.%Y')} в {order.cleaning_time.strftime('%H:%M')}\n"
                f"  Адрес: {full_address}\n"
            )
            if order.additional_services_details:
                service_names = [service['name'] for service in order.additional_services_details]
                message_body_client += f"  Дополнительные услуги: {', '.join(service_names)}\n"
            message_body_client += f"\nС уважением,\nКоманда Gold Clean\n"
            send_gmail_message(subject_client, message_body_client, [order.customer_email])
        else:
            logger.warning(f"Не удалось отправить письмо клиенту для заказа {order.id}: email не указан.")

        admin_email = getattr(settings, 'ADMIN_EMAIL', 'goldclean2026@gmail.com')
        subject_admin = f"Новый заказ №{order.id} на сайте Gold Clean!"
        full_address_admin = f"{order.street} {order.building_number}"
        if order.apartment_number: full_address_admin += f", кв. {order.apartment_number}"
        full_address_admin += f", {order.postal_code}, {order.city.name}"
        if order.entrance: full_address_admin += f", подъезд {order.entrance}"
        if order.floor: full_address_admin += f", этаж {order.floor}"
        if order.intercom_code: full_address_admin += f", домофон {order.intercom_code}"
        message_body_admin = (
            f"Поступил новый заказ №{order.id}.\n\n"
            f"**Данные клиента:**\n"
            f"  Имя: {order.customer_name}\n"
            f"  Email: {order.customer_email}\n"
            f"  Телефон: {order.customer_phone}\n"
            f"\n**Детали заказа:**\n"
            f"  Услуга: {order.service.name}\n"
            f"  Итоговая стоимость: {order.total_price} zł\n"
            f"  Желаемая дата и время: {order.cleaning_date.strftime('%d.%m.%Y')} в {order.cleaning_time.strftime('%H:%M')}\n"
            f"  Адрес: {full_address_admin}\n"
            f"  Комментарии: {order.comments or 'Нет'}\n"
        )
        if order.estimated_duration_minutes:
            message_body_admin += f"  Примерная длительность: {format_duration(order.estimated_duration_minutes)}\n"
        if order.additional_services_details:
            service_names = [service['name'] for service in order.additional_services_details]
            message_body_admin += f"  Дополнительные услуги: {', '.join(service_names)}\n"
        message_body_admin += f"\nПожалуйста, свяжитесь с клиентом для подтверждения заказа.\n"
        send_gmail_message(subject_admin, message_body_admin, [admin_email])
    except Exception as e:
        logger.error(f"Произошла ошибка при отправке email для заказа {order.id}: {e}", exc_info=True)


def _process_order_details_from_summary(order, summary):
    if summary.get('is_window_service'):
        order.window_count = summary.get('window_count', 0)
    else:
        order.rooms_count = summary.get('rooms_count', 0)
        order.bathrooms_count = summary.get('bathrooms_count', 0)
        order.sqm = summary.get('sqm', 0)
        order.frequency = summary.get('frequency', 'one_time')
        order.bring_vacuum_cleaner = summary.get('bring_vacuum', False)
        order.is_private_house = summary.get('is_private_house', False)
        order.estimated_duration_minutes = summary.get('estimated_duration_minutes', 0)


def order_create(request):
    summary = request.session.get('order_summary')
    if not summary:
        messages.error(request, _("Your session has expired. Please calculate the cost again."))
        return redirect('index')
    try:
        summary_total_price = Decimal(str(summary.get('total_price', '0.00')))
        summary_service_id = summary.get('service_id')
        if not isinstance(summary_service_id, int): raise ValueError("Invalid service ID in session summary.")
    except Exception:
        messages.error(request, _("Invalid order summary data. Please calculate the cost again."))
        if 'order_summary' in request.session: del request.session['order_summary']
        return redirect('index')
    cities = City.objects.order_by('delivery_charge', 'name')
    user_profile = None
    if request.user.is_authenticated:
        user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            selected_city = form.cleaned_data['city']
            delivery_charge = selected_city.delivery_charge
            base_price = summary_total_price 
            final_price = base_price + delivery_charge
            if request.user.is_authenticated and user_profile and user_profile.penalty_balance > 0:
                penalty_balance_applied = user_profile.penalty_balance
                final_price += penalty_balance_applied
                penalty_note = _("\n[System Note] Added outstanding penalty of {fee} zł.").format(fee=penalty_balance_applied)
                order.comments = (form.cleaned_data.get('comments') or "") + penalty_note
                user_profile.penalty_balance = Decimal('0.00')
                user_profile.save()
            
            order.service = get_object_or_404(Service, id=summary_service_id)
            order.total_price = final_price
            order.delivery_charge = delivery_charge
            _process_order_details_from_summary(order, summary)
            order.save()
            
            # --- ИЗМЕНЕНИЕ: ЛОГИКА SNAPSHOT ---
            # Берем готовый список услуг из сессии.
            details = summary.get('additional_services_details')
            if details and not summary.get('is_window_service'):
                order.additional_services_details = details
                order.save()
            # ----------------------------------

            if 'order_summary' in request.session:
                del request.session['order_summary']
            
            # Отправляем письмо только если оплата наличными
            if order.payment_method == 'cash':
                _send_order_confirmation_email(order)

            if order.payment_method == 'card':
                return redirect(reverse('orders:create_checkout_session', kwargs={'order_id': order.id}))
            else:
                return redirect('orders:order_success')
    else: 
        initial_data = {}
        if request.user.is_authenticated and user_profile:
            initial_data = {'customer_name': request.user.get_full_name() or request.user.username, 'customer_email': request.user.email}
        form = OrderCreateForm(initial=initial_data)
    penalty_balance = user_profile.penalty_balance if user_profile else Decimal('0.00')
    context = {'form': form, 'summary': summary, 'cities': cities, 'penalty_balance': penalty_balance}
    return render(request, 'orders/create_order.html', context)

def order_success(request):
    return render(request, 'orders/order_success.html')

def start_kitchen_order(request):
    if request.method == 'POST':
        try:
            KITCHEN_SERVICE_SLUG = 'kitchen-cleaning'
            kitchen_service = Service.objects.get(slug=KITCHEN_SERVICE_SLUG)
            total_price = kitchen_service.base_price
            additional_services_ids_str = request.POST.get('additional_services_ids', '')
            additional_services_ids = [int(sid) for sid in additional_services_ids_str.split(',')] if additional_services_ids_str else []
            
            # --- ИЗМЕНЕНИЕ: Формируем details ---
            additional_services_details = []
            if additional_services_ids:
                add_services_objs = AdditionalService.objects.filter(id__in=additional_services_ids)
                for svc in add_services_objs:
                    total_price += svc.price
                    additional_services_details.append({
                        'name': svc.name,
                        'price': float(svc.price),
                        'quantity': 1
                    })
            # ------------------------------------

            summary = {
                'service_id': kitchen_service.id, 'service_name': str(kitchen_service.name),
                'is_window_service': False, 'rooms_count': 0, 'bathrooms_count': 0, 'sqm': 0,
                'additional_services_details': additional_services_details, # <-- Сохраняем details
                'frequency': 'one_time',
                'bring_vacuum': False, 'is_private_house': False,
                'estimated_duration_minutes': kitchen_service.base_duration_minutes,
                'total_price': str(total_price),
            }
            request.session['order_summary'] = summary
            return redirect(reverse('orders:order_create'))
        except Service.DoesNotExist:
            messages.error(request, _("Kitchen Cleaning service is not available at the moment."))
            return redirect('kitchen_cleaning')
        except Exception as e:
            logger.error(f"Error starting kitchen order: {e}", exc_info=True)
            messages.error(request, _("An unexpected error occurred. Please try again."))
            return redirect('kitchen_cleaning')
    return redirect('kitchen_cleaning')

def create_checkout_session(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.payment_status == 'paid':
        messages.error(request, _("This order has already been paid for."))
        return redirect('index')
    success_url = request.build_absolute_uri(reverse('orders:payment_success'))
    cancel_url = request.build_absolute_uri(reverse('orders:payment_cancel'))
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'pln',
                    'product_data': {'name': f'Order #{order.id} - {order.service.name}'},
                    'unit_amount': int(order.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=order.customer_email,
            metadata={'order_id': order.id}
        )
        order.stripe_session_id = session.id
        order.save()
        return redirect(session.url, code=303)
    except Exception as e:
        logger.error(f"Stripe session creation failed for order {order.id}: {e}", exc_info=True)
        return HttpResponse(_("An error occurred while creating the payment session. Please try again later."), status=500)

class PaymentSuccessView(TemplateView):
    template_name = 'orders/payment_success.html'

class PaymentCancelView(TemplateView):
    template_name = 'orders/payment_cancel.html'


def initialize_order(request):
    """
    Принимает POST-запрос со страниц услуг/цен,
    сохраняет выбранную услугу в сессию и перенаправляет.
    """
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        if not service_id:
            messages.error(request, _("Please select a service."))
            return redirect(request.META.get('HTTP_REFERER', 'index'))
        
        try:
            service = get_object_or_404(Service, id=service_id)
            summary = {
                'service_id': service.id,
                'service_name': str(service.name),
                'is_window_service': service.is_window_service,
                'is_kitchen_service': service.slug == 'kitchen-cleaning',
                'rooms_count': 1,
                'bathrooms_count': 1,
                'total_price': str(service.base_price),
                'additional_services_details': [] # <-- Пустой список по умолчанию
            }
            request.session['order_summary'] = summary
            return redirect(reverse('orders:order_create'))

        except Exception as e:
            logger.error(f"Error initializing order for service_id {service_id}: {e}")
            messages.error(request, _("An unexpected error occurred. Please try again."))
            return redirect('index')
            
    return redirect('index')    


def initialize_order_from_list(request):
    """
    Принимает POST-запрос со страниц услуг/цен.
    """
    if request.method == 'POST':
        main_service_id = request.POST.get('main_service')
        additional_services_ids = request.POST.getlist('additional_services')

        if not main_service_id:
            messages.error(request, _("Please select a main service to proceed."))
            return redirect(request.META.get('HTTP_REFERER', reverse('index')))

        try:
            main_service = get_object_or_404(Service, id=main_service_id)
            total_price = main_service.base_price
            
            # --- ИЗМЕНЕНИЕ: Формируем details ---
            additional_services_details = []
            if additional_services_ids:
                add_services_objs = AdditionalService.objects.filter(id__in=additional_services_ids)
                for svc in add_services_objs:
                    total_price += svc.price
                    additional_services_details.append({
                        'name': svc.name,
                        'price': float(svc.price),
                        'quantity': 1
                    })
            # ------------------------------------

            summary = {
                'service_id': main_service.id,
                'service_name': str(main_service.name),
                'is_window_service': main_service.is_window_service,
                'additional_services_details': additional_services_details, # <-- Сохраняем details
                'rooms_count': 1,
                'bathrooms_count': 1,
                'sqm': 0,
                'frequency': 'one_time',
                'bring_vacuum': False,
                'is_private_house': False,
                'estimated_duration_minutes': main_service.base_duration_minutes,
                'total_price': str(total_price),
            }
            request.session['order_summary'] = summary
            return redirect(reverse('orders:order_create'))

        except Exception as e:
            logger.error(f"Error initializing order from list: {e}", exc_info=True)
            messages.error(request, _("An unexpected error occurred. Please try again."))
            return redirect('index')

    return redirect('index')