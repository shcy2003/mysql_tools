from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class LoginForm(AuthenticationForm):
    """登录表单"""
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '请输入用户名',
                'autofocus': True
            }
        )
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': '请输入密码'
            }
        )
    )


class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': '请输入邮箱地址'
            }
        )
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入用户名'
                }
            ),
            'password1': forms.PasswordInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入密码'
                }
            ),
            'password2': forms.PasswordInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请再次输入密码'
                }
            ),
        }