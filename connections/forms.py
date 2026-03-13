from django import forms
from .models import MySQLConnection
from environments.models import Environment


class MySQLConnectionForm(forms.ModelForm):
    """MySQL 连接配置表单"""
    environment = forms.ModelChoiceField(
        queryset=Environment.objects.all(),
        required=True,
        empty_label='请选择环境',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = MySQLConnection
        fields = ['name', 'host', 'port', 'username', 'password', 'environment']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入连接名称'
                }
            ),
            'host': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入主机地址'
                }
            ),
            'port': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入端口'
                }
            ),
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入用户名'
                }
            ),
            'password': forms.PasswordInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入密码'
                }
            ),
        }
        labels = {
            'name': '连接名称',
            'host': '主机地址',
            'port': '端口',
            'username': '用户名',
            'password': '密码',
            'environment': '所属环境',
        }