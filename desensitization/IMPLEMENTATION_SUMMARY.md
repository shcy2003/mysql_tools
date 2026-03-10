# 脱敏规则字段重复检查功能实现总结

## 功能概述

实现了脱敏规则管理系统中的字段重复检查功能，防止用户添加已存在于其他脱敏规则中的列名，确保数据脱敏规则的一致性和准确性。

## 实现详情

### 1. 后端表单验证 (`desensitization/forms.py`)

在 `MaskingRuleForm` 类中添加了 `clean_column_names` 方法：
- 检查提交的列名列表是否与其他规则的列名有重叠
- 支持编辑时排除当前规则的检查
- 抛出表单验证错误，显示具体的重复字段信息

### 2. 视图层处理 (`desensitization/views.py`)

更新了两个核心视图函数：
- `masking_rule_create_view`：在创建规则时检查字段重复
- `masking_rule_edit_view`：在编辑规则时检查字段重复

同时添加了新的 API 视图函数 `api_check_column_exists`，提供异步检查功能。

### 3. 前端验证 (`templates/desensitization/`)

在 `create.html` 和 `edit.html` 中添加了 JavaScript 验证：
- `checkColumnExists()`：异步检查列名是否已在其他规则中存在
- 在添加列名按钮点击事件中先检查当前规则中是否已存在
- 再通过 API 检查其他规则中是否已存在
- 提供友好的错误提示

### 4. API 接口 (`desensitization/urls.py`)

添加了新的 API 路由：
```python
path('api/check-column/', views.api_check_column_exists, name='api_check_column_exists'),
```

## 验证流程

### 创建规则时

1. 用户在界面添加列名
2. JavaScript 先检查是否已在当前规则中存在
3. 通过 API 检查是否在其他规则中存在
4. 表单提交到后端，再次进行验证
5. 验证失败时显示详细错误信息

### 编辑规则时

1. 与创建规则类似，但 API 会排除当前规则的检查
2. 确保修改时不会与其他规则的列名冲突

## 功能特点

- **双重验证**：前端异步检查 + 后端表单验证
- **友好提示**：具体显示哪个字段已存在于哪个规则中
- **编辑支持**：编辑时排除当前规则的检查逻辑
- **异步检查**：使用 AJAX 实现无刷新验证

## 错误信息示例

- "该列名已存在于当前规则中"
- "该列名已存在于其他脱敏规则中"
- "字段 phone 已存在于其他规则中"

## 文件修改

1. `desensitization/forms.py`：添加表单验证逻辑
2. `desensitization/views.py`：更新视图和添加 API
3. `desensitization/urls.py`：添加路由配置
4. `templates/desensitization/create.html`：添加前端验证
5. `templates/desensitization/edit.html`：添加前端验证