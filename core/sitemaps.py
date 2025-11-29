# ПУТЬ: cleaning_service/core/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Service

class StaticViewSitemap(Sitemap):
    """Карта статических страниц (Главная, Цены, О нас)"""
    priority = 0.8
    changefreq = 'weekly'
    i18n = True  # Генерирует ссылки для всех языков

    def items(self):
        return ['index', 'services', 'pricing', 'about', 'window_cleaning', 'kitchen_cleaning']

    def location(self, item):
        return reverse(item)

# Если у тебя будут детальные страницы услуг (например /service/regular-cleaning/),
# раскомментируй этот блок:
# class ServiceSitemap(Sitemap):
#     priority = 0.9
#     changefreq = 'weekly'
#     i18n = True
#     def items(self):
#         return Service.objects.filter(is_active=True)