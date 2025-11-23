from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class RegistrationForm(UserCreationForm):
    # Добавляем только наше кастомное поле email
    email = forms.EmailField(
        required=True, 
        label=_("Email"),
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        # Говорим форме использовать стандартные поля ('username') + наше поле 'email'
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        # Вызываем родительский метод __init__, который создает все поля
        super(RegistrationForm, self).__init__(*args, **kwargs)
        
        # Теперь, когда все поля гарантированно существуют, мы можем их стилизовать.
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        
        # ИСПРАВЛЕНО: Используем правильные имена полей: 'password1' и 'password2'
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})