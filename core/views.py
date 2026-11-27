# File: core/views.py

import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from gallery.models import GalleryImage
from orders.models import Order
from products.models import AdditionalService, KitchenCleaningFeature, Service
from reviews.models import Review

from .models import CleaningArea
from .utils import format_duration

logger = logging.getLogger(__name__)

# Constants
# Дефолтные значения (переопределяются из SiteConfiguration)
DISCOUNT_WEEKLY = Decimal('0.20')
DISCOUNT_BI_WEEKLY = Decimal('0.15')
DISCOUNT_MONTHLY = Decimal('0.10')
ADDITIONAL_ROOM_DURATION_MINUTES = 30
ADDITIONAL_BATHROOM_DURATION_MINUTES = 60
PRIVATE_HOUSE_MULTIPLIER = Decimal('1.2')

@require_POST
@csrf_protect
def submit_lead_form(request):
    """
    Обработка pop-up формы захвата лидов.
    Отправляет данные на email администратора.
    """
    try:
        data = json.loads(request.body)
        
        phone = data.get('phone', '').strip()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        # Валидация
        if not phone or not name or not email:
            return JsonResponse({
                'success': False,
                'error': _('Please fill in all required fields.')
            }, status=400)
        
        # Формируем email
        subject = f'🔔 Новая заявка с сайта Gold Clean - {name}'
        
        # Текстовая версия
        text_content = f"""
Новая заявка с сайта Gold Clean!

📞 Телефон: {phone}
👤 Имя: {name}
📧 Email: {email}

💬 Сообщение:
{message if message else 'Не указано'}

---
Эта заявка отправлена через pop-up форму на сайте.
        """
        
        # HTML версия
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9;">
            <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: #B89E40; margin: 0; font-size: 24px;">🔔 Новая заявка</h1>
                <p style="color: #fff; margin: 10px 0 0; opacity: 0.8;">Gold Clean Website</p>
            </div>
            
            <div style="background: #fff; padding: 25px; border: 1px solid #e0e0e0; border-top: none;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0;">
                            <strong style="color: #666;">📞 Телефон:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; text-align: right;">
                            <a href="tel:{phone}" style="color: #B89E40; text-decoration: none; font-weight: bold;">{phone}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0;">
                            <strong style="color: #666;">👤 Имя:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; text-align: right;">
                            {name}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0;">
                            <strong style="color: #666;">📧 Email:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; text-align: right;">
                            <a href="mailto:{email}" style="color: #B89E40; text-decoration: none;">{email}</a>
                        </td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background: #f8f8f8; border-radius: 8px;">
                    <strong style="color: #666;">💬 Сообщение:</strong>
                    <p style="margin: 10px 0 0; color: #333; line-height: 1.6;">
                        {message if message else '<em style="color: #999;">Не указано</em>'}
                    </p>
                </div>
                

            </div>
            
            <div style="background: #1a1a1a; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
                <p style="color: #888; margin: 0; font-size: 12px;">
                    Заявка отправлена через pop-up форму на сайте goldclean2026.pl
                </p>
            </div>
        </div>
        """
        
        # Отправляем email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=html_content,
            fail_silently=False,
        )
        
        # Можно также отправить копию клиенту
        client_subject = _('Thank you for your inquiry - Gold Clean')
        client_text = f"""
{_('Dear')} {name},

{_('Thank you for contacting Gold Clean!')}

{_('We have received your inquiry and will contact you shortly.')}


{_('Your contact details:')}
📞 {phone}
📧 {email}

{_('Best regards,')}
Gold Clean Team
+48 781 628 269
        """
        
        send_mail(
            subject=client_subject,
            message=client_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,  # Не критично если не отправится
        )
        
        # Создаём лид в базе
        try:
            from core.models import Lead
            lead = Lead.objects.create(
                name=name,
                phone=phone,
                email=email,
                message=message,
                source='website',
                status='new',
            )
            # Отправляем уведомление в Telegram
            from core.telegram import notify_website_lead
            notify_website_lead(name, phone, email, message)
        except Exception:
            pass  # Не ломаем ответ клиенту

        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': _('Invalid data format.')
        }, status=400)
    except Exception as e:
        print(f"Lead form error: {e}")
        return JsonResponse({
            'success': False,
            'error': _('An error occurred. Please try again.')
        }, status=500)


def _get_base_context_data():
    """Возвращает базовый контекст для страниц с выбором услуг."""
    return {
        'main_services': Service.objects.all(),
        'additional_services': AdditionalService.objects.filter(is_active=True),
    }


def _create_or_update_order_summary(request, **kwargs):
    """Создает или обновляет 'order_summary' в сессии."""
    summary_data = {
        'service_id': kwargs.get('service_id'),
        'service_name': kwargs.get('service_name'),
        'is_sqm_based': kwargs.get('is_sqm_based'),
        'is_window_service': kwargs.get('is_window_service'),
        'sqm': kwargs.get('sqm', 0),
        'rooms_count': kwargs.get('rooms_count', 0),
        'bathrooms_count': kwargs.get('bathrooms_count', 0),
        'window_count': kwargs.get('window_count', 0),
        'additional_services_details': kwargs.get('additional_services_details', []),
        'estimated_duration_minutes': kwargs.get('estimated_duration_minutes', 0),
        'bring_vacuum': kwargs.get('bring_vacuum', False),
        'is_private_house': kwargs.get('is_private_house', False),
        'frequency': kwargs.get('frequency', 'one_time'),
        'total_price': float(kwargs.get('total_price', 0.0)),
    }
    request.session['order_summary'] = summary_data


def index(request):
    """
    Отображает главную страницу со всеми необходимыми данными.
    """

    main_services = Service.objects.filter(is_window_service=False, is_active=True)

    services = Service.objects.filter(is_window_service=False)
    additional_services = AdditionalService.objects.filter(is_active=True)
    gallery_images = GalleryImage.objects.all()
    reviews = Review.objects.filter(is_active=True)
    cleaning_areas = CleaningArea.objects.all()
    
    context = {
        'main_services': main_services, 
        'services': services,
        'additional_services': additional_services,
        'gallery_images': gallery_images,
        'reviews': reviews,
        'vacuum_price': settings.VACUUM_CLEANER_PRICE,
        'cleaning_areas': cleaning_areas,
    }
    return render(request, 'core/index.html', context)


def calculate_price(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data.get('service_id')
            if not service_id:
                return JsonResponse({'error': 'Основная услуга не выбрана'}, status=400)
            
            base_service = Service.objects.get(id=service_id)
            
            frequency = data.get('frequency', 'one_time')
            additional_services_data = data.get('additional_services', [])
            bring_vacuum = data.get('bring_vacuum', False)
            is_private_house = data.get('is_private_house', False)
            
            total_price = base_service.base_price
            total_duration = base_service.base_duration_minutes
            
            details = {'base_service_name': base_service.name, 'base_price': float(base_service.base_price), 'is_sqm_based': base_service.is_sqm_based}
            sqm, rooms_count, bathrooms_count, window_count = 0, 0, 0, 0

            if base_service.is_sqm_based:
                sqm = int(data.get('sqm') or 0)
                sqm_price = Decimal(sqm) * base_service.price_per_sqm
                total_price += sqm_price
                details.update({'sqm': sqm, 'sqm_price': float(sqm_price)})
                if base_service.duration_per_sqm > 0:
                    total_duration += sqm * base_service.duration_per_sqm
                    
                details.update({'sqm': sqm, 'sqm_price': float(sqm_price)})
            else:
                rooms_count = int(data.get('rooms') or 1)
                bathrooms_count = int(data.get('bathrooms') or 1)
                rooms_price = max(0, rooms_count - 1) * base_service.price_per_room
                bathrooms_price = max(0, bathrooms_count - 1) * base_service.price_per_bathroom
                total_price += rooms_price + bathrooms_price
                total_duration += max(0, rooms_count - 1) * ADDITIONAL_ROOM_DURATION_MINUTES + max(0, bathrooms_count - 1) * ADDITIONAL_BATHROOM_DURATION_MINUTES
                details.update({'rooms_count': rooms_count, 'bathrooms_count': bathrooms_count, 'rooms_bathrooms_price': float(rooms_price + bathrooms_price)})

            additional_services_price = Decimal('0.00')
            additional_services_names = []
            additional_services_details_for_session = []
            if additional_services_data:
                service_ids = [item['id'] for item in additional_services_data]
                add_services = AdditionalService.objects.filter(id__in=service_ids)
                services_map = {str(s.id): s for s in add_services}

                for item in additional_services_data:
                    service_obj = services_map.get(str(item['id']))
                    if service_obj:
                        quantity = int(item.get('quantity', 1))
                        item_price = service_obj.price * quantity
                        additional_services_price += item_price
                        
                        name = str(service_obj.name)
                        if quantity > 1:
                            name += f" (x{quantity})"
                        additional_services_names.append(name)
                        
                        total_duration += service_obj.duration_minutes * quantity
                        
                        additional_services_details_for_session.append({
                            'id': service_obj.id,
                            'name': str(service_obj.name),
                            'price': float(service_obj.price),
                            'quantity': quantity
                        })

            total_price += additional_services_price
            details.update({'additional_services_names': additional_services_names, 'additional_services_price': float(additional_services_price), 'formatted_duration': format_duration(total_duration)})

            vacuum_price = Decimal(str(settings.VACUUM_CLEANER_PRICE)) if bring_vacuum else Decimal('0.00')
            total_price += vacuum_price
            details['vacuum_price'] = float(vacuum_price)

            house_multiplier = PRIVATE_HOUSE_MULTIPLIER if is_private_house else Decimal('1.0')
            total_price *= house_multiplier
            details['house_multiplier'] = float(house_multiplier)
            details['frequency'] = frequency

            # Скидка за подписку
            discount_map = {'weekly': DISCOUNT_WEEKLY, 'bi_weekly': DISCOUNT_BI_WEEKLY, 'monthly': DISCOUNT_MONTHLY}
            subscription_discount = discount_map.get(frequency, Decimal('0.00'))
            
            # Скидка для новых клиентов (25%)
            DISCOUNT_NEW_CLIENT = Decimal('0.25')
            MAX_COMBINED_DISCOUNT = Decimal('0.30')
            
            new_client_discount = Decimal('0.00')
            is_new_client = False
            
            # Проверяем включена ли скидка в настройках
            from core.models import SiteConfiguration
            site_config = SiteConfiguration.objects.first()
            discount_enabled = site_config.new_client_discount_enabled if site_config else True

            if discount_enabled and request.user.is_authenticated:
                try:
                    profile = request.user.profile
                    if profile.is_new_client:
                        is_new_client = True
                        new_client_discount = DISCOUNT_NEW_CLIENT
                except:
                    pass
            
            # Комбинируем скидки (максимум 30%)
            combined_discount = min(subscription_discount + new_client_discount, MAX_COMBINED_DISCOUNT)
            
            price_before_discount = total_price
            discount_amount = total_price * combined_discount
            final_price = total_price - discount_amount
            
            _create_or_update_order_summary(
                request, service_id=base_service.id, service_name=str(base_service.name),
                is_sqm_based=base_service.is_sqm_based, is_window_service=base_service.is_window_service,
                sqm=sqm, rooms_count=rooms_count, bathrooms_count=bathrooms_count,
                additional_services_details=additional_services_details_for_session,
                estimated_duration_minutes=total_duration, bring_vacuum=bring_vacuum,
                is_private_house=is_private_house, frequency=frequency, total_price=final_price
            )

            return JsonResponse({
                'total_price': float(final_price), 
                'base_total': float(price_before_discount), 
                'discount_amount': float(discount_amount), 
                'is_new_client': is_new_client,
                'details': details
            })
        
        except Service.DoesNotExist:
            return JsonResponse({'error': 'Основная услуга не найдена'}, status=404)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Data error in calculate_price: {e}")
            return JsonResponse({'error': 'Некорректные данные'}, status=400)
        except Exception as e:
            logger.exception("Unhandled error in calculate_price")
            return JsonResponse({'error': _("Произошла непредвиденная ошибка.")}, status=500)
            
    return JsonResponse({'error': 'Неверный метод запроса'}, status=405)


def window_cleaning_view(request):
    try:
        window_service = Service.objects.get(is_window_service=True)
        return render(request, 'core/windows.html', {'service': window_service})
    except Service.DoesNotExist:
        logger.warning("No window cleaning service found, redirecting to index.")
        messages.error(request, _("Window cleaning service is currently unavailable."))
        return redirect('index')


def calculate_window_price(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            service_id = data.get('service_id')
            window_count = int(data.get('window_count', 1))
            if window_count <= 0: window_count = 1

            service = Service.objects.get(id=service_id)
            total_price = Decimal(window_count) * service.price_per_sqm
            
            _create_or_update_order_summary(
                request, service_id=service.id, service_name=str(service.name),
                is_sqm_based=service.is_sqm_based, is_window_service=True,
                window_count=window_count, total_price=total_price
            )
            
            return JsonResponse({'total_price': float(total_price), 'price_per_window': float(service.price_per_sqm)})
        except Service.DoesNotExist:
            return JsonResponse({'error': 'Услуга по мытью окон не найдена'}, status=404)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Некорректные данные'}, status=400)
        except Exception as e:
            logger.exception("Unhandled error in calculate_window_price")
            return JsonResponse({'error': _("Произошла непредвиденная ошибка.")}, status=500)
    return JsonResponse({'error': 'Неверный метод запроса'}, status=405)


def services_view(request):
    return render(request, 'core/services.html', _get_base_context_data())


def pricing_view(request):
    return render(request, 'core/pricing.html', _get_base_context_data())


def about_view(request):
    return render(request, 'core/about.html')


def kitchen_cleaning_view(request):
    try:
        kitchen_service = Service.objects.get(slug='kitchen-cleaning')
        base_price = kitchen_service.base_price
    except Service.DoesNotExist:
        logger.warning("Service with slug 'kitchen-cleaning' not found. Using default values.")
        kitchen_service, base_price = None, Decimal('229.00')

    features = KitchenCleaningFeature.objects.all().order_by('order')
    additional_services = AdditionalService.objects.filter(is_active=True, is_for_kitchen=True).order_by('order')
    
    context = {
        'kitchen_service': kitchen_service, 'features': features,
        'base_price_str': str(base_price), 'additional_services': additional_services,
    }
    return render(request, 'core/kitchen_cleaning.html', context)


def start_order_from_list(request):
    if request.method == 'POST':
        main_service_id = request.POST.get('main_service')
        additional_services_ids = request.POST.getlist('additional_services')

        if not main_service_id:
            messages.error(request, _("Please select a main cleaning service."))
            return redirect(request.META.get('HTTP_REFERER', 'index'))

        try:
            main_service = get_object_or_404(Service, id=main_service_id)
            
            total_price = main_service.base_price
            total_duration = main_service.base_duration_minutes
            
            additional_services_details = []
            if additional_services_ids:
                additional_services = AdditionalService.objects.filter(id__in=additional_services_ids)
                for s in additional_services:
                    total_price += s.price
                    total_duration += s.duration_minutes
                    additional_services_details.append({
                        'id': s.id, 'name': str(s.name), 'price': float(s.price), 'quantity': 1
                    })
            
            _create_or_update_order_summary(
                request, service_id=main_service.id, service_name=str(main_service.name),
                is_sqm_based=main_service.is_sqm_based, is_window_service=main_service.is_window_service,
                additional_services_details=additional_services_details,
                estimated_duration_minutes=total_duration, total_price=total_price
            )
            return redirect(reverse('orders:order_create'))
        except Exception as e:
            logger.exception("Unhandled error in start_order_from_list")
            messages.error(request, _("An unexpected error occurred while starting your order."))
        return redirect(request.META.get('HTTP_REFERER', 'index'))
    return redirect('index')

def privacy_policy_view(request):
    """Страница политики конфиденциальности."""
    return render(request, 'core/legal/privacy_policy.html')


def terms_view(request):
    """Страница правил и условий."""
    return render(request, 'core/legal/terms.html')    
