# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    penalty_balance = models.DecimalField(
        _("Penalty Balance"),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    def __str__(self):
        return f"Profile for {self.user.username}"

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")