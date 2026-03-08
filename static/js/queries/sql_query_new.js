/**
 * SQL查询新界面 - 主逻辑
 */

// 全局状态
let sqlEditor = null;  // CodeMirror编辑器实例
let currentQueryData = null;
let currentPage = 1;
let pageSize = 50;

// SQL关键词列表
const SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'NULL', 'IS', 'IN', 'LIKE',
    'BETWEEN', 'ORDER', 'BY', 'ASC', 'DESC', 'LIMIT', 'OFFSET', 'GROUP', 'HAVING',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'DISTINCT', 'COUNT',
    'SUM', 'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'SHOW',
    'DATABASES', 'TABLES', 'COLUMNS', 'FROM', 'USE'
];

// SQL函数列表
const SQL_FUNCTIONS = [
    'ABS', 'ACOS', 'ADDDATE', 'ADDTIME', 'ASCII', 'ASIN', 'ATAN', 'AVG',
    'BIT_AND', 'BIT_OR', 'BIT_XOR', 'CEIL', 'CEILING', 'CHAR', 'CHAR_LENGTH',
    'CHARACTER_LENGTH', 'COALESCE', 'CONCAT', 'CONCAT_WS', 'CONV', 'CONVERT',
    'COS', 'COT', 'COUNT', 'CURDATE', 'CURRENT_DATE', 'CURRENT_TIME',
    'CURRENT_TIMESTAMP', 'CURTIME', 'DATE', 'DATEDIFF', 'DATE_ADD', 'DATE_FORMAT',
    'DATE_SUB', 'DAY', 'DAYNAME', 'DAYOFMONTH', 'DAYOFWEEK', 'DAYOFYEAR',
    'DEGREES', 'ELT', 'EXP', 'EXTRACT', 'FIELD', 'FIND_IN_SET', 'FLOOR',
    'FORMAT', 'FROM_DAYS', 'FROM_UNIXTIME', 'GREATEST', 'HEX', 'HOUR',
    'IF', 'IFNULL', 'IN', 'INET_ATON', 'INET_NTOA', 'INSERT', 'INSTR',
    'INTERVAL', 'ISNULL', 'LAST_INSERT_ID', 'LCASE', 'LEAST', 'LEFT', 'LENGTH',
    'LIKE', 'LN', 'LOAD_FILE', 'LOCATE', 'LOG', 'LOG10', 'LOWER', 'LPAD',
    'LTRIM', 'MAKE_SET', 'MAKEDATE', 'MAKETIME', 'MID', 'MINUTE', 'MOD',
    'MONTH', 'MONTHNAME', 'NOW', 'NULLIF', 'OCT', 'OCTET_LENGTH', 'ORD',
    'PERIOD_ADD', 'PERIOD_DIFF', 'PI', 'POW', 'POWER', 'QUARTER', 'QUOTE',
    'RADIANS', 'RAND', 'ROUND', 'RPAD', 'RTRIM', 'SEC_TO_TIME', 'SECOND',
    'SESSION_USER', 'SIGN', 'SIN', 'SLEEP', 'SOUNDEX', 'SPACE', 'SQRT',
    'STD', 'STDDEV', 'STR_TO_DATE', 'STRCMP', 'SUBDATE', 'SUBSTRING',
    'SUBSTRING_INDEX', 'SUM', 'SYSDATE', 'SYSTEM_USER', 'TAN', 'TIME',
    'TIME_FORMAT', 'TIME_TO_SEC', 'TIMEDIFF', 'TIMESTAMP', 'TIMESTAMPADD',
    'TIMESTAMPDIFF', 'TO_DAYS', 'TRIM', 'TRUNCATE', 'UCASE', 'UNHEX',
    'UNIX_TIMESTAMP', 'UPPER', 'USER', 'UTC_DATE', 'UTC_TIME', 'UTC_TIMESTAMP',
    'UUID', 'WEEK', 'WEEKDAY', 'WEEKOFYEAR', 'YEAR', 'YEARWEEK'
];

// 初始化
$(document).ready(function() {
    initEventHandlers();
    initSqlEditor();
    initPageSizeSelector();
    checkSavedQuery();
    initSavedQueriesModal();

    // 监听侧边栏连接状态变化
    window.updateSqlQueryConnection = function(connectionId) {
        console.log('SQL查询页面: 连接已更新为', connectionId);
    };

    window.updateSqlQueryDatabase = function(database) {
        console.log('SQL查询页面: 数据库已更新为', database);
    };

    window.updateSqlQueryEditor = function(sql, autoExecute) {
        console.log('SQL查询页面: 更新SQL编辑器内容');
        if (sqlEditor) {
            sqlEditor.setValue(sql);
            // 默认自动执行查询，但可以通过参数禁用
            if (autoExecute !== false) {
                executeQuery();
            }
        }
    };
});

// 初始化SQL编辑器（CodeMirror）
function initSqlEditor() {
    const textarea = document.getElementById('sqlEditor');

    // 创建CodeMirror编辑器
    sqlEditor = CodeMirror.fromTextArea(textarea, {
        mode: 'text/x-sql',
        theme: 'monokai',
        lineNumbers: true,
        lineWrapping: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: true,
        extraKeys: {
            'Ctrl-Space': 'autocomplete',  // Ctrl+Space 自动提示
            'Ctrl-Enter': executeQuery,   // Ctrl+Enter 执行查询
            'Ctrl-/': 'toggleComment',    // Ctrl+/ 注释
            'Tab': function(cm) {
                if (cm.state.completionActive) {
                    // 如果正在自动完成，按Tab键插入建议
                    CodeMirror.commands.acceptCompletion(cm);
                } else {
                    // 否则，插入缩进
                    cm.replaceSelection('    ', 'end');
                }
            }
        },
        hintOptions: {
            completeSingle: false
        },
        matchBrackets: true,
        autoCloseBrackets: true,
        foldGutter: true,
        gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter']
    });

    // 设置编辑器大小
    function resizeSqlEditor() {
        const editorHeight = 300;
        sqlEditor.setSize('100%', editorHeight);
    }

    // 初始化时设置一次
    setTimeout(function() {
        resizeSqlEditor();
    }, 50);

    // 监听窗口大小变化
    $(window).on('resize', function() {
        resizeSqlEditor();
    });

    // 自定义自动提示
    CodeMirror.registerHelper('hint', 'sql', function(cm) {
        const cursor = cm.getCursor();
        const line = cm.getLine(cursor.line).slice(0, cursor.ch);

        // 获取当前上下文
        const lastWord = getLastWord(line);
        const suggestions = [];

        // 收集建议
        if (lastWord) {
            // 关键词和函数
            const filteredKeywords = SQL_KEYWORDS.filter(word =>
                word.toLowerCase().startsWith(lastWord.toLowerCase())
            );
            suggestions.push(...filteredKeywords.map(word => ({
                text: word,
                type: 'keyword',
                displayText: word,
                className: 'cm-sql-keyword'
            })));

            const filteredFunctions = SQL_FUNCTIONS.filter(word =>
                word.toLowerCase().startsWith(lastWord.toLowerCase())
            );
            suggestions.push(...filteredFunctions.map(word => ({
                text: word,
                type: 'function',
                displayText: word + '()',
                className: 'cm-sql-function'
            })));
        }

        return {
            list: suggestions,
            from: CodeMirror.Pos(cursor.line, cursor.ch - lastWord.length),
            to: CodeMirror.Pos(cursor.line, cursor.ch)
        };
    });
}

// 获取最后一个单词
function getLastWord(text) {
    const match = text.match(/[a-zA-Z_0-9]*$/);
    return match ? match[0] : '';
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// 事件处理
// ============================================

function initEventHandlers() {
    // 执行查询
    $('#executeBtn').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
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

    // 每页显示行数选择
    $('#pageSizeSelect').on('change', function() {
        pageSize = parseInt($(this).val());
        // 如果正在显示查询结果，重新执行查询以应用新的每页显示行数
        if (currentQueryData) {
            executeQuery();
        }
    });
}

// 初始化每页显示行数选择器
function initPageSizeSelector() {
    // 从本地存储加载保存的设置
    const savedPageSize = localStorage.getItem('pageSize');
    if (savedPageSize) {
        pageSize = parseInt(savedPageSize);
        $('#pageSizeSelect').val(pageSize);
    }

    // 保存设置到本地存储
    $('#pageSizeSelect').on('change', function() {
        const selectedSize = parseInt($(this).val());
        localStorage.setItem('pageSize', selectedSize);
    });
}

// ============================================
// SQL 编辑器功能
// ============================================

function clearEditor() {
    if (sqlEditor) {
        sqlEditor.setValue('');
        sqlEditor.focus();
    }
    $('#emptyState').show();
    $('#resultsContent').hide();
    $('#errorContent').hide();
    currentQueryData = null;
    currentPage = 1;
}

function saveQuery() {
    if (!sqlEditor) return;

    const sql = sqlEditor.getValue().trim();
    if (!sql) {
        showNotification('请先输入 SQL 查询语句', 'warning');
        return;
    }

    const name = prompt('请输入查询名称:');
    if (!name) {
        return;
    }

    $.ajax({
        url: '/api/queries/saved/',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            name: name,
            sql: sql,
            connection_id: window.selectedConnectionId,
            database: window.selectedDatabase
        }),
        dataType: 'json',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        },
        success: function(response) {
            if (response.code === 0) {
                showNotification('查询已保存', 'success');
            } else {
                showNotification(response.message || '保存失败', 'error');
            }
        },
        error: function() {
            showNotification('保存失败', 'error');
        }
    });
}

// ============================================
// 查询执行
// ============================================

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.match(/csrftoken=([^;]+)/)?.[1]
        || '';
}

function executeQuery() {
    if (!sqlEditor) return;

    const sql = sqlEditor.getValue().trim();

    if (!sql) {
        showNotification('请输入 SQL 查询语句', 'warning');
        sqlEditor.focus();
        return;
    }

    if (!window.selectedConnectionId) {
        showNotification('请先从左侧侧边栏选择一个数据库连接', 'warning');
        return;
    }

    const firstWord = sql.split(/\s+/)[0].toLowerCase();
    if (firstWord !== 'select' && firstWord !== 'show') {
        showNotification('目前仅支持 SELECT 或 SHOW 查询', 'warning');
        return;
    }

    currentPage = 1;
    currentQueryData = null;
    showLoadingOverlay();

    $.ajax({
        url: '/api/queries/execute/',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            connection_id: window.selectedConnectionId,
            sql: sql,
            database: window.selectedDatabase,
            page: currentPage,
            page_size: pageSize
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
        error: function(xhr) {
            hideLoadingOverlay();
            let errorMsg = '请求失败，请检查网络连接';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            }
            showError(errorMsg);
        }
    });
}

function showLoadingOverlay() {
    $('#loadingOverlay').show();
}

function hideLoadingOverlay() {
    $('#loadingOverlay').hide();
}

function renderResults(data) {
    currentQueryData = data;
    currentPage = data.page || 1;
    $('#emptyState').hide();
    $('#errorContent').hide();
    $('#resultsContent').show();

    // 更新元信息
    const executionTime = data.execution_time_ms || 0;
    const rowCount = data.row_count || 0;
    const totalCount = data.total_count || 0;

    let metaHtml = `
        <span class="me-3"><i class="bi bi-clock"></i> ${executionTime.toFixed(2)}ms</span>
        <span class="me-3"><i class="bi bi-list-ol"></i> 显示 ${rowCount} / ${totalCount} 条记录</span>
    `;

    if (data.total_pages && data.total_pages > 1) {
        metaHtml += renderPagination(data);
    }

    $('#resultsMeta').html(metaHtml);

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

    bindPaginationEvents();
}

function renderPagination(data) {
    const page = data.page || 1;
    const totalPages = data.total_pages || 1;

    let html = '<span class="pagination-container ms-3">';

    if (page > 1) {
        html += `<button class="btn btn-sm btn-outline-primary page-btn" data-page="${page - 1}">
            <i class="bi bi-chevron-left"></i>
        </button>`;
    } else {
        html += `<button class="btn btn-sm btn-outline-secondary page-btn" disabled>
            <i class="bi bi-chevron-left"></i>
        </button>`;
    }

    for (let i = 1; i <= totalPages; i++) {
        if (i === page) {
            html += `<button class="btn btn-sm btn-primary page-btn active" data-page="${i}">${i}</button>`;
        } else {
            html += `<button class="btn btn-sm btn-outline-primary page-btn" data-page="${i}">${i}</button>`;
        }
    }

    if (page < totalPages) {
        html += `<button class="btn btn-sm btn-outline-primary page-btn" data-page="${page + 1}">
            <i class="bi bi-chevron-right"></i>
        </button>`;
    } else {
        html += `<button class="btn btn-sm btn-outline-secondary page-btn" disabled>
            <i class="bi bi-chevron-right"></i>
        </button>`;
    }

    html += '</span>';
    return html;
}

function bindPaginationEvents() {
    $('.page-btn').off('click').on('click', function(e) {
        e.preventDefault();
        const $btn = $(this);
        if ($btn.hasClass('active') || $btn.prop('disabled')) {
            return;
        }
        const page = parseInt($btn.data('page'));
        if (page && page > 0) {
            goToPage(page);
        }
    });
}

function goToPage(page) {
    if (!sqlEditor) return;

    const sql = sqlEditor.getValue().trim();
    if (!sql || !window.selectedConnectionId || !currentQueryData) {
        return;
    }

    showLoadingOverlay();

    $.ajax({
        url: '/api/queries/execute/',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            connection_id: window.selectedConnectionId,
            database: window.selectedDatabase,
            sql: sql,
            page: page,
            page_size: pageSize
        }),
        dataType: 'json',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        },
        success: function(response) {
            hideLoadingOverlay();
            if (response.code === 0) {
                renderResults(response.data);
                $('#resultsContainer')[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                showError(response.message || '查询失败');
            }
        },
        error: function(xhr) {
            hideLoadingOverlay();
            showError(xhr.responseJSON?.message || '请求失败');
        }
    });
}

function showError(message) {
    $('#emptyState').hide();
    $('#resultsContent').hide();
    $('#errorContent').show();
    $('#errorMessage').text(message);
}

// ============================================
// 工具函数
// ============================================

// 检查是否需要使用保存的查询
function checkSavedQuery() {
    try {
        const savedQueryData = localStorage.getItem('useSavedQuery');
        if (savedQueryData) {
            const queryData = JSON.parse(savedQueryData);
            localStorage.removeItem('useSavedQuery');

            // 显示通知
            showNotification(`正在使用查询: ${queryData.name || '未命名查询'}`, 'info');

            // 填充SQL编辑器
            if (queryData.sql) {
                sqlEditor.setValue(queryData.sql);
            }

            // 尝试选择连接和数据库
            if (queryData.connectionId && window.updateSqlQueryConnection) {
                window.updateSqlQueryConnection(parseInt(queryData.connectionId));
            }

            if (queryData.database && window.updateSqlQueryDatabase) {
                window.updateSqlQueryDatabase(queryData.database);
            }
        }
    } catch (e) {
        console.error('Error loading saved query:', e);
    }
}

function showNotification(message, type) {
    const alertType = type === 'error' ? 'danger' : type;
    const icons = {
        'success': 'bi-check-circle',
        'warning': 'bi-exclamation-triangle',
        'danger': 'bi-x-circle',
        'info': 'bi-info-circle'
    };
    const icon = icons[alertType] || icons['info'];

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

    setTimeout(function() {
        alertDiv.fadeOut('slow', function() {
            $(this).remove();
        });
    }, 3000);
}

// 初始化已保存查询模态框
function initSavedQueriesModal() {
    // 模态框显示时加载数据
    $('#savedQueriesModal').on('show.bs.modal', function() {
        loadSavedQueries();
    });

    // 全选/取消全选
    $('#selectAll').on('change', function() {
        const isChecked = $(this).prop('checked');
        $('.query-checkbox').prop('checked', isChecked);
        updateDeleteButton();
    });

    // 单个复选框变化
    $(document).on('change', '.query-checkbox', function() {
        updateSelectAll();
        updateDeleteButton();
    });

    // 使用查询
    $(document).on('click', '.use-query-btn', function() {
        const sql = $(this).data('sql');
        const connectionId = $(this).data('connection-id');
        const database = $(this).data('database');

        // 填充到SQL编辑器
        if (sqlEditor) {
            sqlEditor.setValue(sql);
            showNotification('已加载已保存的查询', 'info');
        }

        // 更新选中的连接和数据库
        if (connectionId) {
            window.selectedConnectionId = connectionId;
        }
        if (database) {
            window.selectedDatabase = database;
        }

        // 关闭模态框
        $('#savedQueriesModal').modal('hide');
    });

    // 删除单个查询
    $(document).on('click', '.delete-query-btn', function() {
        const queryId = $(this).data('query-id');
        if (confirm('确定要删除这个查询吗？')) {
            deleteQueries([queryId]);
        }
    });

    // 批量删除
    $('#deleteSelectedBtn').on('click', function() {
        const queryIds = [];
        $('.query-checkbox:checked').each(function() {
            queryIds.push(parseInt($(this).val()));
        });

        if (queryIds.length === 0) {
            return;
        }

        if (confirm(`确定要删除选中的 ${queryIds.length} 个查询吗？`)) {
            deleteQueries(queryIds);
        }
    });
}

// 加载已保存的查询
function loadSavedQueries() {
    $.ajax({
        url: '/api/queries/saved/',
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            if (response.code === 0) {
                renderSavedQueriesTable(response.data);
            } else {
                showNotification(response.message || '加载失败', 'error');
            }
        },
        error: function() {
            showNotification('加载失败，请重试', 'error');
        }
    });
}

// 渲染已保存查询的表格
function renderSavedQueriesTable(queries) {
    const $tbody = $('#savedQueriesTableBody');
    $tbody.empty();

    if (queries.length === 0) {
        $tbody.append(`
            <tr>
                <td colspan="7" class="text-center py-4 text-muted">
                    <div class="empty-state-icon">
                        <i class="bi bi-inbox"></i>
                    </div>
                    <h5>暂无保存的查询</h5>
                    <p>在 SQL 查询页面保存查询后，它们会显示在这里</p>
                </td>
            </tr>
        `);
        return;
    }

    queries.forEach(function(query) {
        $tbody.append(`
            <tr data-query-id="${query.id}">
                <td>
                    <input type="checkbox" class="query-checkbox form-check-input" value="${query.id}">
                </td>
                <td><strong>${query.name}</strong></td>
                <td>
                    <code class="text-muted small">${query.sql.slice(0, 80)}${query.sql.length > 80 ? '...' : ''}</code>
                </td>
                <td>${query.connection_name || '-'}</td>
                <td>${query.database || '-'}</td>
                <td>${query.updated_at}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary use-query-btn"
                                data-sql="${query.sql}"
                                data-connection-id="${query.connection_id || ''}"
                                data-database="${query.database || ''}">
                            <i class="bi bi-play"></i> 使用
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-query-btn" data-query-id="${query.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `);
    });

    // 重置全选状态
    $('#selectAll').prop('checked', false);
    updateDeleteButton();
}

// 更新全选状态
function updateSelectAll() {
    const allCount = $('.query-checkbox').length;
    const checkedCount = $('.query-checkbox:checked').length;
    $('#selectAll').prop('checked', allCount > 0 && allCount === checkedCount);
}

// 更新删除按钮状态
function updateDeleteButton() {
    const checkedCount = $('.query-checkbox:checked').length;
    $('#deleteSelectedBtn').prop('disabled', checkedCount === 0);
}

// 删除查询
function deleteQueries(queryIds) {
    $.ajax({
        url: '/api/queries/saved/',
        method: 'DELETE',
        contentType: 'application/json',
        data: JSON.stringify({ ids: queryIds }),
        dataType: 'json',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        },
        success: function(response) {
            if (response.code === 0) {
                showNotification(response.message, 'success');
                // 重新加载数据
                loadSavedQueries();
            } else {
                showNotification(response.message || '删除失败', 'error');
            }
        },
        error: function() {
            showNotification('删除失败，请重试', 'error');
        }
    });
}
