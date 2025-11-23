from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        # --- ПЛАНИРОВЩИК ОТКЛЮЧЕН ДЛЯ СТАБИЛЬНОСТИ DOCKER ---
        # В Gunicorn этот код вызывает падение воркеров из-за конфликта в БД.
        # Мы включим его позже правильно (через отдельный процесс).
        pass

        # from . import jobs
        # from django_apscheduler.jobstores import DjangoJobStore
        # from apscheduler.schedulers.background import BackgroundScheduler

        # scheduler = BackgroundScheduler()
        # scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # # Запускаем нашу задачу каждый день в 12:00
        # scheduler.add_job(
        #     jobs.send_cleaning_reminders,
        #     trigger='cron',
        #     hour='00',
        #     minute='00',
        #     id='send_cleaning_reminders_job',
        #     replace_existing=True,
        # )
        
        # try:
        #     print("Starting scheduler...")
        #     scheduler.start()
        # except Exception as e:
        #     print(f"Scheduler failed to start: {e}")