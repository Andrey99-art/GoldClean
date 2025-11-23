# File: core/management/commands/authorize_gmail.py (ФИНАЛЬНАЯ ВЕРСИЯ)

import os
from django.core.management.base import BaseCommand
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'

class Command(BaseCommand):
    help = 'Проводит OAuth2 авторизацию для отправки писем через Gmail API (финальный метод)'

    def handle(self, *args, **options):
        # Используем специальный "loopback" метод, который требует redirect_uri http://localhost:[PORT]
        # Убедитесь, что http://localhost:8000/ добавлен в Google Cloud Console
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(host='localhost', port=8000, 
                                      authorization_prompt_message='Пожалуйста, авторизуйтесь в открывшемся окне браузера...', 
                                      success_message='Авторизация прошла успешно! Можете закрыть это окно.')

        # Сохраняем учетные данные для будущего использования
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        self.stdout.write(self.style.SUCCESS(f'Токен успешно сохранен в файл {TOKEN_FILE}'))
        self.stdout.write(self.style.WARNING('Убедитесь, что вы добавили token.json в ваш .gitignore файл.'))