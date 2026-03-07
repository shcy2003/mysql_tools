"""
SQL查询解析器 - 用于解析联表查询中的表别名和字段映射
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class TableInfo:
    """表信息"""
    table_name: str  # 原始表名
    alias: Optional[str] = None  # 表别名
    database: Optional[str] = None  # 数据库名

    def get_identifier(self) -> str:
        """获取表标识（别名优先）"""
        return self.alias or self.table_name


@dataclass
class ColumnInfo:
    """列信息"""
    column_name: str  # 原始列名
    alias: Optional[str] = None  # 列别名
    table_alias: Optional[str] = None  # 所属表的别名
    table_name: Optional[str] = None  # 所属表的原始表名

    def get_result_name(self) -> str:
        """获取结果集中的列名（别名优先）"""
        return self.alias or self.column_name


@dataclass
class ParsedQuery:
    """解析后的查询信息"""
    tables: Dict[str, TableInfo] = field(default_factory=dict)  # 表标识 -> 表信息
    columns: List[ColumnInfo] = field(default_factory=list)  # 选中的列信息
    result_column_map: Dict[str, ColumnInfo] = field(default_factory=dict)  # 结果列名 -> 列信息

    def add_table(self, table_name: str, alias: Optional[str] = None, database: Optional[str] = None) -> TableInfo:
        """添加表信息"""
        table_info = TableInfo(table_name=table_name, alias=alias, database=database)
        identifier = table_info.get_identifier()
        self.tables[identifier] = table_info
        return table_info

    def add_column(self, column_name: str, alias: Optional[str] = None,
                  table_alias: Optional[str] = None, table_name: Optional[str] = None) -> ColumnInfo:
        """添加列信息"""
        column_info = ColumnInfo(
            column_name=column_name,
            alias=alias,
            table_alias=table_alias,
            table_name=table_name
        )
        self.columns.append(column_info)
        self.result_column_map[column_info.get_result_name()] = column_info
        return column_info

    def get_column_by_result_name(self, result_name: str) -> Optional[ColumnInfo]:
        """根据结果列名获取列信息"""
        return self.result_column_map.get(result_name)


class SQLQueryParser:
    """SQL查询解析器"""

    def __init__(self, sql: str):
        self.sql = sql.strip()
        self.parsed = ParsedQuery()

    def parse(self) -> ParsedQuery:
        """解析SQL查询"""
        # 标准化SQL（移除多余空格、转大写关键字等）
        normalized_sql = self._normalize_sql(self.sql)

        # 解析 FROM/JOIN 子句获取表信息
        self._parse_tables(normalized_sql)

        # 解析 SELECT 子句获取列信息
        self._parse_columns(normalized_sql)

        return self.parsed

    def _normalize_sql(self, sql: str) -> str:
        """标准化SQL"""
        # 移除多余空白
        sql = re.sub(r'\s+', ' ', sql).strip()
        return sql

    def _parse_tables(self, sql: str):
        """解析表信息（FROM 和 JOIN 子句）"""
        # 匹配 FROM 子句
        from_pattern = r'\bFROM\b\s+(.+?)(?=\s+(?:WHERE|GROUP|ORDER|HAVING|LIMIT|$))'
        from_match = re.search(from_pattern, sql, re.IGNORECASE)

        if from_match:
            from_clause = from_match.group(1).strip()
            self._parse_table_list(from_clause)

        # 匹配 JOIN 子句
        join_patterns = [
            r'\b(?:INNER\s+)?JOIN\b\s+(.+?)(?=\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|JOIN|INNER|LEFT|RIGHT|FULL|$))',
            r'\bLEFT\s+(?:OUTER\s+)?JOIN\b\s+(.+?)(?=\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|JOIN|INNER|LEFT|RIGHT|FULL|$))',
            r'\bRIGHT\s+(?:OUTER\s+)?JOIN\b\s+(.+?)(?=\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|JOIN|INNER|LEFT|RIGHT|FULL|$))',
            r'\bFULL\s+(?:OUTER\s+)?JOIN\b\s+(.+?)(?=\s+(?:ON|USING|WHERE|GROUP|ORDER|HAVING|LIMIT|JOIN|INNER|LEFT|RIGHT|FULL|$))',
        ]

        for pattern in join_patterns:
            matches = re.finditer(pattern, sql, re.IGNORECASE)
            for match in matches:
                join_clause = match.group(1).strip()
                self._parse_table_list(join_clause)

    def _parse_table_list(self, table_list: str):
        """解析表列表（逗号分隔）"""
        # 分割多个表（考虑括号和引号）
        tables = self._split_by_comma_outside_quotes(table_list)

        for table_spec in tables:
            table_spec = table_spec.strip()
            if not table_spec:
                continue

            # 解析单个表规范
            self._parse_single_table(table_spec)

    def _parse_single_table(self, table_spec: str):
        """解析单个表规范"""
        # 匹配模式：[database.]table [AS] alias
        pattern = r'^(?:(?:`?([^`.\s]+)`?\.)?`?([^`.\s]+)`?)(?:\s+(?:AS\s+)?`?([^`\s]+)`?)?$'
        match = re.match(pattern, table_spec, re.IGNORECASE)

        if match:
            database = match.group(1)
            table_name = match.group(2)
            alias = match.group(3)
            self.parsed.add_table(table_name, alias, database)

    def _parse_columns(self, sql: str):
        """解析 SELECT 子句中的列"""
        # 提取 SELECT 子句
        select_pattern = r'^SELECT\s+(.+?)\s+FROM\b'
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if not select_match:
            # 尝试匹配没有 FROM 关键字的 SELECT（不太可能）
            select_pattern = r'^SELECT\s+(.+)$'
            select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if not select_match:
            return

        select_clause = select_match.group(1).strip()

        # 处理 DISTINCT 等关键字
        select_clause = re.sub(r'^\s*(?:DISTINCT|ALL)\s+', '', select_clause, flags=re.IGNORECASE)

        # 分割列列表
        columns = self._split_by_comma_outside_quotes(select_clause)

        for column_spec in columns:
            column_spec = column_spec.strip()
            if column_spec == '*':
                # SELECT * - 跳过，无法确定具体列
                continue
            self._parse_single_column(column_spec)

    def _parse_single_column(self, column_spec: str):
        """解析单个列规范"""
        # 跳过复杂表达式（包含函数、括号等）
        if any(op in column_spec for op in ['(', ')', '+', '-', '*', '/', '=']):
            # 尝试提取别名（如果有）
            alias_match = re.search(r'\bAS\s+`?([^`\s]+)`?$', column_spec, re.IGNORECASE)
            if alias_match:
                alias = alias_match.group(1)
                # 对于复杂表达式，只添加别名映射
                self.parsed.add_column(
                    column_name=alias,
                    alias=alias
                )
            return

        # 匹配模式：[table_alias.]column [AS] alias
        pattern = r'^(?:`?([^`.\s]+)`?\.)?`?([^`.\s]+)`?(?:\s+(?:AS\s+)?`?([^`\s]+)`?)?$'
        match = re.match(pattern, column_spec, re.IGNORECASE)

        if match:
            table_alias = match.group(1)
            column_name = match.group(2)
            alias = match.group(3)

            # 查找表名
            table_name = None
            if table_alias and table_alias in self.parsed.tables:
                table_name = self.parsed.tables[table_alias].table_name

            self.parsed.add_column(
                column_name=column_name,
                alias=alias,
                table_alias=table_alias,
                table_name=table_name
            )

    def _split_by_comma_outside_quotes(self, text: str) -> List[str]:
        """在引号外按逗号分割文本"""
        result = []
        current = []
        in_quote = None
        i = 0

        while i < len(text):
            char = text[i]

            if char in ['`', '"', "'"]:
                if in_quote == char:
                    in_quote = None
                elif in_quote is None:
                    in_quote = char
                current.append(char)
            elif char == ',' and in_quote is None:
                result.append(''.join(current))
                current = []
            else:
                current.append(char)

            i += 1

        if current:
            result.append(''.join(current))

        return result


def parse_select_query(sql: str) -> ParsedQuery:
    """
    解析SELECT查询，提取表别名和列信息

    Args:
        sql: SELECT SQL语句

    Returns:
        ParsedQuery对象，包含解析后的表和列信息
    """
    parser = SQLQueryParser(sql)
    return parser.parse()
