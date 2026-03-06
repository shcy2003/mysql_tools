/**
 * SQL查询新界面 - 主逻辑
 */

// 全局状态
let connectionTreeData = [];
let selectedConnectionId = null;
let selectedConnectionName = null;

// 初始化
$(document).ready(function() {
    initConnectionTree();
    initEventHandlers();
    initSQLEditor();
});

// ============================================
// 连接树相关功能
// ============================================

// 初始化连接树
function initConnectionTree() {
    loadConnectionTree();
}

// 加载连接树数据
function loadConnectionTree() {
    const $treeContainer = $('#connectionTree');
    showTreeLoading($treeContainer);

    $.ajax({
        url: '/api/connections/tree/',
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            if (response.code === 0) {
                connectionTreeData = response.data || [];
                renderConnectionTree(connectionTreeData);
            } else {
                showTreeError(response.message || '加载连接树失败');
            }
        },
        error: function(xhr, status, error) {
            console.error('加载连接树失败:', error);
            showTreeError('无法连接到服务器，请检查网络');
        }
    });
}

// 显示树加载中
function showTreeLoading($container) {
    $container.html(`
        <div class="empty-state py-3">
            <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
            <small class="text-muted d-block mt-1">加载连接...</small>
        </div>
    `);
}

// 渲染连接树
function renderConnectionTree(connections) {
    const $treeContainer = $('#connectionTree');

    if (!connections || connections.length === 0) {
        $treeContainer.html(`
            <div class="empty-state py-3">
                <i class="bi bi-inbox text-muted" style="font-size: 2rem;"></i>
                <small class="text-muted d-block mt-1">暂无连接</small>
                <a href="/connections/create/" class="btn btn-sm btn-outline-primary mt-2">
                    <i class="bi bi-plus"></i> 创建连接
                </a>
            </div>
        `);
        return;
    }

    let html = '<ul class="tree-list">';
    connections.forEach(function(conn) {
        html += renderConnectionNode(conn);
    });
    html += '</ul>';

    $treeContainer.html(html);
}

// 渲染连接节点
function renderConnectionNode(conn) {
    const hasChildren = conn.databases && conn.databases.length > 0;
    const expandIcon = hasChildren 
        ? '<i class="bi bi-chevron-right expand-icon"></i>' 
        : '<span class="expand-icon" style="width:12px;display:inline-block;"></span>';

    let html = `<li class="tree-item">`;
    html += `<div class="tree-node connection-node" data-connection-id="${conn.id}" data-type="connection" data-name="${escapeHtml(conn.name)}">`;
    html += `${expandIcon}`;
    html += `<span class="icon"><i class="bi bi-hdd-network"></i></span>`;
    html += `<span class="node-name">${escapeHtml(conn.name)}</span>`;
    html += `</div>`;

    if (hasChildren) {
        html += `<ul class="tree-children database-list">`;
        conn.databases.forEach(function(db) {
            html += renderDatabaseNode(db);
        });
        html += `</ul>`;
    }

    html += `</li>`;
    return html;
}

// 渲染数据库节点
function renderDatabaseNode(db) {
    const hasChildren = db.tables && db.tables.length > 0;
    const expandIcon = hasChildren 
        ? '<i class="bi bi-chevron-right expand-icon"></i>' 
        : '<span class="expand-icon" style="width:12px;display:inline-block;"></span>';

    let html = `<li class="tree-item">`;
    html += `<div class="tree-node database-node" data-database="${escapeHtml(db.name)}" data-type="database">`;
    html += `${expandIcon}`;
    html += `<span class="icon"><i class="bi bi-database"></i></span>`;
    html += `<span class="node-name">${escapeHtml(db.name)}</span>`;
    html += `</div>`;

    if (hasChildren) {
        html += `<ul class="tree-children table-list">`;
        db.tables.forEach(function(table) {
            html += renderTableNode(table, db.name);
        });
        html += `</ul>`;
    }

    html += `</li>`;
    return html;
}

// 渲染表节点
function renderTableNode(table, dbName) {
    let html = `<li class="tree-item">`;
    html += `<div class="tree-node table-node" data-table="${escapeHtml(table)}" data-database="${escapeHtml(dbName)}" data-type="table">`;
    html += `<span class="expand-icon" style="width:12px;display:inline-block;"></span>`;
    html += `<span class="icon"><i class="bi bi-table"></i></span>`;
    html += `<span class="node-name">${escapeHtml(table)}</span>`;
    html += `</div>`;
    html += `</li>`;
    return html;
}

// 显示树错误
function showTreeError(message) {
    $('#connectionTree').html(`
        <div class="alert alert-warning m-2" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${message}
        </div>
    `);
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// CSRF Token
// ============================================
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.match(/csrftoken=([^;]+)/)?.[1]
        || '';
}

// ============================================
// 事件处理
// ============================================

// 初始化事件处理器
function initEventHandlers() {
    // 侧边栏折叠/展开
    $('#treeToggleBtn').on('click', function() {
        const $sidebar = $('#connectionTreeSidebar');
        $sidebar.toggleClass('collapsed');
        $(this).find('i').toggleClass('bi-chevron-left bi-chevron-right');
    });

    // 刷新连接树
    $('#refreshTreeBtn').on('click', function() {
        const $btn = $(this);
        $btn.prop('disabled', true).find('i').addClass('spin');
        loadConnectionTree();
        setTimeout(() => {
            $btn.prop('disabled', false).find('i').removeClass('spin');
        }, 500);
    });

    // 连接树节点点击事件（委托）
    $('#connectionTree').on('click', '.tree-node', function(e) {
        e.stopPropagation();
        const $node = $(this);
        const nodeType = $node.data('type');

        // 切换展开/折叠
        const $children = $node.siblings('.tree-children');
        if ($children.length > 0) {
            $node.toggleClass('expanded');
            $children.toggleClass('expanded');
        }

        // 处理节点选择
        if (nodeType === 'connection') {
            selectedConnectionId = $node.data('connection-id');
            selectedConnectionName = $node.data('name');
            
            // 更新UI选中状态
            $('.tree-node').removeClass('active');
            $node.addClass('active');
            
            // 更新编辑器提示
            updateEditorPlaceholder();
            
            showNotification(`已选择连接: ${selectedConnectionName}`, 'info');
        } else if (nodeType === 'table') {
            const tableName = $node.data('table');
            const dbName = $node.data('database');
            insertTableIntoEditor(tableName, dbName);
        }
    });

    // 执行查询
    $('#executeBtn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('>>> Execute button clicked at', new Date().toISOString());
        console.log('>>> Button type:', this.type);
        console.log('>>> Button form:', this.form);
        executeQuery();
    });

    // 清空
    $('#clearBtn').on('click', function() {
        clearEditor();
    });

    // 保存查询
    $('#saveBtn').on('click', function() {
        saveQuery();
    });

    // SQL编辑器快捷键
    $('#sqlEditor').on('keydown', function(e) {
        // Ctrl+Enter 执行查询
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            executeQuery();
        }
        
        // Tab 键缩进
        if (e.key === 'Tab') {
            e.preventDefault();
            const $textarea = $(this);
            const start = $textarea[0].selectionStart;
            const end = $textarea[0].selectionEnd;
            const value = $textarea.val();
            
            $textarea.val(value.substring(0, start) + '  ' + value.substring(end));
            $textarea[0].selectionStart = $textarea[0].selectionEnd = start + 2;
        }
    });
}

// ============================================
// SQL 编辑器功能
// ============================================

// 初始化 SQL 编辑器
function initSQLEditor() {
    updateEditorPlaceholder();
}

// 更新编辑器占位符
function updateEditorPlaceholder() {
    const $editor = $('#sqlEditor');
    if (selectedConnectionName) {
        $editor.attr('placeholder', `已选择连接: ${selectedConnectionName}\n\n请输入 SQL 查询语句...\n例如：SELECT * FROM users WHERE status = 'active' LIMIT 10`);
    } else {
        $editor.attr('placeholder', `请先从左侧连接树中选择一个连接...\n\n然后输入 SQL 查询语句`);
    }
}

// 插入表名到编辑器
function insertTableIntoEditor(tableName, dbName) {
    const $editor = $('#sqlEditor');
    const currentValue = $editor.val();
    const insertText = dbName ? `\`${dbName}\`.\`${tableName}\`` : `\`${tableName}\``;

    if (currentValue.trim() === '') {
        $editor.val(`SELECT * FROM ${insertText} LIMIT 10`);
    } else {
        // 在光标位置插入
        const cursorPos = $editor.prop('selectionStart');
        const textBefore = currentValue.substring(0, cursorPos);
        const textAfter = currentValue.substring(cursorPos);
        $editor.val(textBefore + insertText + textAfter);
    }

    // 聚焦编辑器
    $editor.focus();
    showNotification(`已插入表名: ${tableName}`, 'success');
}

// ============================================
// 查询执行
// ============================================

// 执行查询
function executeQuery() {
    const sql = $('#sqlEditor').val().trim();

    if (!sql) {
        showNotification('请输入 SQL 查询语句', 'warning');
        $('#sqlEditor').focus();
        return;
    }

    if (!selectedConnectionId) {
        showNotification('请先从左侧连接树中选择一个连接', 'warning');
        return;
    }

    // 验证是否为 SELECT 语句
    const firstWord = sql.split(/\s+/)[0].toLowerCase();
    if (firstWord !== 'select') {
        showNotification('目前仅支持 SELECT 查询', 'warning');
        return;
    }

    // 显示加载状态
    showLoadingOverlay();

    // 发送请求
    $.ajax({
        url: '/api/queries/execute/',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            connection_id: selectedConnectionId,
            sql: sql
        }),
        dataType: 'json',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        },
        success: function(response) {
            hideLoadingOverlay();
            if (response.code === 0) {
                renderResults(response.data);
            } else {
                showError(response.message || '查询失败');
            }
        },
        error: function(xhr, status, error) {
            hideLoadingOverlay();
            console.error('查询请求失败:', error);
            let errorMsg = '请求失败，请检查网络连接';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            }
            showError(errorMsg);
        }
    });
}

// 显示加载遮罩
function showLoadingOverlay() {
    $('#loadingOverlay').show();
}

// 隐藏加载遮罩
function hideLoadingOverlay() {
    $('#loadingOverlay').hide();
}

// ============================================
// 结果渲染
// ============================================

// 渲染查询结果
function renderResults(data) {
    $('#emptyState').hide();
    $('#errorContent').hide();
    $('#resultsContent').show();

    // 更新元信息
    const executionTime = data.execution_time_ms || 0;
    const rowCount = data.row_count || 0;
    const isLimited = data.limited || false;
    const limitText = isLimited ? ' (已限制前10条)' : '';

    $('#resultsMeta').html(`
        <span class="me-3"><i class="bi bi-clock"></i> ${executionTime.toFixed(2)}ms</span>
        <span><i class="bi bi-list-ol"></i> ${rowCount} 条记录${limitText}</span>
    `);

    // 渲染表格
    const columns = data.columns || [];
    const rows = data.rows || [];

    let tableHtml = '<table class="data-table"><thead><tr>';
    columns.forEach(function(col) {
        tableHtml += `<th>${escapeHtml(col)}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';

    if (rows.length === 0) {
        tableHtml += `<tr><td colspan="${columns.length}" class="text-center text-muted py-4">暂无数据</td></tr>`;
    } else {
        rows.forEach(function(row) {
            tableHtml += '<tr>';
            columns.forEach(function(col) {
                const value = row[col];
                const displayValue = value === null || value === undefined 
                    ? '<span class="text-muted fst-italic">NULL</span>' 
                    : escapeHtml(String(value));
                tableHtml += `<td>${displayValue}</td>`;
            });
            tableHtml += '</tr>';
        });
    }

    tableHtml += '</tbody></table>';

    $('#dataTableWrapper').html(tableHtml);
}

// 显示错误
function showError(message) {
    $('#emptyState').hide();
    $('#resultsContent').hide();
    $('#errorContent').show();
    $('#errorMessage').text(message);
}

// ============================================
// 工具函数
// ============================================

// 清空编辑器
function clearEditor() {
    $('#sqlEditor').val('').focus();
    $('#emptyState').show();
    $('#resultsContent').hide();
    $('#errorContent').hide();
}

// 保存查询
function saveQuery() {
    const sql = $('#sqlEditor').val().trim();
    if (!sql) {
        showNotification('没有可保存的查询', 'warning');
        return;
    }

    // 弹出保存对话框
    const name = prompt('请输入查询名称:', '我的查询');
    if (name) {
        // TODO: 实现真正的保存功能，调用后端API
        showNotification(`查询 "${name}" 已保存`, 'success');
    }
}

// 显示通知
function showNotification(message, type) {
    const alertType = type === 'error' ? 'danger' : type;
    const icons = {
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle',
        'danger': 'bi-x-circle',
        'info': 'bi-info-circle'
    };
    const icon = icons[alertType] || icons['info'];

    // 移除已存在的通知
    $('.floating-alert').remove();

    const alertDiv = $(`
        <div class="alert alert-${alertType} alert-dismissible fade show floating-alert" role="alert" style="position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <div class="d-flex align-items-center">
                <i class="bi ${icon} me-2" style="font-size: 1.2rem;"></i>
                <div>${message}</div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);

    $('body').append(alertDiv);

    // 3秒后自动隐藏
    setTimeout(function() {
        alertDiv.fadeOut('slow', function() {
            $(this).remove();
        });
    }, 3000);
}
