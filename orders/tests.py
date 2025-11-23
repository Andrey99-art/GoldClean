# ПУТЬ: cleaning_service/orders/tests/test_integration.py
# КОНТЕКСТ: Проверка сквозного флоу "Калькулятор -> Сессия -> Заказ"

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Service, AdditionalService
from orders.models import Order, City

class OrderFlowIntegrationTest(TestCase):
    """
    Интеграционный тест проверяет полный цикл заказа:
    1. Расчет стоимости (API core).
    2. Сохранение данных в сессию.
    3. Оформление заказа (View orders).
    """

    def setUp(self):
        # 1. Настройка инфраструктуры данных
        self.client = Client()
        
        # Создаем город
        self.city = City.objects.create(name="Warsaw", delivery_charge=Decimal('10.00'))
        
        # Создаем основную услугу
        self.service = Service.objects.create(
            name="Standard Cleaning",
            slug="standard-cleaning",
            base_price=Decimal('100.00'),
            price_per_room=Decimal('20.00'),
            price_per_bathroom=Decimal('30.00'),
            base_duration_minutes=60,
            is_active=True
        )

        # Создаем доп. услугу
        self.add_service = AdditionalService.objects.create(
            name="Fridge Cleaning",
            price=Decimal('50.00'),
            duration_minutes=30,
            is_active=True
        )

    def test_full_order_creation_flow(self):
        """
        Сценарий: Пользователь выбирает 2 комнаты, 1 ванную и чистку холодильника.
        Ожидание: Цена рассчитана верно, заказ создан с правильной суммой.
        """
        
        # --- ШАГ 1: Эмуляция калькулятора (POST /calculate/) ---
        # Эмулируем AJAX запрос от JS
        calc_payload = {
            "service_id": self.service.id,
            "rooms": 2,      # +20 PLN (1 extra room)
            "bathrooms": 1,  # +0 PLN (base included)
            "frequency": "one_time",
            "additional_services": [{"id": self.add_service.id, "quantity": 1}] # +50 PLN
        }
        
        # Base (100) + Room (20) + Fridge (50) = 170.00 PLN
        expected_service_price = Decimal('170.00')

        response_calc = self.client.post(
            reverse('calculate_price'),
            data=calc_payload,
            content_type='application/json'
        )
        
        self.assertEqual(response_calc.status_code, 200)
        json_data = response_calc.json()
        self.assertEqual(float(json_data['total_price']), float(expected_service_price))

        # ПРОВЕРКА: Данные должны сохраниться в сессии
        session = self.client.session
        self.assertIn('order_summary', session)
        self.assertEqual(float(session['order_summary']['total_price']), float(expected_service_price))
        
        # --- ШАГ 2: Оформление заказа (POST /order/create/) ---
        order_payload = {
            'customer_name': 'Test User',
            'customer_phone': '123456789',
            'customer_email': 'test@example.com',
            'city': self.city.id, # Delivery +10.00
            'street': 'Test St',
            'postal_code': '00-001',
            'building_number': '1',
            'cleaning_date': '2025-12-01',
            'cleaning_time': '10:00',
            'payment_method': 'cash'
        }

        response_order = self.client.post(reverse('orders:order_create'), data=order_payload)

        # Ожидаем редирект на страницу успеха (т.к. оплата наличными)
        self.assertRedirects(response_order, reverse('orders:order_success'))

        # --- ШАГ 3: Проверка базы данных ---
        # Заказ должен быть создан
        self.assertEqual(Order.objects.count(), 1)
        created_order = Order.objects.first()

        # Проверка итоговой цены: Service (170) + Delivery (10) = 180
        expected_total = expected_service_price + self.city.delivery_charge
        self.assertEqual(created_order.total_price, expected_total)
        
        # Проверка JSON поля с доп. услугами
        self.assertEqual(len(created_order.additional_services_details), 1)
        self.assertEqual(created_order.additional_services_details[0]['name'], "Fridge Cleaning")

        # Проверка очистки сессии
        self.assertNotIn('order_summary', self.client.session)

        print(f"\n✅ TEST PASSED: Order created for {created_order.customer_name} with total {created_order.total_price} PLN")