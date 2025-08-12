#!/usr/bin/env python3
"""
核心遍历器类
整合所有功能模块，提供统一的遍历接口
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Set, Optional

from .initialization import InitializationMixin
from .discovery import DiscoveryMixin
from .navigation import NavigationMixin
from .extraction import ExtractionMixin
from .reporting import ReportingMixin
from .resume_handler import ResumeHandlerMixin
from .download_mixin import DownloadMixin


class FeishuDirectoryTraverser(InitializationMixin, DiscoveryMixin, NavigationMixin, ExtractionMixin, ReportingMixin, ResumeHandlerMixin, DownloadMixin):
    """飞书知识库目录遍历器主类"""
    
    def __init__(self, output_dir: str = "/Users/abc/PycharmProjects/knowledge/output", enable_download: bool = False):
        self.output_dir = output_dir
        self.enable_download = enable_download
        self.driver = None
        self.wait = None
        
        # 访问控制配置
        self.access_delay = (2, 5)  # 2-5秒随机延迟
        self.max_retries = 3
        self.retry_delay = 10
        
        # 数据记录
        self.visited_urls: Set[str] = set()
        self.access_log: List[Dict] = []
        self.failed_items: List[Dict] = []
        self.permission_denied_items: List[Dict] = []
        
        # 统计信息
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_items_found": 0,
            "successful_access": 0,
            "permission_denied": 0,
            "access_failed": 0,
            "total_duration": 0,
            "average_delay": 0
        }
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化下载统计
        self.init_download_stats()
        
        # 设置日志
        self.setup_logging()
    
    def traverse_all_items(self):
        """主遍历逻辑 - 多层级递归遍历"""
        self.logger.info("🚀 开始遍历知识库目录...")
        self.logger.info("严格遵循2-5秒访问间隔，尊重访问权限")
        self.logger.info("🌲 支持多层级目录递归遍历")
        
        self.stats["start_time"] = datetime.now()
        
        # 先检查当前页面类型
        current_url = self.driver.current_url
        page_title = self.driver.title
        
        # 检查是否在文档页面而非目录页面
        if '/wiki/' in current_url and '?' in current_url:
            self.logger.warning("⚠️ 检测到当前是文档详情页面，不适合批量遍历")
            self.logger.info("=" * 50)
            self.logger.info("📍 您需要导航到【知识库目录页面】才能使用此工具")
            self.logger.info("=" * 50)
            self.logger.info("🎯 正确的页面应该具备以下特征:")
            self.logger.info("   ✓ 页面显示文件/文档列表，而不是单个文档内容")
            self.logger.info("   ✓ 左侧有完整的目录树结构，包含多个文件夹和文档")
            self.logger.info("   ✓ 页面中应该有几十个或更多的文档链接")
            self.logger.info("   ✓ URL通常不包含'?'查询参数，或是知识库主页")
            self.logger.info("")
            self.logger.info("🔧 具体操作步骤:")
            self.logger.info("   1. 点击浏览器的【返回】按钮")
            self.logger.info("   2. 或点击页面顶部的知识库名称返回主页")
            self.logger.info("   3. 或在地址栏中删除'?'后面的所有参数")
            self.logger.info("   4. 确保能看到文档列表视图（表格或卡片形式）")
            self.logger.info("")
            self.logger.info(f"📄 当前页面: {page_title}")
            self.logger.info(f"🔗 当前URL: {current_url}")
            self.logger.info("=" * 50)
        
        # 开始递归遍历
        self.recursive_traverse_directory()
        
        # 更新统计信息
        self.stats["end_time"] = datetime.now()
        self.stats["total_duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # 保存结果
        self.save_results()
        
        # 打印最终统计
        self.print_final_summary()