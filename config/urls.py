# ПУТЬ: config/urls.py

from django.contrib import admin
from django.urls import path, include 
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap 

sitemaps = {
    'static': StaticViewSitemap,
    # 'services': ServiceSitemap, # Если добавишь динамические услуги
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('order/', include('orders.urls', namespace='orders')),
    path('reviews/', include('reviews.urls')),
    path('accounts/', include('accounts.urls')),
    prefix_default_language=True,
)

# --- БЛОК DEBUG TOOLBAR ---
if settings.DEBUG:
    # Раздача медиа-файлов (у тебя это уже было)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    