/**
 * SQL查询新界面 - 主逻辑
 */

// 全局状态
let sqlEditor = null;  // Monaco编辑器实例包装对象
let currentQueryData = null;
let currentPage = 1;
let pageSize = 25;
let currentTableName = null;  // 当前选中的表名
let currentTableRowCount = null;  // 当前选中表的行数
let lastExecutedSql = null;  // 最后执行的SQL
let originalSql = null;  // 原始SQL（不带ORDER BY）

// 排序状态
let sortColumn = null;  // 排序字段
let sortOrder = 'asc';  // 排序方式 asc 或 desc

// 字段列表状态
let fieldsList = [];
let fieldsPanelVisible = false;

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

// 加载系统配置
function loadSystemConfigs() {
    return $.ajax({
        url: '/api/queries/configs/',
        method: 'GET',
        dataType: 'json'
    }).done(function(response) {
        if (response.code === 0 && response.data) {
            const configs = response.data;

            // 从服务器配置设置默认分页大小
            if (configs.sql_query_page_size) {
                pageSize = configs.sql_query_page_size;
                localStorage.setItem('pageSize', pageSize);
                // 更新下拉框选中状态
                $('#pageSizeSelect').val(pageSize);
            }

        }
    }).fail(function(xhr, status, error) {
        // 加载配置失败，使用默认值
    });
}

// 初始化
$(document).ready(function() {
    // 先加载系统配置，再初始化其他组件
    loadSystemConfigs().then(() => {
        initEventHandlers();
        initSqlEditor();
        initPageSizeSelector();
        checkSavedQuery();
        initSavedQueriesModal();
        initFieldsPanel();
        initEditorResizer();
    });

    // 监听侧边栏连接状态变化
    window.updateSqlQueryConnection = function(connectionId) {
        // 当连接改变时，清空表和字段缓存
        window.currentTables = [];
        window.currentTableColumns = {};
        // 只有在已选择数据库时才加载表列表
        if (window.selectedDatabase) {
            loadTablesForCompletion(connectionId);
        }
    };

    window.updateSqlQueryDatabase = function(database) {
        // 当数据库改变时，加载表列表和字段信息
        loadTablesForCompletion(window.selectedConnectionId);
        loadColumnsForCompletion(window.selectedConnectionId, database);
    };

    window.updateSqlQueryEditor = function(sql, autoExecute) {
        if (sqlEditor) {
            sqlEditor.setValue(sql);
            // 默认自动执行查询，但可以通过参数禁用
            if (autoExecute !== false) {
                executeQuery();
            }
        }
    };
});

// Monaco Editor 实例和语言服务
let monacoEditor = null;
let monaco = null;

// 加载 Monaco Editor
function initSqlEditor() {
    // 如果已加载则直接返回
    if (window.monacoInited) {
        console.log('Monaco already initialized');
        return;
    }

    // 使用本地 @monaco-editor/loader
    if (window.MonacoEditor && window.MonacoEditor.loader) {
        window.MonacoEditor.loader.config({
            paths: { vs: '/static/js/monaco/vs' }
        });
        window.MonacoEditor.loader.init().then(function(monacoInstance) {
            monaco = monacoInstance;
            window.monacoInited = true;
            createMonacoEditor();
        });
    } else {
        // 备用方案：直接加载本地loader
        var script = document.createElement('script');
        script.src = '/static/js/monaco/vs/loader.js';
        script.charset = 'utf-8';
        script.onload = function() {
            require.config({
                paths: { vs: '/static/js/monaco/vs' }
            });
            require(['vs/editor/editor.main'], function() {
                monaco = window.monaco;
                window.monacoInited = true;
                createMonacoEditor();
            });
        };
        script.onerror = function(e) {
            console.error('Failed to load Monaco:', e);
        };
        document.head.appendChild(script);
    }
}

function createMonacoEditor() {
    // 注册 SQL 语言（使用 Monaco 内置的 SQL 支持）
    monaco.languages.register({ id: 'sql' });

    // 定义主题
    monaco.editor.defineTheme('sql-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [],
        colors: {
            'editor.background': '#272822',
        }
    });

    // 注册自定义 SQL 自动补全提供者
    monaco.languages.registerCompletionItemProvider('sql', {
        triggerCharacters: [' ', '.', ','],
        provideCompletionItems: function(model, position) {
            return provideSqlCompletionItems(model, position);
        }
    });

    // 创建编辑器
    const editorContainer = document.getElementById('monacoEditor');
    if (!editorContainer) {
        console.error('Editor container not found');
        return;
    }

    monacoEditor = monaco.editor.create(editorContainer, {
        value: '',
        language: 'sql',
        theme: 'sql-dark',
        minimap: { enabled: false },
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        fontSize: 14,
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        tabSize: 4,
        insertSpaces: true,
        wordWrap: 'on',
        contextmenu: true,
        suggestOnTriggerCharacters: true,
        quickSuggestions: true,
        acceptSuggestionOnEnter: 'on',
        formatOnPaste: true,
        formatOnType: true,
        autoClosingBrackets: 'always',
        autoClosingQuotes: 'always',
        autoIndent: 'full',
        renderLineHighlight: 'line',
        scrollbar: {
            verticalScrollbarSize: 10,
            horizontalScrollbarSize: 10
        }
    });

    // 暴露给全局
    sqlEditor = {
        setValue: function(value) {
            monacoEditor.setValue(value);
        },
        getValue: function() {
            return monacoEditor.getValue();
        },
        focus: function() {
            monacoEditor.focus();
        },
        setCursor: function(pos) {
            // Monaco 使用 lineNumber 和 column
            monacoEditor.setPosition({ lineNumber: pos.line || 1, column: pos.ch || 1 });
        },
        getCursor: function() {
            var pos = monacoEditor.getPosition();
            return { line: pos.lineNumber, ch: pos.column };
        },
        replaceRange: function(text, start, end) {
            var startPos = start.line ? { lineNumber: start.line, column: start.ch || 1 } : { lineNumber: 1, column: 1 };
            var endPos = end ? { lineNumber: end.line, column: end.ch || 1 } : startPos;
            var range = new monaco.Range(startPos.lineNumber, startPos.column, endPos.lineNumber, endPos.column);
            monacoEditor.executeEdits('', [{ range: range, text: text }]);
        },
        refresh: function() {
            monacoEditor.layout();
        }
    };

    // 添加键盘快捷键
    monacoEditor.addAction({
        id: 'execute-query',
        label: '执行查询',
        keybindings: [
            monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter
        ],
        run: function() {
            executeQuery();
        }
    });

    // 监听编辑器内容变化
    monacoEditor.onDidChangeModelContent(function() {
        // 可以在这里添加自动保存等功能
    });

    console.log('Monaco Editor initialized');
}

// SQL 自动补全提供者
function provideSqlCompletionItems(model, position) {
    const suggestions = [];
    const textUntilPosition = model.getValueInRange({
        startLineNumber: position.lineNumber,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column
    });

    // 获取当前单词
    const lastWordMatch = textUntilPosition.match(/[a-zA-Z_0-9]*$/);
    const lastWord = lastWordMatch ? lastWordMatch[0] : '';

    // 检测是否在 FROM 后面（需要表名补全）
    const isAfterFrom = /from\s+$/i.test(textUntilPosition.replace(lastWord, ''));
    // 检测是否在表名后面（需要字段补全）
    const isAfterTable = /\w+\.$/.test(textUntilPosition.replace(lastWord, ''));
    // 检测是否在 JOIN 后面
    const isAfterJoin = /join\s+$/i.test(textUntilPosition.replace(lastWord, ''));

    // 添加 SQL 关键词
    if (!isAfterFrom && !isAfterTable && !isAfterJoin) {
        SQL_KEYWORDS.forEach(function(keyword) {
            if (!lastWord || keyword.toLowerCase().startsWith(lastWord.toLowerCase())) {
                suggestions.push({
                    label: keyword,
                    kind: monaco.languages.CompletionItemKind.Keyword,
                    insertText: keyword,
                    detail: '关键词'
                });
            }
        });

        // 添加 SQL 函数
        SQL_FUNCTIONS.forEach(function(func) {
            if (!lastWord || func.toLowerCase().startsWith(lastWord.toLowerCase())) {
                suggestions.push({
                    label: func,
                    kind: monaco.languages.CompletionItemKind.Function,
                    insertText: func + '()',
                    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                    detail: '函数'
                });
            }
        });
    }

    // 添加表名补全（如果在 FROM 后面）
    if (isAfterFrom && window.currentTables) {
        window.currentTables.forEach(function(table) {
            suggestions.push({
                label: table,
                kind: monaco.languages.CompletionItemKind.Class,
                insertText: table,
                detail: '表'
            });
        });
    }

    // 添加字段补全（如果在表名.后面）
    if (isAfterTable && window.currentTableColumns) {
        const tableName = textUntilPosition.match(/\.(\w*)$/);
        if (tableName && window.currentTableColumns[tableName[1]]) {
            window.currentTableColumns[tableName[1]].forEach(function(col) {
                suggestions.push({
                    label: col.name,
                    kind: monaco.languages.CompletionItemKind.Field,
                    insertText: col.name,
                    detail: col.type || '字段'
                });
            });
        }
    }

    // 添加 JOIN 表名补全
    if (isAfterJoin && window.currentTables) {
        window.currentTables.forEach(function(table) {
            suggestions.push({
                label: table,
                kind: monaco.languages.CompletionItemKind.Class,
                insertText: table,
                detail: '表 (JOIN)'
            });
        });
    }

    return { suggestions: suggestions };
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

// 检测主键列
function detectPrimaryKey(columns) {
    const primaryKeyNames = ['id', 'pk', 'key', 'primary', 'no', 'code', 'sn', 'uuid'];
    for (const col of columns) {
        const colLower = col.toLowerCase();
        for (const pk of primaryKeyNames) {
            if (colLower === pk || colLower.endsWith('_' + pk)) {
                return col;
            }
        }
    }
    return null;
}

// 排序点击事件处理 - 通过修改SQL并重新执行来实现服务器端排序
function handleSortClick(column) {
    if (!lastExecutedSql) return;

    // 检测主键列
    const primaryKey = detectPrimaryKey(currentQueryData.columns || []);
    if (!primaryKey) {
        showNotification('未找到主键列，无法排序', 'warning');
        return;
    }

    // 切换排序方向
    if (sortColumn === column) {
        sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortOrder = 'desc';
    }

    // 修改SQL添加ORDER BY，使用原始SQL
    let sql = (originalSql || lastExecutedSql).trim();

    // 移除末尾的分号
    sql = sql.replace(/;$/, '');

    // 移除现有的ORDER BY子句（更全面的正则，支持反引号和点号）
    sql = sql.replace(/ORDER\s+BY\s+`?[\w.`\[\]]+`?(\s+(ASC|DESC))?/gi, '');

    // 移除末尾的LIMIT（如果有的话，保留LIMIT但放到ORDER BY后面）
    let limitClause = '';
    const limitMatch = sql.match(/LIMIT\s+\d+/i);
    if (limitMatch) {
        sql = sql.replace(limitMatch[0], '');
        limitClause = ' ' + limitMatch[0];
    }

    // 清理多余的空白
    sql = sql.trim();

    // 添加ORDER BY子句
    const orderByClause = ` ORDER BY \`${column}\` ${sortOrder.toUpperCase()}${limitClause}`;

    // 重新设置SQL并执行，传入true表示这是排序查询
    sqlEditor.setValue(sql + orderByClause);
    executeQuery(true);
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

    // 保存查询
    $('#saveBtn').on('click', function() {
        saveQuery();
    });

    // 格式化SQL
    $('#formatBtn').on('click', function() {
        formatSql();
    });

    // 导出Excel
    $('#exportBtn').on('click', function() {
        exportQueryResult();
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

// 格式化SQL
function formatSql() {
    if (!sqlEditor) {
        return;
    }

    const sql = sqlEditor.getValue().trim();
    if (!sql) {
        showNotification('请先输入SQL查询语句', 'warning');
        return;
    }

    try {
        // 使用 sql-formatter 库格式化SQL (兼容旧版本API)
        let formattedSql;
        if (typeof sqlFormatter !== 'undefined' && sqlFormatter.format) {
            try {
                // 尝试新版本API
                formattedSql = sqlFormatter.format(sql, {
                    indent: '    ',
                    uppercase: false
                });
            } catch (e) {
                // 回退到简单格式化
                formattedSql = simpleSqlFormat(sql);
            }
        } else {
            // 使用简单格式化作为备用方案
            formattedSql = simpleSqlFormat(sql);
        }

        sqlEditor.setValue(formattedSql);
        showNotification('SQL格式化成功', 'success');
    } catch (error) {
        console.error('SQL格式化错误:', error);
        // 即使出错也尝试简单格式化
        try {
            const formattedSql = simpleSqlFormat(sql);
            sqlEditor.setValue(formattedSql);
            showNotification('SQL格式化成功', 'success');
        } catch (e) {
            showNotification('SQL格式化失败，请检查SQL语法是否正确', 'error');
        }
    }
}

// 简单SQL格式化函数（作为备用方案）
function simpleSqlFormat(sql) {
    if (!sql) return sql;

    let formatted = sql;

    // 简单的关键词大写
    const keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC', 'LIMIT', 'OFFSET', 'VALUES', 'SET', 'TABLE', 'INTO', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'INDEX', 'DATABASE', 'USE', 'SHOW', 'DESCRIBE', 'EXPLAIN'];

    keywords.forEach(keyword => {
        const regex = new RegExp('\\b' + keyword + '\\b', 'gi');
        formatted = formatted.replace(regex, keyword);
    });

    // 在关键关键字前换行
    const breakKeywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET'];
    breakKeywords.forEach(keyword => {
        const regex = new RegExp('\\b(' + keyword + ')\\b', 'gi');
        formatted = formatted.replace(regex, '\n$1');
    });

    // 移除多余的空行
    formatted = formatted.replace(/\n\s*\n/g, '\n');

    // 简单缩进
    const lines = formatted.split('\n');
    let indentLevel = 0;
    const indented = lines.map((line, index) => {
        line = line.trim();
        if (!line) return '';

        // 减少缩进的关键字
        if (/^(FROM|WHERE|AND|OR|GROUP|ORDER|HAVING|LIMIT|OFFSET)\b/i.test(line) && indentLevel > 0) {
            indentLevel--;
        }

        const indentedLine = '    '.repeat(indentLevel) + line;

        // 增加缩进的关键字
        if (/^(SELECT)\b/i.test(line)) {
            indentLevel++;
        }

        return indentedLine;
    });

    return indented.join('\n').trim();
}

// 初始化每页显示行数选择器
function initPageSizeSelector() {
    // 从本地存储加载保存的设置
    const savedPageSize = localStorage.getItem('pageSize');
    if (savedPageSize) {
        pageSize = parseInt(savedPageSize);
        $('#pageSizeSelect').val(pageSize);
    }

    // 导出到 window 对象供其他脚本使用
    window.pageSize = pageSize;

    // 保存设置到本地存储
    $('#pageSizeSelect').on('change', function() {
        const selectedSize = parseInt($(this).val());
        localStorage.setItem('pageSize', selectedSize);
        pageSize = selectedSize;
        window.pageSize = selectedSize;
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

function executeQuery(isSortQuery = false) {
    if (!sqlEditor) return;

    // 如果不是排序查询，则重置排序状态
    if (!isSortQuery) {
        sortColumn = null;
        sortOrder = 'asc';
    }

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
    // 保存原始SQL（不含ORDER BY），去掉末尾分号
    const cleanSql = sql.replace(/;$/, '').trim();
    if (!cleanSql.includes('ORDER BY')) {
        originalSql = cleanSql;
    }
    lastExecutedSql = sql;  // 保存最后执行的SQL
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

// 导出查询结果为Excel
function exportQueryResult() {
    if (!lastExecutedSql || !window.selectedConnectionId) {
        showNotification('请先执行查询', 'warning');
        return;
    }

    showLoadingOverlay();

    $.ajax({
        url: '/api/queries/export_excel/',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            connection_id: window.selectedConnectionId,
            sql: lastExecutedSql,
            database: window.selectedDatabase
        }),
        xhrFields: {
            responseType: 'blob'
        },
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        },
        success: function(blob, status, xhr) {
            hideLoadingOverlay();

            // 创建下载链接
            const filename = xhr.getResponseHeader('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'query_result.xlsx';
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showNotification('导出成功', 'success');
        },
        error: function(xhr) {
            hideLoadingOverlay();
            const errorMsg = xhr.responseJSON?.message || '导出失败';
            showNotification(errorMsg, 'error');
        }
    });
}

// 获取表的行数
function getTableRowCount(tableName) {
    if (!window.selectedConnectionId || !window.selectedDatabase) {
        return;
    }

    $.ajax({
        url: '/api/queries/table_row_count/',
        method: 'GET',
        data: {
            connection_id: window.selectedConnectionId,
            table: tableName,
            database: window.selectedDatabase
        },
        dataType: 'json',
        success: function(response) {
            if (response.code === 0) {
                const rowCount = response.data.row_count;
                currentTableRowCount = rowCount;
                $('#tableRowCount').text(`表行数: ${rowCount.toLocaleString()}`).show();
            }
        },
        error: function() {
            // 忽略错误
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

    // 检测主键列（id, pk, key 等）
    const primaryKeyColumn = detectPrimaryKey(columns);

    let tableHtml = '<table class="data-table"><thead><tr>';
    tableHtml += '<th style="width: 40px;"></th>'; // 操作列
    columns.forEach(function(col) {
        if (col === primaryKeyColumn) {
            const sortIcon = sortColumn === col
                ? (sortOrder === 'asc' ? 'bi-caret-up-fill' : 'bi-caret-down-fill')
                : 'bi-caret-up';
            const activeClass = sortColumn === col ? 'text-primary' : '';
            tableHtml += `<th class="sortable-header ${activeClass}" data-column="${escapeHtml(col)}">
                ${escapeHtml(col)}
                <i class="bi ${sortIcon} sort-icon"></i>
            </th>`;
        } else {
            tableHtml += `<th>${escapeHtml(col)}</th>`;
        }
    });
    tableHtml += '</tr></thead><tbody>';

    if (rows.length === 0) {
        tableHtml += `<tr><td colspan="${columns.length + 1}" class="text-center text-muted py-4">暂无数据</td></tr>`;
    } else {
        rows.forEach(function(row, index) {
            tableHtml += '<tr>';
            tableHtml += `<td><button type="button" class="btn btn-sm btn-outline-secondary btn-view-row" data-index="${index}" title="查看详情"><i class="bi bi-card-text"></i></button></td>`;
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

    // 绑定查看详情按钮事件
    $('.btn-view-row').on('click', function() {
        const index = $(this).data('index');
        const rowData = currentQueryData.rows[index];
        showRowDetailModal(rowData);
    });

    // 绑定排序点击事件
    $('.sortable-header').on('click', function() {
        const column = $(this).data('column');
        handleSortClick(column);
    });

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

// 显示行详情模态框（类似 MySQL 的 \G 格式）
function showRowDetailModal(rowData) {
    const columns = currentQueryData ? currentQueryData.columns : Object.keys(rowData);

    let html = '<div class="row-detail-list">';
    columns.forEach(function(col) {
        const value = rowData[col];
        const displayValue = value === null || value === undefined
            ? '<span class="text-muted fst-italic">NULL</span>'
            : escapeHtml(String(value));
        html += `
            <div class="row-detail-item">
                <div class="row-detail-key">${escapeHtml(col)}</div>
                <div class="row-detail-value">${displayValue}</div>
            </div>
        `;
    });
    html += '</div>';

    // 创建或更新模态框
    let modal = $('#rowDetailModal');
    if (modal.length === 0) {
        const modalHtml = `
            <div class="modal fade" id="rowDetailModal" tabindex="-1" role="dialog" aria-labelledby="rowDetailModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl modal-dialog-scrollable" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="rowDetailModalLabel">
                                <i class="bi bi-card-text"></i> 行详情
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="rowDetailContent" style="max-height: 70vh;"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('body').append(modalHtml);
        modal = $('#rowDetailModal');
    }

    $('#rowDetailContent').html(html);
    const bsModal = new bootstrap.Modal(modal[0]);
    bsModal.show();
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

    // 搜索功能
    $(document).on('keyup', '#searchSavedQueries', function() {
        const searchText = $(this).val().toLowerCase().trim();
        searchAndHighlightSavedQueries(searchText);
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

    // 编辑查询
    $(document).on('click', '.edit-query-btn', function() {
        const queryId = $(this).data('query-id');
        const queryName = $(this).data('name');
        const querySql = $(this).data('sql');

        // 填充到编辑模态框
        $('#editQueryId').val(queryId);
        $('#editQueryName').val(queryName);
        $('#editQuerySql').val(querySql);

        // 显示编辑模态框
        const editModal = new bootstrap.Modal(document.getElementById('editSavedQueryModal'));
        editModal.show();
    });

    // 保存编辑的查询
    $('#saveEditedQueryBtn').on('click', function() {
        saveEditedQuery();
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

// 搜索并高亮已保存的查询
function searchAndHighlightSavedQueries(searchText) {
    $('#savedQueriesTableBody tr').each(function() {
        const $row = $(this);
        const queryName = $row.find('td:eq(1)').text().toLowerCase();
        const querySql = $row.find('td:eq(2) code').text().toLowerCase();

        if (!searchText) {
            // 无搜索条件，显示所有行并移除高亮
            $row.show();
            $row.find('td:eq(1)').html($row.find('td:eq(1)').text());
            $row.find('td:eq(2) code').html($row.find('td:eq(2) code').text());
            return;
        }

        // 检查是否匹配
        const matches = queryName.includes(searchText) || querySql.includes(searchText);

        if (matches) {
            $row.show();
            // 高亮匹配的关键字
            highlightText($row.find('td:eq(1)'), searchText);
            highlightText($row.find('td:eq(2) code'), searchText);
        } else {
            $row.hide();
        }
    });
}

// 高亮文本
function highlightText(element, searchText) {
    if (!searchText) {
        return;
    }

    const text = element.text();
    const regex = new RegExp(`(${searchText})`, 'gi');
    const highlighted = text.replace(regex, '<mark style="background: #ffc107; padding: 0 2px; border-radius: 2px;">$1</mark>');
    element.html(highlighted);
}

// 保存编辑后的查询
function saveEditedQuery() {
    const queryId = $('#editQueryId').val();
    const queryName = $('#editQueryName').val().trim();
    const querySql = $('#editQuerySql').val().trim();

    if (!queryName || !querySql) {
        showNotification('查询名称和SQL都不能为空', 'warning');
        return;
    }

    $.ajax({
        url: '/api/queries/saved/',
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify({
            id: queryId,
            name: queryName,
            sql: querySql
        }),
        dataType: 'json',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
        },
        success: function(response) {
            if (response.code === 0) {
                showNotification('查询已成功更新', 'success');
                // 关闭模态框并重新加载数据
                $('#editSavedQueryModal').modal('hide');
                loadSavedQueries();
            } else {
                showNotification(response.message || '更新失败', 'error');
            }
        },
        error: function(xhr) {
            showNotification(xhr.responseJSON?.message || '请求失败', 'error');
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

    // 保存原始查询数据用于搜索
    window.savedQueriesData = queries;

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
        // 对特殊字符进行转义，避免 HTML 属性解析问题
        const escapedName = escapeHtml(query.name);
        const escapedSql = escapeHtml(query.sql);
        const escapedSqlPreview = escapeHtml(query.sql.slice(0, 80) + (query.sql.length > 80 ? '...' : ''));

        $tbody.append(`
            <tr data-query-id="${query.id}">
                <td>
                    <input type="checkbox" class="query-checkbox form-check-input" value="${query.id}">
                </td>
                <td data-query-name="${escapedName}"><strong>${escapedName}</strong></td>
                <td data-query-sql="${escapedSql}">
                    <code class="text-muted small">${escapedSqlPreview}</code>
                </td>
                <td>${query.connection_name || '-'}</td>
                <td>${query.database || '-'}</td>
                <td>${query.updated_at}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary use-query-btn"
                                data-sql="${escapedSql}"
                                data-connection-id="${query.connection_id || ''}"
                                data-database="${query.database || ''}">
                            <i class="bi bi-play"></i> 使用
                        </button>
                        <button type="button" class="btn btn-outline-secondary edit-query-btn"
                                data-query-id="${query.id}"
                                data-name="${escapedName}"
                                data-sql="${escapedSql}">
                            <i class="bi bi-pencil"></i> 编辑
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-query-btn" data-query-id="${query.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `);
    });

    // 重置全选状态和搜索框
    $('#selectAll').prop('checked', false);
    $('#searchSavedQueries').val('');
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

// 初始化字段列表面板
function initFieldsPanel() {
    // 字段列表面板关闭按钮
    $('#closeFieldsPanel').on('click', function() {
        hideFieldsPanel();
    });

    // 暴露字段列表加载函数给外部调用
    window.loadFieldsPanel = showFieldsPanel;
    window.loadFieldsList = loadFieldsList;
}

// 初始化编辑器高度调整
function initEditorResizer() {
    const resizer = document.getElementById('editorResizer');
    const editorSection = document.getElementById('sqlEditorSection');
    const resultsSection = document.getElementById('resultsSection');
    const container = document.getElementById('mainEditorCol');

    if (!resizer || !editorSection || !resultsSection) return;

    let isResizing = false;
    let startY = 0;
    let startEditorHeight = 0;

    // 加载保存的高度，如果高度太小则使用默认值300px（约12行）
    const savedHeight = localStorage.getItem('sqlEditorHeight');
    const minHeight = 450; // 默认12行高度
    if (savedHeight) {
        const height = parseInt(savedHeight);
        if (height >= minHeight && container.offsetHeight > height + 100) {
            editorSection.style.height = height + 'px';
            editorSection.style.flex = 'none';
        } else {
            // 高度太小，使用默认高度
            editorSection.style.height = minHeight + 'px';
            editorSection.style.flex = 'none';
        }
    } else {
        // 没有保存的高度，使用默认高度
        editorSection.style.height = minHeight + 'px';
        editorSection.style.flex = 'none';
    }

    resizer.addEventListener('mousedown', function(e) {
        isResizing = true;
        startY = e.clientY;
        startEditorHeight = editorSection.offsetHeight;
        resizer.classList.add('resizing');
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;

        // 鼠标向下移动时编辑器变高，向上移动时变矮
        const diff = e.clientY - startY;
        let newHeight = startEditorHeight + diff;
        const containerHeight = container.offsetHeight;

        // 限制最小和最大高度
        newHeight = Math.max(80, Math.min(newHeight, containerHeight - 100));

        editorSection.style.height = newHeight + 'px';
        editorSection.style.flex = 'none';

        // 更新 Monaco 编辑器大小
        if (sqlEditor && sqlEditor.refresh) {
            sqlEditor.refresh();
        }
    });

    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';

            // 保存高度到 localStorage
            localStorage.setItem('sqlEditorHeight', editorSection.offsetHeight);

            // 刷新 Monaco
            if (sqlEditor && sqlEditor.refresh) {
                sqlEditor.refresh();
            }
        }
    });
}

// 显示字段列表面板
function showFieldsPanel() {
    const panel = $('#fieldsPanel');
    const panelCol = $('#fieldsPanelCol');
    const mainEditorCol = $('#mainEditorCol');
    const container = $('#sqlQueryContainer');

    panelCol.show();
    panel.show();

    // 获取容器宽度，设置主编辑区域固定宽度
    const containerWidth = container.width();
    mainEditorCol.css('width', (containerWidth - 260) + 'px');

    fieldsPanelVisible = true;
}

// 隐藏字段列表面板
function hideFieldsPanel() {
    const panel = $('#fieldsPanel');
    const panelCol = $('#fieldsPanelCol');
    const mainEditorCol = $('#mainEditorCol');
    panel.hide();
    panelCol.hide();
    // 恢复主编辑区域宽度为 auto
    mainEditorCol.css('width', 'auto');
    fieldsPanelVisible = false;
}

// 切换字段列表面板的显示/隐藏
function toggleFieldsPanel() {
    const panel = $('#fieldsPanel');

    if (fieldsPanelVisible) {
        panel.hide();
        fieldsPanelVisible = false;
    } else {
        panel.show();
        fieldsPanelVisible = true;
    }
}

// 加载字段列表
function loadFieldsList(tableName) {
    if (!window.selectedConnectionId || !window.selectedDatabase) {
        showNotification('请先选择数据库连接和数据库', 'warning');
        return;
    }

    currentTableName = tableName;
    $('#currentTableName').text(tableName);

    // 获取表行数并显示
    getTableRowCount(tableName);

    // 如果面板隐藏，自动打开
    if (!fieldsPanelVisible) {
        showFieldsPanel();
    }

    // 显示加载状态
    $('#fieldsListContainer').html(`
        <div class="fields-empty">
            <div class="spinner-border spinner-border-sm text-primary"></div>
            <p class="mt-2">加载字段中...</p>
        </div>
    `);

    // 调用API获取表结构
    $.get('/api/queries/table_structure/', {
        connection_id: window.selectedConnectionId,
        table: tableName,
        database: window.selectedDatabase
    }, function(response) {
        if (response.code === 0) {
            const columns = response.data.columns || response.data;
            fieldsList = columns;
            renderFieldsList(columns, tableName);
        } else {
            showNotification(response.message || '获取字段列表失败', 'error');
            $('#fieldsListContainer').html(`
                <div class="fields-empty">
                    <div class="icon"><i class="bi bi-exclamation-triangle"></i></div>
                    <p>加载字段失败</p>
                </div>
            `);
        }
    }).fail(function() {
        showNotification('获取字段列表失败，请重试', 'error');
        $('#fieldsListContainer').html(`
            <div class="fields-empty">
                <div class="icon"><i class="bi bi-exclamation-triangle"></i></div>
                <p>加载字段失败</p>
            </div>
        `);
    });
}

// 渲染字段列表
function renderFieldsList(columns, tableName) {
    const container = $('#fieldsListContainer');

    if (!columns || columns.length === 0) {
        container.html(`
            <div class="fields-empty">
                <div class="icon"><i class="bi bi-database"></i></div>
                <p>该表没有字段</p>
            </div>
        `);
        return;
    }

    let html = '<ul class="fields-list">';

    columns.forEach(function(col, index) {
        const fieldName = col.Field;
        const dataType = col.Type;

        html += `
            <li class="field-item"
                data-field-name="${fieldName}"
                data-table-name="${tableName}"
                title="双击插入字段：${fieldName}">
                <span class="field-name">${fieldName}</span>
                <span class="field-type text-muted small">${dataType}</span>
            </li>
        `;
    });

    html += '</ul>';
    container.html(html);

    // 绑定双击事件
    $('.field-item').on('dblclick', function() {
        const fieldName = $(this).data('field-name');
        const tableName = $(this).data('table-name');
        insertFieldAtCursor(fieldName, tableName);

        // 添加高亮效果
        $(this).addClass('highlight');
        setTimeout(() => $(this).removeClass('highlight'), 600);
    });
}

// 在光标位置插入字段
function insertFieldAtCursor(fieldName, tableName) {
    if (!sqlEditor) {
        return;
    }

    // 格式化为用反引号包裹的字段名
    const formattedField = '`' + fieldName + '`';

    // 在光标位置插入
    const cursor = sqlEditor.getCursor();
    sqlEditor.replaceRange(formattedField, cursor);

    // 将光标移到插入位置之后
    sqlEditor.focus();
    sqlEditor.setCursor({
        line: cursor.line,
        ch: cursor.ch + formattedField.length
    });

    showNotification(`已插入字段：${fieldName}`, 'success');
}

// ============================================
// Monaco Editor 语法检查（使用内置功能）
// ============================================
// Monaco Editor 内置基本的 SQL 语法高亮
// 高级语法检查功能可以后续通过 monaco-sql-languages 扩展
// ============================================

// 用于自动补全的表和字段数据
window.currentTables = [];
window.currentTableColumns = {};

// 加载表列表用于自动补全
function loadTablesForCompletion(connectionId) {
    if (!connectionId) {
        window.currentTables = [];
        return;
    }

    // 需要先选择数据库才能获取表列表
    if (!window.selectedDatabase) {
        window.currentTables = [];
        return;
    }

    $.ajax({
        url: '/api/connections/' + connectionId + '/tables/',
        method: 'GET',
        data: { database: window.selectedDatabase },
        dataType: 'json',
        success: function(response) {
            if (response.code === 0 && response.data) {
                window.currentTables = response.data;
            }
        },
        error: function() {
            window.currentTables = [];
        }
    });
}

// 加载字段列表用于自动补全
function loadColumnsForCompletion(connectionId, database) {
    if (!connectionId || !database) {
        window.currentTableColumns = {};
        return;
    }

    $.ajax({
        url: '/api/connections/' + connectionId + '/tables/',
        method: 'GET',
        data: { database: database },
        dataType: 'json',
        success: function(response) {
            if (response.code === 0 && response.data) {
                // 整理成表名 -> 字段列表的格式
                const columnsMap = {};
                response.data.forEach(function(tableName) {
                    // 为每个表获取字段信息
                    loadTableColumns(connectionId, database, tableName, columnsMap);
                });
            }
        },
        error: function() {
            window.currentTableColumns = {};
        }
    });
}

// 加载单个表的字段
function loadTableColumns(connectionId, database, tableName, columnsMap) {
    $.ajax({
        url: '/api/connections/' + connectionId + '/columns/',
        method: 'GET',
        data: { database: database, table: tableName },
        dataType: 'json',
        success: function(response) {
            if (response.code === 0 && response.data) {
                // 将字段信息转换为简单格式
                const simpleColumns = response.data.map(function(col) {
                    return {
                        name: col.name,
                        type: col.type
                    };
                });
                window.currentTableColumns[tableName] = simpleColumns;
            }
        },
        error: function() {
            // 忽略错误
        }
    });
}
