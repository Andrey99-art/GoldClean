"""
Утилита для отправки уведомлений в Telegram.
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram(message, parse_mode='HTML'):
    """Отправляет сообщение во все чаты из TELEGRAM_CHAT_IDS."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_ids = getattr(settings, 'TELEGRAM_CHAT_IDS', [])
    
    if not token or not chat_ids:
        logger.warning('Telegram not configured')
        return
    
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    for chat_id in chat_ids:
        try:
            response = requests.post(url, data={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode,
            }, timeout=10)
            if not response.ok:
                logger.error(f'Telegram error: {response.text}')
        except Exception as e:
            logger.error(f'Telegram send failed: {e}')


def notify_new_lead(lead):
    """Уведомление о новом лиде из Instagram."""
    msg = '\U0001f195 <b>Новый лид!</b>\n\n'
    msg += '\U0001f464 ' + (lead.name or '-') + '\n'
    msg += '\U0001f4de ' + (lead.phone or '-') + '\n'
    msg += '\U0001f4e7 ' + (lead.email or '-') + '\n'
    msg += '\U0001f9f9 ' + (lead.service_name or '-') + '\n'
    msg += '\U0001f4e2 ' + lead.get_source_display() + '\n'
    if lead.lead_received_at:
        msg += '\U0001f4c5 ' + lead.lead_received_at.strftime('%d.%m.%Y %H:%M') + '\n'
    msg += '\n\U0001f449 <a href="https://goldclean2026.pl/admin/core/lead/' + str(lead.pk) + '/change/">Открыть в CRM</a>'
    send_telegram(msg)


def notify_website_lead(name, phone, email, message=''):
    """Уведомление о заявке с pop-up формы сайта."""
    msg = '\U0001f4e9 <b>Заявка с сайта!</b>\n\n'
    msg += '\U0001f464 <b>Имя:</b> ' + name + '\n'
    msg += '\U0001f4de <b>Телефон:</b> ' + phone + '\n'
    msg += '\U0001f4e7 <b>Email:</b> ' + email + '\n'
    if message:
        msg += '\U0001f4ac <b>Сообщение:</b>\n' + message + '\n'
    msg += '\n\U0001f310 <i>Источник: pop-up форма на сайте goldclean2026.pl</i>'
    send_telegram(msg)


def notify_new_order(order):
    """Уведомление о новом заказе."""
    payment_icons = {'cash': '\U0001f4b5 Наличные', 'card': '\U0001f4b3 Карта (BLIK)'}
    payment = payment_icons.get(order.payment_method, order.payment_method or '-')
    
    freq_map = {'one_time': 'Разовая', 'weekly': 'Еженедельно', 'bi_weekly': 'Раз в 2 недели', 'monthly': 'Ежемесячно'}
    frequency = freq_map.get(order.frequency, order.frequency or 'Разовая')
    
    additional = ''
    if order.additional_services_details:
        try:
            services = order.additional_services_details
            if isinstance(services, list) and services:
                names = [s.get('name', '') for s in services if s.get('name')]
                if names:
                    additional = ', '.join(names)
        except Exception:
            pass
    
    msg = '\U0001f4e6 <b>Новый заказ!</b>\n\n'
    msg += '\U0001f464 <b>Клиент:</b> ' + (order.customer_name or '-') + '\n'
    msg += '\U0001f4de <b>Телефон:</b> ' + (order.customer_phone or '-') + '\n'
    msg += '\U0001f4e7 <b>Email:</b> ' + (order.customer_email or '-') + '\n\n'
    
    msg += '\U0001f9f9 <b>Услуга:</b> ' + str(order.service or '-') + '\n'
    rooms = str(order.rooms_count) if order.rooms_count else '-'
    baths = str(order.bathrooms_count) if order.bathrooms_count else '-'
    msg += '\U0001f3e0 <b>Комнат:</b> ' + rooms + ' | <b>Санузлов:</b> ' + baths + '\n'
    if order.sqm:
        msg += '\U0001f4cf <b>Площадь:</b> ' + str(order.sqm) + ' m2\n'
    if order.window_count:
        msg += '\U0001fa9f <b>Окон:</b> ' + str(order.window_count) + '\n'
    if additional:
        msg += '\u2795 <b>Доп. услуги:</b> ' + additional + '\n'
    if order.bring_vacuum_cleaner:
        msg += '\U0001f9f9 Пылесос: нужен\n'
    if order.is_private_house:
        msg += '\U0001f3e1 Тип: Частный дом\n'
    msg += '\U0001f504 <b>Частота:</b> ' + frequency + '\n\n'
    
    if order.cleaning_date:
        msg += '\U0001f4c5 <b>Дата:</b> ' + order.cleaning_date.strftime('%d.%m.%Y') + '\n'
    if order.cleaning_time:
        msg += '\u23f0 <b>Время:</b> ' + order.cleaning_time.strftime('%H:%M') + '\n'
    if order.estimated_duration_minutes:
        hours = order.estimated_duration_minutes // 60
        mins = order.estimated_duration_minutes % 60
        msg += '\u23f1 <b>Длительность:</b> ' + str(hours) + 'ч ' + str(mins) + 'мин\n'
    msg += '\n'
    
    addr = str(order.city or '') + ', ' + (order.street or '') + ' ' + (order.building_number or '')
    if order.apartment_number:
        addr += ', кв. ' + order.apartment_number
    if order.floor:
        addr += ', эт. ' + order.floor
    msg += '\U0001f4cd <b>Адрес:</b> ' + addr + '\n'
    if order.intercom_code:
        msg += '\U0001f511 <b>Домофон:</b> ' + order.intercom_code + '\n'
    if order.comments:
        msg += '\U0001f4ac <b>Комментарий:</b> ' + order.comments + '\n'
    msg += '\n'
    
    msg += '\U0001f4b0 <b>Сумма:</b> ' + '{:.0f}'.format(float(order.total_price or 0)) + ' zl\n'
    msg += payment + '\n\n'
    msg += '\U0001f449 <a href="https://goldclean2026.pl/admin/orders/order/' + str(order.pk) + '/change/">Открыть в CRM</a>'
    
    send_telegram(msg)


def notify_order_status(order):
    """Уведомление об изменении статуса заказа."""
    status_icons = {
        'new': '\U0001f195', 'pending': '\u23f3',
        'in_progress': '\U0001f504', 'confirmed': '\u2705',
        'completed': '\u2705', 'canceled': '\u274c',
    }
    icon = status_icons.get(order.status, '\U0001f4cb')
    msg = icon + ' <b>Статус заказа #' + str(order.pk) + ' изменён</b>\n\n'
    msg += '\U0001f464 ' + (order.customer_name or '-') + '\n'
    msg += '\U0001f4ca ' + order.get_status_display() + '\n'
    msg += '\U0001f9f9 ' + str(order.service or '-') + '\n'
    if order.cleaning_date:
        msg += '\U0001f4c5 ' + order.cleaning_date.strftime('%d.%m.%Y') + '\n'
    msg += '\n\U0001f449 <a href="https://goldclean2026.pl/admin/orders/order/' + str(order.pk) + '/change/">Открыть</a>'
    send_telegram(msg)
