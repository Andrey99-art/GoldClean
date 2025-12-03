#!/bin/sh
# ПУТЬ: entrypoint.sh
# КОНТЕКСТ: Надёжный entrypoint с автосозданием базы

set -e

echo "=== Waiting for PostgreSQL ==="
while ! nc -z $DB_HOST $DB_PORT; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up!"

# === КРИТИЧНО: Проверяем/создаём базу данных ===
echo "=== Checking if database exists ==="
export PGPASSWORD=$DB_PASSWORD

DB_EXISTS=$(psql -h $DB_HOST -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" != "1" ]; then
    echo "Database $DB_NAME does not exist. Creating..."
    psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
    echo "Database $DB_NAME created successfully!"
else
    echo "Database $DB_NAME already exists."
fi

unset PGPASSWORD

# === Применяем миграции ===
echo "=== Applying migrations ==="
python manage.py migrate --noinput

# === Собираем статику ===
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

# === Запускаем Gunicorn ===
echo "=== Starting Gunicorn ==="
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --access-logfile - \
    --error-logfile -