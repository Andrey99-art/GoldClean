# Файл: core/context_processors.py 

from .models import SiteConfiguration

def site_settings(request):
    """
    Добавляет объект настроек сайта в контекст каждого шаблона.
    Это позволяет глобально получать доступ ко всем настройкам, таким как 
    TELEGRAM_LINK, services_page_enabled и т.д.
    """
    try:
        # get_solo() получает единственный экземпляр настроек
        config = SiteConfiguration.get_solo()
        # Возвращаем весь объект в контекст под именем 'site_config'
        return {'site_config': config}
    except SiteConfiguration.DoesNotExist:
        # Если настроек еще нет (например, после миграций), 
        # возвращаем пустой словарь, чтобы сайт не падал.
        return {}