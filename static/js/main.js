// 页面加载完成后的初始化
$(document).ready(function() {
    // 表单验证
    initializeFormValidation();

    // 初始化工具提示
    initializeTooltips();

    // 初始化数据表格
    initializeDataTables();

    // 初始化搜索功能
    initializeSearch();

    // 初始化分页
    initializePagination();
});

// 表单验证
function initializeFormValidation() {
    // 为所有表单添加验证
    $('form').each(function() {
        const $form = $(this);

        $form.on('submit', function(e) {
            // 简单的必填项验证
            const $requiredFields = $form.find('[required]');
            let isValid = true;

            $requiredFields.each(function() {
                if (!$(this).val().trim()) {
                    isValid = false;
                    showError($(this), '此字段为必填项');
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });

        // 输入框失去焦点时验证
        $form.find(':input').on('blur', function() {
            if ($(this).prop('required') && !$(this).val().trim()) {
                showError($(this), '此字段为必填项');
            } else {
                removeError($(this));
            }
        });
    });
}

// 显示错误信息
function showError(element, message) {
    const $element = $(element);
    $element.addClass('is-invalid');

    // 检查是否已经有错误提示
    let $errorDiv = $element.next('.invalid-feedback');
    if (!$errorDiv.length) {
        $errorDiv = $('<div class="invalid-feedback"></div>').insertAfter($element);
    }
    $errorDiv.text(message);
}

// 移除错误信息
function removeError(element) {
    const $element = $(element);
    $element.removeClass('is-invalid');

    const $errorDiv = $element.next('.invalid-feedback');
    if ($errorDiv.length) {
        $errorDiv.remove();
    }
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化数据表格
function initializeDataTables() {
    // 为所有表格添加响应式样式
    $('.table').addClass('table-responsive');
}

// 初始化搜索功能
function initializeSearch() {
    $('.search-box .btn-search').on('click', function() {
        const $searchInput = $(this).prev('input');
        if ($searchInput.val().trim()) {
            $(this).closest('form').submit();
        }
    });

    $('.search-box input').on('keypress', function(e) {
        if (e.which == 13) {
            $(this).next('.btn-search').click();
        }
    });
}

// 初始化分页
function initializePagination() {
    // 为分页链接添加样式
    $('.pagination a').addClass('page-link');
    $('.pagination span').addClass('page-link');
}

// 通用 AJAX 请求函数
function makeAjaxRequest(url, data, method, successCallback, errorCallback) {
    $.ajax({
        url: url,
        data: data,
        method: method || 'GET',
        dataType: 'json',
        success: function(response) {
            if (successCallback) {
                successCallback(response);
            }
        },
        error: function(xhr, status, error) {
            if (errorCallback) {
                errorCallback(error);
            } else {
                showNotification('请求失败: ' + error, 'error');
            }
        }
    });
}

// 显示通知
function showNotification(message, type) {
    const alertType = type === 'error' ? 'danger' : type;
    const alertDiv = $(`
        <div class="alert alert-${alertType} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);

    // 添加到页面顶部
    $('main').prepend(alertDiv);

    // 3秒后自动隐藏
    setTimeout(function() {
        alertDiv.fadeOut('slow', function() {
            $(this).remove();
        });
    }, 3000);
}

// 显示加载动画
function showLoading(element) {
    const $element = $(element);
    $element.attr('disabled', true);

    // 保存原始内容
    const originalContent = $element.html();
    $element.data('original-content', originalContent);

    $element.html(`
        <span class="loading"></span> 加载中...
    `);
}

// 隐藏加载动画
function hideLoading(element) {
    const $element = $(element);
    $element.attr('disabled', false);

    // 恢复原始内容
    const originalContent = $element.data('original-content');
    if (originalContent) {
        $element.html(originalContent);
    }
}