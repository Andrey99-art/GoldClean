from django.db import models
from django.utils.translation import gettext_lazy as _

class GalleryImage(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title / Description"))
    before_image = models.ImageField(upload_to='gallery/before/', verbose_name=_("'Before' Image"))
    after_image = models.ImageField(upload_to='gallery/after/', verbose_name=_("'After' Image"))
    order = models.PositiveIntegerField(default=0, blank=False, null=False, verbose_name=_("Display Order"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Gallery Image")
        verbose_name_plural = _("Gallery Images")
        ordering = ['order']