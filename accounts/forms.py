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


class UserForm(forms.ModelForm):
    """用户管理表单（创建和编辑用户）"""
    password = forms.CharField(
        label='密码',
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': '请输入密码'
            }
        )
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'is_active')
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入用户名'
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入邮箱地址'
                }
            ),
            'role': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'is_active': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        # 检查是否是编辑模式（instance 存在）
        is_edit = kwargs.get('instance') is not None
        super().__init__(*args, **kwargs)

        if is_edit:
            # 编辑用户时密码可选
            self.fields['password'].required = False
            self.fields['password'].widget.attrs['placeholder'] = '留空则不修改密码'
        else:
            # 创建用户时密码必填
            self.fields['password'].required = True
            self.fields['password'].widget.attrs['placeholder'] = '请输入密码'

        # 确保所有字段都有正确的 class
        for field_name, field in self.fields.items():
            if field_name == 'is_active':
                continue
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' '
            else:
                field.widget.attrs['class'] = ''
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] += 'form-check-input'
            else:
                field.widget.attrs['class'] += 'form-control'