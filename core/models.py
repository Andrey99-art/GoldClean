# File: core/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from solo.models import SingletonModel

class CleaningArea(models.Model):
    title = models.CharField(_("Title"), max_length=100, help_text=_("e.g., 'Bathroom', 'Kitchen'"))
    image = models.ImageField(_("Image"), upload_to='cleaning_areas/')
    order = models.PositiveIntegerField(_("Display Order"), default=0, help_text=_("Lower numbers are displayed first."))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Cleaning Area")
        verbose_name_plural = _("Cleaning Areas")
        ordering = ['order']


class FeaturePoint(models.Model):
    area = models.ForeignKey(
        CleaningArea, 
        on_delete=models.CASCADE, 
        related_name='feature_points', 
        verbose_name=_("Cleaning Area")
    )
    description = models.CharField(_("Description"), max_length=200)
    position_x = models.FloatField(
        _("Position X (%)"), 
        default=50.0, 
        help_text=_("Horizontal position from left to right, in percent (e.g., 25.5)")
    )
    position_y = models.FloatField(
        _("Position Y (%)"), 
        default=50.0, 
        help_text=_("Vertical position from top to bottom, in percent (e.g., 70)")
    )

    def __str__(self):
        return self.description


class SiteConfiguration(SingletonModel):
    cancellation_fee = models.DecimalField(
        _("Cancellation Fee (zł)"),
        max_digits=10,
        decimal_places=2,
        default=50.00,
        help_text=_("The fee charged for cancellations made less than 24 hours in advance.")
    )
    services_page_enabled = models.BooleanField(
        _("Показывать страницу 'Услуги'"),
        default=True,
        help_text=_("Если флаг выключен, ссылка на страницу 'Услуги' исчезнет из навигации сайта.")
    )
    telegram_link = models.URLField(
        _("Telegram Link"),
        max_length=255, 
        blank=True,     
        null=True, 
        help_text=_("Full URL to the Telegram account, e.g., https://t.me/your_account")
    )
    whatsapp_link = models.URLField(
       _("WhatsApp Link"),
       max_length=255,
       blank=True,
       null=True,
       help_text=_("Full URL to WhatsApp, e.g., https://wa.me/48781628269")
    )

    def __str__(self):
        return str(_("Site Configuration"))

    class Meta:
        verbose_name = _("Site Configuration")


class PromoBanner(models.Model):
    """Промо-баннер для праздников и акций"""
    
    CONTENT_TYPE_CHOICES = [
        ('image', _('Image (PNG, JPG, GIF)')),
        ('video', _('Video (MP4, WebM)')),
        ('lottie', _('Lottie Animation (JSON)')),
        ('text_only', _('Text Only')),
    ]
    
    # Основные поля
    name = models.CharField(
        _("Banner Name"),
        max_length=100,
        help_text=_("Internal name for admin, e.g., 'New Year 2026'")
    )
    content_type = models.CharField(
        _("Content Type"),
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='image'
    )
    
    # Медиа контент
    image = models.ImageField(
        _("Image / GIF"),
        upload_to='promo_banners/',
        blank=True,
        null=True,
        help_text=_("Upload image or animated GIF")
    )
    video_file = models.FileField(
        _("Video File"),
        upload_to='promo_banners/videos/',
        blank=True,
        null=True,
        help_text=_("Upload MP4 or WebM video")
    )
    lottie_json = models.FileField(
        _("Lottie Animation"),
        upload_to='promo_banners/lottie/',
        blank=True,
        null=True,
        help_text=_("Upload Lottie JSON file")
    )
    
    # Текстовый контент
    title = models.CharField(
        _("Title"),
        max_length=200,
        blank=True,
        help_text=_("Holiday greeting or promo title")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Additional text or message")
    )
    
    # Ссылка
    link = models.URLField(
        _("Link URL"),
        blank=True,
        null=True,
        help_text=_("Optional: URL to open when banner is clicked")
    )
    link_text = models.CharField(
        _("Link Button Text"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("Text for the button, e.g., 'Learn more'")
    )
    
    # Период показа
    start_date = models.DateTimeField(
        _("Start Date"),
        blank=True,
        null=True,
        help_text=_("When to start showing the banner. Leave empty to show immediately.")
    )
    end_date = models.DateTimeField(
        _("End Date"),
        blank=True,
        null=True,
        help_text=_("When to stop showing the banner. Leave empty to show indefinitely.")
    )
    
    # Настройки отображения
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Enable or disable this banner")
    )
    show_border = models.BooleanField(
        _("Show Border"),
        default=True,
        help_text=_("Show decorative border around the banner")
    )
    border_style = models.CharField(
        _("Border Style"),
        max_length=20,
        choices=[
            ('gold', _('Gold (default)')),
            ('festive', _('Festive (animated)')),
            ('minimal', _('Minimal')),
            ('none', _('No border')),
        ],
        default='gold'
    )
    background_color = models.CharField(
        _("Background Color"),
        max_length=20,
        blank=True,
        default='',
        help_text=_("CSS color, e.g., '#ffffff' or 'transparent'")
    )
    
    # Приоритет (если несколько баннеров активны)
    priority = models.PositiveIntegerField(
        _("Priority"),
        default=0,
        help_text=_("Higher number = higher priority. Banner with highest priority will be shown.")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Promo Banner")
        verbose_name_plural = _("Promo Banners")
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.name

    def is_visible(self):
        """Проверяет, должен ли баннер отображаться сейчас"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    is_visible.boolean = True
    is_visible.short_description = _("Currently Visible")

    class Lead(models.Model):
     """
     Модель для хранения заявок с pop-up формы.
     """
    STATUS_CHOICES = [
        ('new', _('New')),
        ('contacted', _('Contacted')),
        ('converted', _('Converted to Order')),
        ('cancelled', _('Cancelled')),
    ]
    
    name = models.CharField(_('Name'), max_length=100)
    phone = models.CharField(_('Phone'), max_length=20)
    email = models.EmailField(_('Email'))
    message = models.TextField(_('Message'), blank=True)
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    converted_user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        verbose_name=_('Converted User')
    )
    
    admin_notes = models.TextField(_('Admin Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.phone} ({self.get_status_display()})"