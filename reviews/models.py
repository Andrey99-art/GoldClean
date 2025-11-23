from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone  # <--- ВЕРНУЛИ ЭТОТ ИМПОРТ (though not needed for auto_now_add)

class Review(models.Model):
    author_name = models.CharField(
        max_length=100, 
        verbose_name=_("Author's Name"), 
        blank=True, 
        null=True
    )
    text = models.TextField(verbose_name=_("Review Text"))
    rating = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating (1-5)")
    )
    
    # Use auto_now_add=True for automatic creation timestamp (non-editable, sets on first save only)
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Date Created")
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    order = models.PositiveIntegerField(default=0, blank=False, null=False, verbose_name=_("Display Order"))
    
    # New field to toggle date display on the frontend
    show_date = models.BooleanField(
        default=True,
        verbose_name=_("Show Creation Date on Site"),
        help_text=_("If checked, the creation date will be displayed on the website.")
    )

    def __str__(self):
        author = self.author_name if self.author_name else "Anonymous"
        return f"{author} - {self.rating} stars"
    
    def get_rating_range(self):
        return range(self.rating)

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ['-created_at']