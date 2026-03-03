/**
 * DataTable Component - 现代化数据表格组件
 * 支持分页、排序、筛选、选择、导出等功能
 * 
 * @version 1.0.0
 * @author Frontend Agent
 */

class DataTable {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        if (!this.container) {
            throw new Error('DataTable: Container not found');
        }

        // 默认配置
        this.defaultOptions = {
            columns: [],
            data: [],
            loading: false,
            
            // 分页配置
            pagination: {
                enabled: true,
                current: 1,
                pageSize: 20,
                pageSizeOptions: [10, 20, 50, 100],
                total: 0,
                showQuickJumper: true,
                showSizeChanger: true
            },
            
            // 排序配置
            sort: {
                enabled: true,
                field: null,
                order: null, // 'asc' | 'desc'
                multiSort: false
            },
            
            // 筛选配置
            filter: {
                enabled: true,
                filters: {},
                filterMode: 'server' // 'server' | 'client'
            },
            
            // 选择配置
            selection: {
                enabled: false,
                type: 'checkbox', // 'checkbox' | 'radio'
                selectedKeys: [],
                onChange: null
            },
            
            // 行配置
            row: {
                key: 'id',
                expandable: false,
                expandedRowRender: null,
                onClick: null,
                onDoubleClick: null,
                rowClassName: null
            },
            
            // 空状态
            empty: {
                text: '暂无数据',
                description: '没有找到符合条件的数据',
                image: null
            },
            
            // 加载状态
            loadingText: '加载中...',
            
            // 滚动配置
            scroll: {
                x: false,
                y: false
            },
            
            // 样式配置
            size: 'middle', // 'small' | 'middle' | 'large'
            bordered: true,
            striped: true,
            hover: true,
            
            // 工具栏
            toolbar: {
                enabled: true,
                showRefresh: true,
                showExport: true,
                showColumns: true,
                showFilter: true,
                customButtons: []
            },
            
            // 事件回调
            onChange: null,
            onSort: null,
            onFilter: null,
            onPageChange: null,
            onRowClick: null,
            onRowDoubleClick: null,
            onSelectChange: null,
            onExpand: null
        };

        // 合并配置
        this.options = this.mergeOptions(this.defaultOptions, options);
        
        // 初始化状态
        this.state = {
            data: this.options.data,
            loading: this.options.loading,
            pagination: { ...this.options.pagination },
            sort: { ...this.options.sort },
            filter: { ...this.options.filter },
            selection: { ...this.options.selection },
            expandedRows: []
        };

        // 缓存DOM元素
        this.elements = {};
        
        // 初始化
        this.init();
    }

    /**
     * 合并配置（深拷贝）
     */
    mergeOptions(defaults, options) {
        const merged = { ...defaults };
        
        for (const key in options) {
            if (options.hasOwnProperty(key)) {
                if (typeof options[key] === 'object' && options[key] !== null && !Array.isArray(options[key])) {
                    merged[key] = this.mergeOptions(defaults[key] || {}, options[key]);
                } else {
                    merged[key] = options[key];
                }
            }
        }
        
        return merged;
    }

    /**
     * 初始化组件
     */
    init() {
        this.render();
        this.bindEvents();
        this.updateUI();
    }

    /**
     * 渲染组件
     */
    render() {
        const { options, state } = this;
        
        // 创建容器结构
        this.container.innerHTML = `
            <div class="datatable-wrapper datatable-size-${options.size}">
                ${this.renderToolbar()}
                ${this.renderTable()}
                ${options.pagination.enabled ? this.renderPagination() : ''}
            </div>
        `;
        
        // 缓存DOM元素
        this.cacheElements();
    }

    /**
     * 渲染工具栏
     */
    renderToolbar() {
        const { toolbar } = this.options;
        
        if (!toolbar.enabled) return '';
        
        return `
            <div class="datatable-toolbar">
                <div class="datatable-toolbar-left">
                    ${toolbar.showRefresh ? `
                        <button class="btn btn-sm btn-outline-secondary datatable-btn-refresh" title="刷新">
                            <i class="bi bi-arrow-clockwise"></i> 刷新
                        </button>
                    ` : ''}
                    ${toolbar.showFilter ? `
                        <button class="btn btn-sm btn-outline-secondary datatable-btn-filter" title="筛选">
                            <i class="bi bi-funnel"></i> 筛选
                        </button>
                    ` : ''}
                </div>
                <div class="datatable-toolbar-right">
                    ${toolbar.showColumns ? `
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                                <i class="bi bi-columns"></i> 列显示
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end datatable-column-dropdown">
                                ${this.renderColumnToggles()}
                            </ul>
                        </div>
                    ` : ''}
                    ${toolbar.showExport ? `
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                                <i class="bi bi-download"></i> 导出
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="#" data-format="csv"><i class="bi bi-filetype-csv"></i> CSV</a></li>
                                <li><a class="dropdown-item" href="#" data-format="excel"><i class="bi bi-filetype-xlsx"></i> Excel</a></li>
                                <li><a class="dropdown-item" href="#" data-format="json"><i class="bi bi-filetype-json"></i> JSON</a></li>
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * 渲染列显示切换
     */
    renderColumnToggles() {
        return this.options.columns
            .filter(col => col.key !== 'selection')
            .map(col => `
                <li>
                    <label class="dropdown-item">
                        <input type="checkbox" class="form-check-input me-2" 
                               data-column="${col.key}" ${col.visible !== false ? 'checked' : ''}>
                        ${col.title}
                    </label>
                </li>
            `).join('');
    }

    /**
     * 渲染表格
     */
    renderTable() {
        const { options, state } = this;
        
        return `
            <div class="datatable-container ${options.bordered ? 'datatable-bordered' : ''} ${options.scroll.x ? 'datatable-scroll-x' : ''} ${options.scroll.y ? 'datatable-scroll-y' : ''}">
                <table class="datatable ${options.striped ? 'datatable-striped' : ''} ${options.hover ? 'datatable-hover' : ''}">
                    ${this.renderTableHeader()}
                    ${this.renderTableBody()}
                </table>
                ${state.loading ? this.renderLoading() : ''}
                ${!state.loading && state.data.length === 0 ? this.renderEmpty() : ''}
            </div>
        `;
    }

    /**
     * 渲染表头
     */
    renderTableHeader() {
        const { options, state } = this;
        const { sort, selection, columns } = options;
        
        return `
            <thead class="datatable-thead">
                <tr>
                    ${selection.enabled ? `
                        <th class="datatable-selection-column">
                            ${selection.type === 'checkbox' ? `
                                <input type="checkbox" class="form-check-input datatable-select-all" 
                                    ${this.isAllSelected() ? 'checked' : ''}>
                            ` : ''}
                        </th>
                    ` : ''}
                    ${columns
                        .filter(col => col.visible !== false)
                        .map(col => {
                            const isSorted = sort.field === col.key;
                            const sortOrder = isSorted ? sort.order : '';
                            
                            return `
                                <th class="datatable-cell ${col.fixed ? `datatable-fixed-${col.fixed}` : ''} ${isSorted ? 'datatable-sorted' : ''}"
                                    data-column="${col.key}"
                                    style="width: ${col.width || 'auto'}; text-align: ${col.align || 'left'}">
                                    <div class="datatable-column-title">
                                        ${col.title}
                                        ${sort.enabled && col.sortable !== false ? `
                                            <span class="datatable-sort-icons">
                                                <i class="bi bi-caret-up-fill ${sortOrder === 'asc' ? 'active' : ''}"></i>
                                                <i class="bi bi-caret-down-fill ${sortOrder === 'desc' ? 'active' : ''}"></i>
                                            </span>
                                        ` : ''}
                                    </div>
                                </th>
                            `;
                        }).join('')}
                </tr>
                ${this.options.filter.enabled ? this.renderFilterRow() : ''}
            </thead>
        `;
    }

    /**
     * 渲染筛选行
     */
    renderFilterRow() {
        const { columns, filter } = this.options;
        const { filters } = this.state.filter;
        
        return `
            <tr class="datatable-filter-row">
                ${this.options.selection.enabled ? '<th></th>' : ''}
                ${columns
                    .filter(col => col.visible !== false)
                    .map(col => {
                        if (!col.filterable) return '<th></th>';
                        
                        const currentFilter = filters[col.key];
                        
                        return `
                            <th>
                                <input type="text" 
                                       class="form-control form-control-sm datatable-filter-input" 
                                       placeholder="筛选 ${col.title}"
                                       data-column="${col.key}"
                                       value="${currentFilter || ''}">
                            </th>
                        `;
                    }).join('')}
            </tr>
        `;
    }

    /**
     * 渲染表格主体
     */
    renderTableBody() {
        const { options, state } = this;
        const { data } = state;
        const { columns, selection, row } = options;
        
        if (state.loading || data.length === 0) {
            return '<tbody class="datatable-tbody"></tbody>';
        }
        
        return `
            <tbody class="datatable-tbody">
                ${data.map((record, index) => {
                    const rowKey = record[row.key] || index;
                    const isSelected = this.isRowSelected(rowKey);
                    const isExpanded = this.isRowExpanded(rowKey);
                    
                    return `
                        <tr class="datatable-row ${isSelected ? 'datatable-row-selected' : ''} ${row.rowClassName ? row.rowClassName(record, index) : ''}"
                            data-key="${rowKey}">
                            ${selection.enabled ? `
                                <td class="datatable-selection-column">
                                    <input type="${selection.type === 'radio' ? 'radio' : 'checkbox'}" 
                                           class="form-check-input datatable-select-row" 
                                           name="${selection.type === 'radio' ? 'datatable-radio' : ''}"
                                           value="${rowKey}"
                                           ${isSelected ? 'checked' : ''}>
                                </td>
                            ` : ''}
                            ${columns
                                .filter(col => col.visible !== false)
                                .map(col => {
                                    let value = record[col.key];
                                    if (col.formatter) {
                                        value = col.formatter(value, record);
                                    }
                                    return `
                                        <td class="datatable-cell ${col.fixed ? `datatable-fixed-${col.fixed}` : ''}"
                                            data-column="${col.key}"
                                            style="text-align: ${col.align || 'left'}">
                                            ${value !== null && value !== undefined ? value : ''}
                                        </td>
                                    `;
                                }).join('')}
                        </tr>
                        ${isExpanded && row.expandable && row.expandedRowRender ? `
                            <tr class="datatable-expanded-row">
                                <td colspan="${this.getColumnCount()}" class="datatable-expanded-cell">
                                    <div class="datatable-expanded-content">
                                        ${row.expandedRowRender(record)}
                                    </div>
                                </td>
                            </tr>
                        ` : ''}
                    `;
                }).join('')}
            </tbody>
        `;
    }

    /**
     * 渲染加载状态
     */
    renderLoading() {
        const colCount = this.getColumnCount();
        return `
            <div class="datatable-loading">
                <div class="datatable-loading-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-2 text-muted">${this.options.loadingText}</p>
                </div>
            </div>
        `;
    }

    /**
     * 渲染空状态
     */
    renderEmpty() {
        const { empty } = this.options;
        return `
            <div class="datatable-empty">
                <div class="datatable-empty-content">
                    <i class="bi bi-inbox display-4 text-muted"></i>
                    <p class="mt-3 mb-1 fs-5 fw-medium">${empty.text}</p>
                    <p class="text-muted">${empty.description}</p>
                </div>
            </div>
        `;
    }

    /**
     * 渲染分页
     */
    renderPagination() {
        const { pagination } = this.state;
        const { pageSizeOptions, showQuickJumper, showSizeChanger } = this.options.pagination;
        
        const totalPages = Math.ceil(pagination.total / pagination.pageSize);
        const current = pagination.current;
        
        // 计算显示的页码范围
        let startPage = Math.max(1, current - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        const pages = [];
        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }
        
        return `
            <div class="datatable-pagination">
                <div class="datatable-pagination-info">
                    显示 ${(current - 1) * pagination.pageSize + 1} - 
                    ${Math.min(current * pagination.pageSize, pagination.total)} 条，
                    共 ${pagination.total} 条
                </div>
                <div class="datatable-pagination-controls">
                    ${showSizeChanger ? `
                        <select class="form-select form-select-sm datatable-page-size">
                            ${pageSizeOptions.map(size => `
                                <option value="${size}" ${size === pagination.pageSize ? 'selected' : ''}>
                                    ${size} 条/页
                                </option>
                            `).join('')}
                        </select>
                    ` : ''}
                    <nav aria-label="Table pagination">
                        <ul class="pagination pagination-sm mb-0">
                            <li class="page-item ${current === 1 ? 'disabled' : ''}">
                                <a class="page-link" href="#" data-page="${current - 1}" aria-label="上一页">
                                    <span aria-hidden="true">&laquo;</span>
                                </a>
                            </li>
                            ${startPage > 1 ? `
                                <li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>
                                ${startPage > 2 ? '<li class="page-item disabled"><span class="page-link">...</span></li>' : ''}
                            ` : ''}
                            ${pages.map(page => `
                                <li class="page-item ${page === current ? 'active' : ''}">
                                    <a class="page-link" href="#" data-page="${page}">${page}</a>
                                </li>
                            `).join('')}
                            ${endPage < totalPages ? `
                                ${endPage < totalPages - 1 ? '<li class="page-item disabled"><span class="page-link">...</span></li>' : ''}
                                <li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>
                            ` : ''}
                            <li class="page-item ${current === totalPages || totalPages === 0 ? 'disabled' : ''}">
                                <a class="page-link" href="#" data-page="${current + 1}" aria-label="下一页">
                                    <span aria-hidden="true">&raquo;</span>
                                </a>
                            </li>
                        </ul>
                    </nav>
                    ${showQuickJumper && totalPages > 1 ? `
                        <div class="datatable-quick-jumper">
                            <span>跳至</span>
                            <input type="number" class="form-control form-control-sm" min="1" max="${totalPages}" value="${current}">
                            <span>页</span>
                            <button class="btn btn-sm btn-primary">确定</button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * 获取列数量
     */
    getColumnCount() {
        const { columns, selection } = this.options;
        let count = columns.filter(col => col.visible !== false).length;
        if (selection.enabled) count++;
        return count;
    }

    /**
     * 缓存DOM元素
     */
    cacheElements() {
        this.elements = {
            wrapper: this.container.querySelector('.datatable-wrapper'),
            toolbar: this.container.querySelector('.datatable-toolbar'),
            table: this.container.querySelector('.datatable'),
            tbody: this.container.querySelector('.datatable-tbody'),
            pagination: this.container.querySelector('.datatable-pagination')
        };
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 排序事件
        if (this.options.sort.enabled) {
            this.container.addEventListener('click', (e) => {
                const sortHeader = e.target.closest('.datatable-column-title');
                if (sortHeader) {
                    const th = sortHeader.closest('th');
                    if (th && th.dataset.column) {
                        this.handleSort(th.dataset.column);
                    }
                }
            });
        }

        // 分页事件
        if (this.options.pagination.enabled) {
            this.container.addEventListener('click', (e) => {
                const pageLink = e.target.closest('[data-page]');
                if (pageLink) {
                    e.preventDefault();
                    const page = parseInt(pageLink.dataset.page, 10);
                    if (page && page !== this.state.pagination.current) {
                        this.handlePageChange(page);
                    }
                }
            });

            // 每页条数变化
            const pageSizeSelect = this.container.querySelector('.datatable-page-size');
            if (pageSizeSelect) {
                pageSizeSelect.addEventListener('change', (e) => {
                    const pageSize = parseInt(e.target.value, 10);
                    this.handlePageSizeChange(pageSize);
                });
            }
        }

        // 行选择事件
        if (this.options.selection.enabled) {
            this.container.addEventListener('change', (e) => {
                if (e.target.classList.contains('datatable-select-row')) {
                    const rowKey = e.target.value;
                    this.handleRowSelect(rowKey, e.target.checked);
                } else if (e.target.classList.contains('datatable-select-all')) {
                    this.handleSelectAll(e.target.checked);
                }
            });
        }

        // 行点击事件
        if (this.options.row.onClick) {
            this.container.addEventListener('click', (e) => {
                const row = e.target.closest('.datatable-row');
                if (row && !e.target.closest('.datatable-selection-column') && !e.target.closest('button') && !e.target.closest('a')) {
                    const rowKey = row.dataset.key;
                    const record = this.state.data.find(item => (item[this.options.row.key] || item) == rowKey);
                    if (record) {
                        this.options.row.onClick(record, parseInt(row.dataset.index, 10), e);
                    }
                }
            });
        }

        // 筛选输入事件（防抖）
        if (this.options.filter.enabled) {
            let debounceTimer;
            this.container.addEventListener('input', (e) => {
                if (e.target.classList.contains('datatable-filter-input')) {
                    clearTimeout(debounceTimer);
                    const column = e.target.dataset.column;
                    const value = e.target.value;
                    
                    debounceTimer = setTimeout(() => {
                        this.handleFilterChange(column, value);
                    }, 300);
                }
            });
        }
    }

    /**
     * 处理排序
     */
    handleSort(field) {
        let { sort } = this.state;
        let order;
        
        if (sort.field === field) {
            // 切换排序方向
            order = sort.order === 'asc' ? 'desc' : 'asc';
        } else {
            // 新字段，默认升序
            order = 'asc';
        }
        
        sort = { ...sort, field, order };
        this.state.sort = sort;
        
        // 重置到第一页
        this.state.pagination.current = 1;
        
        // 触发事件
        if (this.options.onSort) {
            this.options.onSort(sort);
        }
        
        if (this.options.onChange) {
            this.options.onChange(this.state.pagination, this.state.filter.filters, sort);
        }
        
        // 客户端排序或触发服务端请求
        if (this.options.filter.filterMode === 'client') {
            this.clientSort();
        }
        
        this.updateUI();
    }

    /**
     * 处理分页变化
     */
    handlePageChange(page) {
        this.state.pagination.current = page;
        
        if (this.options.onPageChange) {
            this.options.onPageChange(page, this.state.pagination.pageSize);
        }
        
        if (this.options.onChange) {
            this.options.onChange(this.state.pagination, this.state.filter.filters, this.state.sort);
        }
        
        // 滚动到顶部
        const container = this.container.querySelector('.datatable-container');
        if (container) {
            container.scrollTop = 0;
        }
        
        this.updateUI();
    }

    /**
     * 处理每页条数变化
     */
    handlePageSizeChange(pageSize) {
        this.state.pagination.pageSize = pageSize;
        this.state.pagination.current = 1; // 重置到第一页
        
        if (this.options.onChange) {
            this.options.onChange(this.state.pagination, this.state.filter.filters, this.state.sort);
        }
        
        this.updateUI();
    }

    /**
     * 处理筛选变化
     */
    handleFilterChange(column, value) {
        const { filters } = this.state.filter;
        
        if (value) {
            filters[column] = value;
        } else {
            delete filters[column];
        }
        
        this.state.filter.filters = filters;
        this.state.pagination.current = 1; // 重置到第一页
        
        if (this.options.onFilter) {
            this.options.onFilter(filters);
        }
        
        if (this.options.onChange) {
            this.options.onChange(this.state.pagination, filters, this.state.sort);
        }
        
        // 客户端筛选或触发服务端请求
        if (this.options.filter.filterMode === 'client') {
            this.clientFilter();
        }
        
        this.updateUI();
    }

    /**
     * 处理行选择
     */
    handleRowSelect(rowKey, checked) {
        const { selectedKeys } = this.state.selection;
        const newSelectedKeys = [...selectedKeys];
        
        if (checked) {
            if (!newSelectedKeys.includes(rowKey)) {
                newSelectedKeys.push(rowKey);
            }
        } else {
            const index = newSelectedKeys.indexOf(rowKey);
            if (index > -1) {
                newSelectedKeys.splice(index, 1);
            }
        }
        
        this.state.selection.selectedKeys = newSelectedKeys;
        
        if (this.options.selection.onChange) {
            const selectedRows = this.state.data.filter(row => {
                const key = row[this.options.row.key] || row;
                return newSelectedKeys.includes(String(key));
            });
            this.options.selection.onChange(newSelectedKeys, selectedRows);
        }
        
        if (this.options.onSelectChange) {
            this.options.onSelectChange(newSelectedKeys);
        }
        
        this.updateUI();
    }

    /**
     * 处理全选
     */
    handleSelectAll(checked) {
        const { data } = this.state;
        const { row } = this.options;
        
        let newSelectedKeys = [];
        if (checked) {
            newSelectedKeys = data.map(item => String(item[row.key] || item));
        }
        
        this.state.selection.selectedKeys = newSelectedKeys;
        
        if (this.options.selection.onChange) {
            const selectedRows = checked ? [...data] : [];
            this.options.selection.onChange(newSelectedKeys, selectedRows);
        }
        
        if (this.options.onSelectChange) {
            this.options.onSelectChange(newSelectedKeys);
        }
        
        this.updateUI();
    }

    /**
     * 判断是否全选
     */
    isAllSelected() {
        const { data } = this.state;
        const { selectedKeys } = this.state.selection;
        const { row } = this.options;
        
        if (data.length === 0) return false;
        
        return data.every(item => {
            const key = String(item[row.key] || item);
            return selectedKeys.includes(key);
        });
    }

    /**
     * 判断是否选中行
     */
    isRowSelected(rowKey) {
        return this.state.selection.selectedKeys.includes(String(rowKey));
    }

    /**
     * 判断是否展开行
     */
    isRowExpanded(rowKey) {
        return this.state.expandedRows.includes(String(rowKey));
    }

    /**
     * 客户端排序
     */
    clientSort() {
        const { data, sort } = this.state;
        const { field, order } = sort;
        
        if (!field || !order) return;
        
        data.sort((a, b) => {
            let aVal = a[field];
            let bVal = b[field];
            
            if (aVal === null || aVal === undefined) aVal = '';
            if (bVal === null || bVal === undefined) bVal = '';
            
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (aVal < bVal) return order === 'asc' ? -1 : 1;
            if (aVal > bVal) return order === 'asc' ? 1 : -1;
            return 0;
        });
    }

    /**
     * 客户端筛选
     */
    clientFilter() {
        // 筛选需要重新加载数据或从原始数据中筛选
        // 这里触发 onChange 让父组件重新加载数据
        if (this.options.onChange) {
            this.options.onChange(this.state.pagination, this.state.filter.filters, this.state.sort);
        }
    }

    /**
     * 更新UI
     */
    updateUI() {
        // 重新渲染表格主体和分页
        const tableContainer = this.container.querySelector('.datatable-container');
        const paginationContainer = this.container.querySelector('.datatable-pagination');
        
        if (tableContainer) {
            const table = tableContainer.querySelector('.datatable');
            const thead = table.querySelector('.datatable-thead');
            const oldTbody = table.querySelector('.datatable-tbody');
            
            // 更新表头（排序状态）
            if (thead) {
                const newThead = document.createElement('thead');
                newThead.innerHTML = this.renderTableHeader().replace(/<thead>|<\/thead>/g, '');
                thead.innerHTML = newThead.innerHTML;
            }
            
            // 更新表体
            if (oldTbody) {
                const newTbody = document.createElement('tbody');
                newTbody.innerHTML = this.renderTableBody().replace(/<tbody>|<\/tbody>/g, '');
                oldTbody.innerHTML = newTbody.innerHTML;
            }
            
            // 更新加载和空状态
            const existingLoading = tableContainer.querySelector('.datatable-loading');
            const existingEmpty = tableContainer.querySelector('.datatable-empty');
            
            if (existingLoading) existingLoading.remove();
            if (existingEmpty) existingEmpty.remove();
            
            if (this.state.loading) {
                tableContainer.insertAdjacentHTML('beforeend', this.renderLoading());
            } else if (this.state.data.length === 0) {
                tableContainer.insertAdjacentHTML('beforeend', this.renderEmpty());
            }
        }
        
        if (paginationContainer && this.options.pagination.enabled) {
            paginationContainer.outerHTML = this.renderPagination();
        }
        
        // 重新绑定事件
        this.bindPaginationEvents();
    }

    /**
     * 绑定分页相关事件
     */
    bindPaginationEvents() {
        // 分页点击事件
        const paginationContainer = this.container.querySelector('.datatable-pagination');
        if (paginationContainer) {
            paginationContainer.addEventListener('click', (e) => {
                const pageLink = e.target.closest('[data-page]');
                if (pageLink) {
                    e.preventDefault();
                    const page = parseInt(pageLink.dataset.page, 10);
                    if (page && page !== this.state.pagination.current) {
                        this.handlePageChange(page);
                    }
                }
            });

            // 每页条数变化
            const pageSizeSelect = paginationContainer.querySelector('.datatable-page-size');
            if (pageSizeSelect) {
                pageSizeSelect.addEventListener('change', (e) => {
                    const pageSize = parseInt(e.target.value, 10);
                    this.handlePageSizeChange(pageSize);
                });
            }
        }
    }

    // ==================== 公共API ====================

    /**
     * 刷新数据
     */
    refresh() {
        if (this.options.onChange) {
            this.options.onChange(this.state.pagination, this.state.filter.filters, this.state.sort);
        }
    }

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        this.state.loading = loading;
        this.updateUI();
    }

    /**
     * 设置数据
     */
    setData(data, total) {
        this.state.data = data;
        if (total !== undefined) {
            this.state.pagination.total = total;
        }
        this.updateUI();
    }

    /**
     * 获取选中的行
     */
    getSelectedRows() {
        return this.state.selection.selectedKeys;
    }

    /**
     * 清空选择
     */
    clearSelection() {
        this.state.selection.selectedKeys = [];
        this.updateUI();
    }

    /**
     * 获取当前分页、排序、筛选状态
     */
    getState() {
        return {
            pagination: { ...this.state.pagination },
            sort: { ...this.state.sort },
            filter: { ...this.state.filter }
        };
    }

    /**
     * 销毁组件
     */
    destroy() {
        this.container.innerHTML = '';
    }
}

// 导出模块（支持ES6和CommonJS）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataTable;
}
