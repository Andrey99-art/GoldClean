# File: core/context_processors.py 

from .models import SiteConfiguration, PromoBanner


def site_settings(request):
    """
    Добавляет объект настроек сайта в контекст каждого шаблона.
    """
    try:
        config = SiteConfiguration.get_solo()
        return {'site_config': config}
    except SiteConfiguration.DoesNotExist:
        return {}


def promo_banner(request):
    """
    Добавляет активный промо-баннер в контекст.
    Выбирает баннер с наивысшим приоритетом, который сейчас должен отображаться.
    """
    try:
        # Получаем все активные баннеры, отсортированные по приоритету
        banners = PromoBanner.objects.filter(is_active=True).order_by('-priority', '-created_at')
        
        # Находим первый видимый баннер
        for banner in banners:
            if banner.is_visible():
                return {'promo_banner': banner}
        
        return {'promo_banner': None}
    except:
        return {'promo_banner': None}