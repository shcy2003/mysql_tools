from django import forms
from .models import MySQLConnection


class MySQLConnectionForm(forms.ModelForm):
    """MySQL 连接配置表单"""
    class Meta:
        model = MySQLConnection
        fields = ['name', 'host', 'port', 'database', 'username', 'password']
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
            'database': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入数据库名称'
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
            'database': '数据库名称',
            'username': '用户名',
            'password': '密码',
        }