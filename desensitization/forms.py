from django import forms
from .models import MaskingRule


class MaskingRuleForm(forms.ModelForm):
    """脱敏规则表单"""
    class Meta:
        model = MaskingRule
        fields = ['connection', 'table_name', 'column_name', 'masking_type', 'masking_params']
        widgets = {
            'connection': forms.Select(attrs={'class': 'form-control'}),
            'table_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入表名'
                }
            ),
            'column_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '请输入列名'
                }
            ),
            'masking_type': forms.Select(attrs={'class': 'form-control'}),
            'masking_params': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': '请输入脱敏参数（JSON 格式）'
                }
            ),
        }
        labels = {
            'connection': '连接',
            'table_name': '表名',
            'column_name': '列名',
            'masking_type': '脱敏类型',
            'masking_params': '脱敏参数',
        }