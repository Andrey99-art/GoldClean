from django import forms
from .models import Review
from django.utils.translation import gettext_lazy as _

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        # Указываем, какие поля будет заполнять пользователь
        fields = ['author_name', 'text', 'rating']
        
        labels = {
            'author_name': _("Your Name (optional)"),
            'text': _("Your Review"),
            'rating': _("Your Rating"),
        }
        
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Enter your name")
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _("Share your experience with us...")
            }),
            'rating': forms.Select(
                choices=[(5, '★★★★★'), (4, '★★★★☆'), (3, '★★★☆☆'), (2, '★★☆☆☆'), (1, '★☆☆☆☆')],
                attrs={'class': 'form-select'}
            ),
        }