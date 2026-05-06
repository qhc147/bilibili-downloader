"""
更新日志解析模块

从 Markdown 格式的更新日志中提取关键更新内容。
"""

import re
from typing import List


class ChangelogParser:
    """更新日志解析器"""

    DEFAULT_MESSAGE = "• 性能优化和 bug 修复"
    MAX_ITEM_LENGTH = 100

    def parse(self, markdown: str, max_items: int = 5) -> str:
        """
        解析 Markdown 格式的更新日志，提取关键更新内容。

        Args:
            markdown: Markdown 格式的更新日志文本
            max_items: 最多返回的条目数，默认 5 条

        Returns:
            格式化的更新内容字符串，每条以 • 开头，多条之间用换行符分隔

        Examples:
            >>> parser = ChangelogParser()
            >>> changelog = "# v1.0\\n- Fix bug\\n- Add feature"
            >>> print(parser.parse(changelog))
            • Fix bug
            • Add feature
        """
        if not markdown or not markdown.strip():
            return self.DEFAULT_MESSAGE

        items = self._extract_items(markdown)

        if not items:
            return self.DEFAULT_MESSAGE

        # 限制条目数
        items = items[:max_items]

        # 格式化输出
        formatted_items = []
        for item in items:
            # 截断过长内容
            if len(item) > self.MAX_ITEM_LENGTH:
                item = item[:self.MAX_ITEM_LENGTH - 3] + "..."
            formatted_items.append(f"• {item}")

        return "\n".join(formatted_items)

    def _extract_items(self, markdown: str) -> List[str]:
        """
        从 Markdown 中提取列表项。

        Args:
            markdown: Markdown 文本

        Returns:
            提取的列表项列表
        """
        items = []
        lines = markdown.split("\n")

        in_code_block = False

        for line in lines:
            line = line.strip()

            # 跳过代码块
            if line.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # 跳过空行
            if not line:
                continue

            # 跳过标题行（但不提取标题内容）
            if line.startswith("#"):
                continue

            # 提取列表项（以 -, *, + 开头）
            list_item_match = re.match(r'^[-*+]\s+(.+)$', line)
            if list_item_match:
                content = list_item_match.group(1).strip()

                # 过滤掉纯链接行
                if self._is_valid_item(content):
                    items.append(content)

        return items

    def _is_valid_item(self, content: str) -> bool:
        """
        判断内容是否为有效的更新项。

        Args:
            content: 待判断的内容

        Returns:
            是否为有效项
        """
        # 过滤掉纯链接
        if re.match(r'^https?://', content):
            return False

        # 过滤掉只包含链接的行
        if re.match(r'^\[.+\]\(.+\)$', content):
            return False

        # 过滤掉过短的内容（少于 3 个字符）
        if len(content) < 3:
            return False

        return True
