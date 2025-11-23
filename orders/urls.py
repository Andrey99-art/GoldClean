# File: orders/urls.py

from django.urls import path
from . import views

# Добавляем app_name для использования пространства имен (например, 'orders:order_create')
app_name = 'orders'

urlpatterns = [
    # Существующие URL'ы
    path('create/', views.order_create, name='order_create'),
    path('success/', views.order_success, name='order_success'),
    path('start-kitchen-order/', views.start_kitchen_order, name='start_kitchen_order'),
    path('initialize/', views.initialize_order, name='initialize_order'),
    path('start-from-list/', views.initialize_order_from_list, name='start_order_from_list'),


    # --- НОВЫЕ URL'Ы ДЛЯ ИНТЕГРАЦИИ STRIPE ---
    # URL для создания сессии Stripe Checkout
    path('create-checkout-session/<int:order_id>/', views.create_checkout_session, name='create_checkout_session'),
    
    # URL'ы для страниц успеха и отмены после оплаты
    path('payment-success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payment-cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),
]