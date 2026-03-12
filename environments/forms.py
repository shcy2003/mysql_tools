from django import forms
from .models import Environment


class EnvironmentForm(forms.ModelForm):
    """环境表单"""
    class Meta:
        model = Environment
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入环境名称'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入描述'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': '环境名称',
            'description': '描述',
            'is_active': '是否启用',
        }
