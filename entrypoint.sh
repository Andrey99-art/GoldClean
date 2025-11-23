#!/bin/sh

# Ждем, пока база данных запустится
echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Применяем миграции
echo "Applying database migrations..."
python manage.py migrate

# Собираем статику (CSS/JS)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Запускаем Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3