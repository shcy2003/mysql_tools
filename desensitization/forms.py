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

    def clean_column_names(self):
        column_names = self.cleaned_data.get('column_names', [])
        # 检查是否有其他规则已经使用了这些列名
        existing_rules = MaskingRule.objects.all()
        if self.instance.pk:  # 编辑时排除当前规则
            existing_rules = existing_rules.exclude(pk=self.instance.pk)

        for rule in existing_rules:
            # 检查列名是否有重叠
            overlapping_columns = set(rule.column_names) & set(column_names)
            if overlapping_columns:
                raise forms.ValidationError(
                    f'字段 {", ".join(overlapping_columns)} 已存在于其他规则中'
                )

        return column_names