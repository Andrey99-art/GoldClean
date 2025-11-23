from django.db import migrations

CITIES_TO_ADD = [
    {'name': 'Warszawa', 'charge': 0.00},
    {'name': 'Piastów', 'charge': 30.00},
    {'name': 'Pruszków', 'charge': 30.00},
    {'name': 'Piaseczno', 'charge': 30.00},
    {'name': 'Sulejówek', 'charge': 40.00},
    {'name': 'Kobyłka', 'charge': 50.00},
    {'name': 'Ożarów Mazowiecki', 'charge': 50.00},
    {'name': 'Zielonka', 'charge': 40.00},
    {'name': 'Legionowo', 'charge': 40.00},
    {'name': 'Józefosław', 'charge': 60.00},
    {'name': 'Ząbki', 'charge': 30.00},
    {'name': 'Stare Babice', 'charge': 30.00},
    {'name': 'Brwinów', 'charge': 50.00},
    {'name': 'Grodzisk Mazowiecki', 'charge': 60.00},
    {'name': 'Marki', 'charge': 30.00},
    {'name': 'Raszyn', 'charge': 25.00},
    {'name': 'Łomianki', 'charge': 40.00},
    {'name': 'Łazy', 'charge': 50.00},
    {'name': 'Nowa Iwiczna', 'charge': 50.00},
    {'name': 'Wołomin', 'charge': 40.00},
    {'name': 'Konstancin-Jeziorna', 'charge': 50.00},
    {'name': 'Jabłonna', 'charge': 40.00},
    {'name': 'Młochów', 'charge': 60.00},
    {'name': 'Milanówek', 'charge': 50.00},
    {'name': 'Mysłiadło', 'charge': 40.00},
    {'name': 'Nowa Wola', 'charge': 60.00},
    {'name': 'Janki', 'charge': 45.00},
    {'name': 'Góraszka', 'charge': 65.00},
]

# Функция, которая будет добавлять города
def add_cities_data(apps, schema_editor):
    # Получаем историческую версию модели City, чтобы миграция была безопасной
    City = apps.get_model('orders', 'City')
    for city_data in CITIES_TO_ADD:
        # Используем get_or_create, чтобы избежать дубликатов при повторном запуске
        City.objects.get_or_create(name=city_data['name'], defaults={'delivery_charge': city_data['charge']})

# Функция, которая будет удалять города при откате миграции
def remove_cities_data(apps, schema_editor):
    City = apps.get_model('orders', 'City')
    city_names = [city['name'] for city in CITIES_TO_ADD]
    City.objects.filter(name__in=city_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_city_remove_order_customer_address_apartment_and_more'),
    ]

    operations = [
        migrations.RunPython(add_cities_data, reverse_code=remove_cities_data),
    ]