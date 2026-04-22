from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile

# =============================================================================
# 🔐 ФОРМА РЕГИСТРАЦИИ
# =============================================================================
class UserRegisterForm(UserCreationForm):
    """Форма регистрации нового пользователя"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'})
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'})
    )

    class Meta:
        model = User
        # Убрали username, если его нет в модели. Оставили только то, что есть.
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован')
        return email


# =============================================================================
# 👤 ФОРМЫ РЕДАКТИРОВАНИЯ ПРОФИЛЯ
# =============================================================================
class UserUpdateForm(forms.ModelForm):
    """Форма обновления данных пользователя (без username, если его нет)"""
    class Meta:
        model = User
        # ВАЖНО: Если у тебя нет поля username в модели User, убери его отсюда!
        # Обычно в кастомных юзерах используют email как логин.
        fields = ['email', 'first_name', 'last_name'] 
        labels = {
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Форма обновления профиля (аватар, телефон, адрес)"""
    class Meta:
        model = Profile
        fields = ['avatar', 'phone', 'address', 'bio']
        labels = {
            'avatar': 'Фото профиля',
            'phone': 'Телефон',
            'address': 'Адрес доставки',
            'bio': 'О себе',
        }
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (___) ___-__-__'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Город, улица, дом, квартира'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Расскажите о себе...'}),
        }