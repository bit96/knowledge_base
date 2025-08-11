#!/usr/bin/env python3
"""
飞书知识库目录遍历器 - 模块化版本
基于test_word_click_fix_fast3.py架构开发的智能目录遍历工具

模块化架构，分离关注点，提升代码可维护性:
- initialization: 初始化和Chrome连接
- discovery: 目录发现和元素查找
- navigation: 导航、点击和权限检查
- extraction: 页面信息提取和递归遍历
- reporting: 数据存储和统计报告
"""

from .traverser_core import FeishuDirectoryTraverser
from .initialization import InitializationMixin
from .discovery import DiscoveryMixin
from .navigation import NavigationMixin
from .extraction import ExtractionMixin
from .reporting import ReportingMixin

__version__ = "2.0.0"
__all__ = [
    "FeishuDirectoryTraverser",
    "InitializationMixin",
    "DiscoveryMixin", 
    "NavigationMixin",
    "ExtractionMixin",
    "ReportingMixin"
]