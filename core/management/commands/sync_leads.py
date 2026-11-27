"""
Management command для синхронизации лидов из Google Sheets в Django.
Google Sheets: "GoldClean Wars. Leads"
Запуск: python manage.py sync_leads
"""
import os
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from core.models import Lead
from core.telegram import notify_new_lead


SPREADSHEET_ID = '1R6c9IgXe19xVGO1PfOO9HmWv2UEwIdytCJstruA-1sg'
RANGE_NAME = 'Аркуш1!A2:Q'  # Начинаем со 2-й строки (1-я = заголовки)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class Command(BaseCommand):
    help = 'Синхронизация лидов из Google Sheets (Instagram Lead Ads) в Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет синхронизировано, без записи в БД',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('🔄 Начинаю синхронизацию лидов из Google Sheets...')
        
        # Подключение к Google Sheets
        creds_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        if not os.path.exists(creds_path):
            self.stderr.write(self.style.ERROR(f'❌ Файл credentials.json не найден: {creds_path}'))
            return
        
        try:
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()
            
            result = sheet.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME
            ).execute()
            
            rows = result.get('values', [])
            self.stdout.write(f'📊 Найдено строк в таблице: {len(rows)}')
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка подключения к Google Sheets: {e}'))
            return
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, row in enumerate(rows, start=2):  # start=2 т.к. строка 1 = заголовки
            # Пропускаем пустые строки
            if not row or not row[0].strip():
                continue
            
            # Проверяем, есть ли уже такой лид (по номеру строки)
            if Lead.objects.filter(sheets_row_id=i).exists():
                skipped_count += 1
                continue
            
            try:
                # Парсим данные из строки
                # A=0: Имя, B=1: Время, C=2: Услуга, D=3: Телефон, E=4: Email
                # F=5: Время обработки, G=6: Статус обработки, H=7: Аудитория
                # I=8: Статус заказа, J=9: Комментарии, K=10: Сумма
                # L=11: Кампания, M=12: Группа объявлений, N=13: Платформа
                # O=14: Форма, P=15: Откуда пришел, Q=16: Месяц
                
                def get_col(idx, default=''):
                    return row[idx].strip() if idx < len(row) and row[idx] else default
                
                name = get_col(0)
                phone = get_col(3)
                email = get_col(4)
                
                if not name and not phone:
                    continue
                
                # Парсим дату поступления
                lead_received_at = None
                date_str = get_col(1)
                if date_str:
                    for fmt in ('%d.%m.%Y %H:%M', '%Y-%m-%d %H:%M', '%d.%m.%Y'):
                        try:
                            naive_dt = datetime.strptime(date_str, fmt)
                            lead_received_at = timezone.make_aware(naive_dt)
                            break
                        except ValueError:
                            continue
                
                # Определяем источник
                platform_raw = get_col(13).lower()
                if platform_raw == 'ig':
                    source = 'instagram'
                    platform = 'ig'
                elif platform_raw == 'fb':
                    source = 'facebook'
                    platform = 'fb'
                else:
                    source = 'other'
                    platform = platform_raw
                
                # Статус обработки
                processing_raw = get_col(6).lower()
                if 'обработана' in processing_raw:
                    processing_status = 'processed'
                else:
                    processing_status = 'not_processed'
                
                # Статус заказа
                order_raw = get_col(8).lower()
                if 'в процессе' in order_raw or 'in progress' in order_raw:
                    order_status = 'in_progress'
                elif 'не заказал' in order_raw:
                    order_status = 'not_ordered'
                elif order_raw:
                    order_status = 'ordered'
                else:
                    order_status = 'not_ordered'
                
                # Сумма заказа
                order_amount = None
                amount_str = get_col(10)
                if amount_str:
                    try:
                        order_amount = float(amount_str.replace(',', '.').replace(' ', '').replace('zł', ''))
                    except ValueError:
                        pass
                
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] Строка {i}: {name} | {phone} | {get_col(2)} | {source}')
                    created_count += 1
                    continue
                
                Lead.objects.create(
                    name=name,
                    phone=phone,
                    email=email,
                    message=get_col(9),  # Комментарии
                    service_name=get_col(2),
                    source=source,
                    platform=platform,
                    audience=get_col(7),
                    campaign=get_col(11),
                    ad_group=get_col(12),
                    processing_time=get_col(5),
                    processing_status=processing_status,
                    order_status=order_status,
                    order_amount=order_amount,
                    lead_received_at=lead_received_at,
                    admin_notes=f"Форма: {get_col(14)}",
                    sheets_row_id=i,
                    status='new',
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Строка {i}: {name} ({phone})'))
                try:
                    notify_new_lead(Lead.objects.get(sheets_row_id=i))
                except Exception as e:
                    self.stderr.write(f'  ⚠️ Telegram: {e}')
                
            except Exception as e:
                error_count += 1
                self.stderr.write(self.style.ERROR(f'  ❌ Строка {i}: {e}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'📈 Результат:'))
        self.stdout.write(f'  Создано: {created_count}')
        self.stdout.write(f'  Пропущено (уже есть): {skipped_count}')
        self.stdout.write(f'  Ошибок: {error_count}')
