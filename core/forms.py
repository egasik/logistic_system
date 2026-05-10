from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Имя", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Фамилия", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    phone = forms.CharField(label="Телефон", max_length=32, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(label="Адрес доставки", max_length=500, required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'address']

class ProfileUpdateForm(forms.ModelForm):
    card_number = forms.CharField(label="Номер карты", max_length=32, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000 0000 0000 0000'}))

    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'card_number']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'})
        }