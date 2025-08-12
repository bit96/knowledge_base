#!/usr/bin/env python3
"""
报告模块
处理数据存储、统计、日志输出等功能
"""

import os
import csv
import json
import time
from datetime import datetime
from typing import List, Dict


class ReportingMixin:
    """数据报告和存储功能混入类"""
    
    def save_results(self):
        """保存遍历结果到文件"""
        try:
            self.logger.info("💾 开始保存遍历结果...")
            
            # 1. 保存主要结果到CSV
            self.save_to_csv()
            
            # 2. 保存权限日志
            self.save_permission_log()
            
            # 3. 保存失败项目日志
            self.save_failed_log()
            
            # 4. 保存统计摘要到JSON
            self.save_summary_json()
            
            self.logger.info("✅ 所有结果文件已保存完成")
            
        except Exception as e:
            self.logger.error(f"保存结果时出错: {e}")
    
    def save_to_csv(self):
        """保存成功访问的页面信息到CSV"""
        if not self.access_log:
            self.logger.warning("没有成功访问的页面，跳过CSV保存")
            return
        
        csv_file = os.path.join(self.output_dir, "directory_traverse_log.csv")
        
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题行
                writer.writerow([
                    '序号', '目录项名称', 'URL', 
                    '访问时间', '响应时间(秒)', '状态'
                ])
                
                # 写入数据行
                for item in self.access_log:
                    writer.writerow([
                        item.get('index', ''),
                        item.get('directory_item', ''),
                        item.get('url', ''),
                        item.get('timestamp', ''),
                        item.get('response_time', ''),
                        '成功'
                    ])
            
            self.logger.info(f"📄 CSV文件已保存: {csv_file}")
            self.logger.info(f"   包含 {len(self.access_log)} 条成功访问记录")
            
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")
    
    def save_single_record_to_csv(self, page_info):
        """立即将单条记录追加到CSV文件"""
        csv_file = os.path.join(self.output_dir, "directory_traverse_log.csv")
        
        # 检查文件是否存在，决定是否写入表头
        file_exists = os.path.exists(csv_file)
        
        try:
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 第一次写入时，先写表头
                if not file_exists:
                    writer.writerow([
                        '序号', '目录项名称', 'URL', 
                        '访问时间', '响应时间(秒)', '状态'
                    ])
                
                # 追加数据行
                writer.writerow([
                    page_info.get('index', ''),
                    page_info.get('directory_item', ''),
                    page_info.get('url', ''),
                    page_info.get('timestamp', ''),
                    page_info.get('response_time', ''),
                    '成功'
                ])
                
        except Exception as e:
            self.logger.warning(f"实时保存CSV记录失败: {e}")
    
    def clear_csv_file(self):
        """清空CSV文件，准备重新开始"""
        csv_file = os.path.join(self.output_dir, "directory_traverse_log.csv")
        
        try:
            # 创建带标题行的新文件
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '序号', '目录项名称', 'URL', 
                    '访问时间', '响应时间(秒)', '状态'
                ])
            
            self.logger.info("✅ 已清空CSV文件，准备重新开始")
            
            # 同时清空内存中的访问日志
            self.access_log = []
            
        except Exception as e:
            self.logger.error(f"清空CSV文件失败: {e}")
    
    def save_permission_log(self):
        """保存权限不足的项目日志"""
        if not self.permission_denied_items:
            return
        
        permission_log_file = os.path.join(self.output_dir, "permission_denied_log.txt")
        
        try:
            with open(permission_log_file, 'w', encoding='utf-8') as f:
                f.write("飞书知识库遍历 - 权限不足项目日志\n")
                f.write("="*50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"权限不足项目数量: {len(self.permission_denied_items)}\n\n")
                
                for i, item in enumerate(self.permission_denied_items, 1):
                    f.write(f"{i}. {item['name']}\n")
                    f.write(f"   链接: {item['href']}\n")
                    f.write(f"   时间: {item['timestamp']}\n")
                    f.write(f"   原因: 权限不足或需要特殊访问权限\n\n")
            
            self.logger.info(f"⚠️ 权限日志已保存: {permission_log_file}")
            self.logger.info(f"   记录了 {len(self.permission_denied_items)} 个权限不足的项目")
            
        except Exception as e:
            self.logger.error(f"保存权限日志失败: {e}")
    
    def save_failed_log(self):
        """保存访问失败的项目日志"""
        if not self.failed_items:
            return
        
        failed_log_file = os.path.join(self.output_dir, "failed_items_log.txt")
        
        try:
            with open(failed_log_file, 'w', encoding='utf-8') as f:
                f.write("飞书知识库遍历 - 访问失败项目日志\n")
                f.write("="*50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"访问失败项目数量: {len(self.failed_items)}\n\n")
                
                for i, item in enumerate(self.failed_items, 1):
                    f.write(f"{i}. {item['name']}\n")
                    f.write(f"   层级: 第{item.get('level', 1)}层\n")
                    f.write(f"   时间: {item['timestamp']}\n")
                    f.write(f"   失败原因: {item['reason']}\n\n")
            
            self.logger.info(f"❌ 失败日志已保存: {failed_log_file}")
            self.logger.info(f"   记录了 {len(self.failed_items)} 个访问失败的项目")
            
        except Exception as e:
            self.logger.error(f"保存失败日志失败: {e}")
    
    def save_summary_json(self):
        """保存统计摘要到JSON文件"""
        summary_file = os.path.join(self.output_dir, "traverse_summary.json")
        
        try:
            # 准备摘要数据
            summary_data = {
                "traverse_info": {
                    "start_time": self.stats["start_time"].strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": self.stats["end_time"].strftime('%Y-%m-%d %H:%M:%S'),
                    "total_duration_seconds": round(self.stats["total_duration"], 2),
                    "total_duration_formatted": self.format_duration(self.stats["total_duration"]),
                    "average_delay_seconds": round(self.stats["average_delay"], 2)
                },
                "statistics": {
                    "total_items_found": self.stats["total_items_found"],
                    "successful_access": self.stats["successful_access"],
                    "permission_denied": self.stats["permission_denied"],
                    "access_failed": self.stats["access_failed"],
                    "success_rate": round(self.stats["successful_access"] / max(self.stats["total_items_found"], 1) * 100, 2)
                },
                "download_statistics": self.get_download_stats_summary() if hasattr(self, 'get_download_stats_summary') else {},
                "output_files": {
                    "csv_log": "directory_traverse_log.csv",
                    "permission_log": "permission_denied_log.txt" if self.permission_denied_items else None,
                    "failed_log": "failed_items_log.txt" if self.failed_items else None,
                    "summary": "traverse_summary.json",
                    "main_log": "traverser.log"
                },
                "access_control": {
                    "delay_range_seconds": self.access_delay,
                    "total_delays": len(self.access_log) - 1 if len(self.access_log) > 1 else 0,
                    "respect_permissions": True,
                    "retry_mechanism": True
                }
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📊 统计摘要已保存: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"保存统计摘要失败: {e}")
    
    def format_duration(self, seconds: float) -> str:
        """格式化时间长度"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{int(minutes)}分{remaining_seconds:.1f}秒"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{int(hours)}小时{int(remaining_minutes)}分钟"
    
    def print_final_summary(self):
        """打印最终统计摘要"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 多层级递归遍历完成统计报告")
        self.logger.info("="*60)
        self.logger.info(f"⏰ 开始时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"⏰ 结束时间: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"⏱️ 总耗时: {self.format_duration(self.stats['total_duration'])}")
        self.logger.info(f"✅ 成功访问页面数: {len(self.access_log)}")
        self.logger.info(f"❌ 访问失败项目数: {len(self.failed_items)}")
        self.logger.info(f"⚠️ 权限不足项目数: {len(self.permission_denied_items)}")
        
        # 下载功能统计
        if hasattr(self, 'print_download_summary'):
            self.print_download_summary()
        
        # 层级统计
        if self.access_log:
            levels = [item.get('level', 1) for item in self.access_log]
            max_level = max(levels) if levels else 0
            self.logger.info(f"🌲 遍历最大深度: {max_level} 层")
            
            # 各层级统计
            level_stats = {}
            for level in levels:
                level_stats[level] = level_stats.get(level, 0) + 1
            
            self.logger.info("📊 各层级访问统计:")
            for level in sorted(level_stats.keys()):
                self.logger.info(f"   第 {level} 层: {level_stats[level]} 个页面")
        
        self.logger.info("\n📁 生成的文件:")
        output_files = [
            "directory_traverse_log.csv - 主要结果数据",
            "traverse_summary.json - 统计摘要",
            "traverser.log - 详细日志"
        ]
        
        if self.permission_denied_items:
            output_files.append("permission_denied_log.txt - 权限不足项目")
        
        if self.failed_items:
            output_files.append("failed_items_log.txt - 访问失败项目")
        
        for file_desc in output_files:
            self.logger.info(f"   📄 {file_desc}")
        
        self.logger.info(f"\n💾 所有文件保存在: {self.output_dir}")
        self.logger.info("="*60)