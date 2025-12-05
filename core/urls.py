# File: core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('kitchen-cleaning/', views.kitchen_cleaning_view, name='kitchen_cleaning'),
    path('start-order-from-list/', views.start_order_from_list, name='start_order_from_list'),
    path('calculate/', views.calculate_price, name='calculate_price'),
    
    path('window-cleaning/', views.window_cleaning_view, name='window_cleaning'),
    path('calculate-windows/', views.calculate_window_price, name='calculate_window_price'),
    
    path('services/', views.services_view, name='services'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('about-us/', views.about_view, name='about'),

    # Legal pages
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms/', views.terms_view, name='terms'),
]