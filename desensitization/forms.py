from django import forms
from .models import MaskingRule


class MaskingRuleForm(forms.ModelForm):
    """脱敏规则表单"""
    class Meta:
        model = MaskingRule
        fields = ['name', 'column_names', 'masking_type', 'masking_params']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'}),
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
            'name': '规则名称',
            'column_names': '列名',
            'masking_type': '脱敏类型',
            'masking_params': '脱敏参数',
        }