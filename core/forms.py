from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации для кастомной модели User"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'})
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # username отключён, поэтому задаём email как идентификатор
        user.username = user.email  # временно, чтобы не было ошибок валидации
        if commit:
            user.save()
        return user