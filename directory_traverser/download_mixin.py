#!/usr/bin/env python3
"""
下载功能混入类
集成 test_word_click_fix_fast6.py 的智能下载功能
"""

import os
import sys
import time
from datetime import datetime

# 添加项目根目录到路径，以便导入 test_word_click_fix_fast6
sys.path.insert(0, '/Users/abc/PycharmProjects/knowledge')

try:
    from test_word_click_fix_fast6 import FastFeishuDownloader
except ImportError:
    print("警告: 无法导入 test_word_click_fix_fast6，下载功能将被禁用")
    FastFeishuDownloader = None


class DownloadMixin:
    """文档下载功能混入类"""
    
    def init_download_stats(self):
        """初始化下载相关统计"""
        if not hasattr(self, 'stats'):
            self.stats = {}
        
        # 添加下载统计字段
        self.stats.update({
            "download_attempted": 0,
            "download_successful": 0, 
            "download_failed": 0,
            "download_skipped": 0,
            "download_total_time": 0
        })
    
    def is_download_enabled(self) -> bool:
        """检查下载功能是否启用"""
        return (hasattr(self, 'enable_download') and 
                self.enable_download and 
                FastFeishuDownloader is not None)
    
    def should_download_document(self, current_url: str) -> bool:
        """判断当前文档是否应该下载"""
        if not self.is_download_enabled():
            return False
        
        # 检查是否为文档页面
        if '/wiki/' not in current_url:
            return False
        
        # 可以在这里添加更多过滤条件
        # 例如：文档类型过滤、大小限制等
        
        return True
    
    def attempt_download_current_document(self, indent: str = "", item_name: str = ""):
        """尝试下载当前文档"""
        if not self.is_download_enabled():
            return False
        
        current_url = self.driver.current_url
        
        if not self.should_download_document(current_url):
            self.stats["download_skipped"] += 1
            return False
        
        self.logger.info(f"{indent}📥 开始下载文档: {item_name}")
        self.stats["download_attempted"] += 1
        
        download_start_time = time.time()
        
        try:
            # 创建下载器实例并复用当前的driver
            downloader = FastFeishuDownloader()
            downloader.driver = self.driver
            downloader.wait = self.wait
            downloader.window_size = self.driver.get_window_size()
            
            # 执行下载
            success = downloader.execute_download_steps()
            
            download_duration = time.time() - download_start_time
            self.stats["download_total_time"] += download_duration
            
            if success:
                self.stats["download_successful"] += 1
                self.logger.info(f"{indent}✅ 文档下载成功: {item_name} (耗时: {download_duration:.1f}秒)")
                return True
            else:
                self.stats["download_failed"] += 1
                self.logger.warning(f"{indent}❌ 文档下载失败: {item_name} (耗时: {download_duration:.1f}秒)")
                return False
                
        except Exception as e:
            download_duration = time.time() - download_start_time
            self.stats["download_total_time"] += download_duration
            self.stats["download_failed"] += 1
            
            self.logger.error(f"{indent}❌ 下载异常: {item_name} - {str(e)} (耗时: {download_duration:.1f}秒)")
            
            # 重置页面状态，避免影响后续遍历
            try:
                self.driver.execute_script("document.body.click();")
                time.sleep(0.5)
            except:
                pass
            
            return False
    
    def get_download_stats_summary(self) -> dict:
        """获取下载统计摘要"""
        if not self.is_download_enabled():
            return {}
        
        total_attempts = self.stats.get("download_attempted", 0)
        successful = self.stats.get("download_successful", 0)
        failed = self.stats.get("download_failed", 0)
        skipped = self.stats.get("download_skipped", 0)
        total_time = self.stats.get("download_total_time", 0)
        
        success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0
        avg_time = (total_time / total_attempts) if total_attempts > 0 else 0
        
        return {
            "enabled": True,
            "total_attempted": total_attempts,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "success_rate": success_rate,
            "total_time": total_time,
            "average_time": avg_time
        }
    
    def print_download_summary(self):
        """打印下载功能摘要"""
        if not self.is_download_enabled():
            self.logger.info("📥 下载功能: 未启用")
            return
        
        stats = self.get_download_stats_summary()
        
        self.logger.info("📥 下载功能统计:")
        self.logger.info(f"   📊 尝试下载: {stats['total_attempted']} 个")
        self.logger.info(f"   ✅ 成功下载: {stats['successful']} 个")
        self.logger.info(f"   ❌ 下载失败: {stats['failed']} 个")
        self.logger.info(f"   ⏭️ 跳过下载: {stats['skipped']} 个")
        self.logger.info(f"   📈 成功率: {stats['success_rate']:.1f}%")
        self.logger.info(f"   ⏱️ 总耗时: {stats['total_time']:.1f}秒")
        if stats['total_attempted'] > 0:
            self.logger.info(f"   ⚡ 平均耗时: {stats['average_time']:.1f}秒/个")