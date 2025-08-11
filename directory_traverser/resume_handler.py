#!/usr/bin/env python3
"""
断点续传处理模块
负责读取进度、导航到断点位置、验证继续位置的准确性
"""

import os
import csv
import time
from typing import Optional, Tuple, List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class ResumeHandlerMixin:
    """断点续传功能混入类"""
    
    def check_resume_progress(self) -> Optional[Tuple[str, str]]:
        """检查是否有未完成的进度，返回(路径, 项目名)或None"""
        csv_file = os.path.join(self.output_dir, "directory_traverse_log.csv")
        
        if not os.path.exists(csv_file):
            return None
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if len(rows) <= 1:  # 只有标题行或空文件
                    return None
                
                # 获取最后一行数据
                last_row = rows[-1]
                if len(last_row) >= 2:
                    path = last_row[0].strip()  # 序号列 (如: "1-10")  
                    name = last_row[1].strip()  # 目录项名称列
                    
                    if path and name:
                        return (path, name)
                        
            return None
            
        except Exception as e:
            self.logger.error(f"读取进度文件失败: {e}")
            return None
    
    def navigate_to_resume_position(self, target_path: str, target_name: str) -> bool:
        """导航到指定的断点续传位置"""
        self.logger.info(f"🎯 导航到断点续传位置: {target_path} - {target_name}")
        
        try:
            # 解析路径 (如: "1-10" -> [1, 10])
            path_parts = [int(x) for x in target_path.split('-')]
            
            # 逐级导航到目标位置
            current_path = []
            for level, target_index in enumerate(path_parts):
                current_path.append(target_index)
                current_path_str = '-'.join(map(str, current_path))
                
                self.logger.info(f"  📍 导航到第 {level + 1} 层，位置 {current_path_str}")
                
                # 获取当前层级的所有项目
                current_items = self.find_sidebar_items_fresh()
                if not current_items:
                    self.logger.error(f"❌ 第 {level + 1} 层未找到任何项目")
                    return False
                
                # 检查目标索引是否超出范围
                if target_index > len(current_items):
                    self.logger.error(f"❌ 目标索引 {target_index} 超出范围，当前层只有 {len(current_items)} 个项目")
                    return False
                
                # 获取目标项目 (索引从1开始，所以-1)
                target_item = current_items[target_index - 1]
                item_name = target_item['name']
                
                self.logger.info(f"  🎯 找到目标项目: {item_name}")
                
                # 如果是最后一层，验证名称是否匹配
                if level == len(path_parts) - 1:
                    if item_name != target_name:
                        self.logger.warning(f"⚠️ 项目名称不匹配！期望: {target_name}, 实际: {item_name}")
                        self.logger.info("这可能是由于页面结构发生了变化")
                        return False
                    
                    self.logger.info(f"✅ 成功定位到断点续传位置: {item_name}")
                    return True
                
                # 如果不是最后一层，需要点击展开子项目
                fresh_element = self.find_element_by_text(item_name)
                if not fresh_element:
                    self.logger.error(f"❌ 无法找到元素: {item_name}")
                    return False
                
                # 点击元素展开子项目
                click_success = self.click_element_safe(fresh_element, item_name)
                if not click_success:
                    self.logger.error(f"❌ 点击失败: {item_name}")
                    return False
                
                # 等待子项目加载
                time.sleep(2)
                self.logger.info(f"  ✅ 成功展开: {item_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"导航到断点续传位置失败: {e}")
            return False
    
    def calculate_next_position(self, current_path: str, current_name: str) -> Tuple[List[int], int]:
        """计算下一个要处理的位置"""
        try:
            # 解析当前路径
            path_parts = [int(x) for x in current_path.split('-')]
            
            # 首先检查当前项目是否有子项目需要处理
            self.logger.info(f"🔍 检查 {current_name} 是否有子项目...")
            
            # 点击当前项目，看是否会展开子项目
            fresh_element = self.find_element_by_text(current_name)
            if fresh_element:
                # 记录点击前的项目数量
                items_before = self.find_sidebar_items_fresh()
                count_before = len(items_before)
                
                # 点击元素
                click_success = self.click_element_safe(fresh_element, current_name)
                if click_success:
                    time.sleep(2)  # 等待可能的子项目加载
                    
                    # 检查点击后的项目数量
                    items_after = self.find_sidebar_items_fresh()
                    count_after = len(items_after)
                    
                    if count_after > count_before:
                        self.logger.info(f"✅ 发现 {current_name} 有子项目，下一个位置: {current_path}-1")
                        return (path_parts + [1], 1)  # 进入子项目的第1个
            
            # 如果没有子项目，继续同级的下一个
            path_parts[-1] += 1  # 最后一级索引+1
            next_index = path_parts[-1]
            
            self.logger.info(f"📍 下一个同级位置: {'-'.join(map(str, path_parts))}")
            return (path_parts, next_index)
            
        except Exception as e:
            self.logger.error(f"计算下一个位置失败: {e}")
            # 默认返回下一个同级位置
            path_parts = [int(x) for x in current_path.split('-')]
            path_parts[-1] += 1
            return (path_parts, path_parts[-1])
    
    def start_from_resume_position(self, resume_path: str, resume_name: str) -> bool:
        """从断点续传位置开始遍历"""
        self.logger.info("🔄 启动断点续传模式")
        
        # 导航到断点位置
        if not self.navigate_to_resume_position(resume_path, resume_name):
            self.logger.error("❌ 无法导航到断点续传位置")
            return False
        
        # 计算下一个要处理的位置
        next_path_parts, next_index = self.calculate_next_position(resume_path, resume_name)
        next_path_str = '-'.join(map(str, next_path_parts))
        
        self.logger.info(f"▶️ 从 {next_path_str} 开始继续遍历...")
        
        # 从计算出的下一个位置开始遍历
        # 这里需要调用合适的层级开始遍历
        level = len(next_path_parts) - 1  # 计算当前层级
        
        # 构建已访问项目集合（避免重复处理）
        visited_texts = set()
        self.populate_visited_texts_from_csv(visited_texts)
        
        # 从指定位置开始递归遍历
        self.resume_recursive_traverse(level, next_path_parts, visited_texts)
        
        return True
    
    def populate_visited_texts_from_csv(self, visited_texts: set):
        """从CSV文件中读取已访问的项目名称"""
        csv_file = os.path.join(self.output_dir, "directory_traverse_log.csv")
        
        if not os.path.exists(csv_file):
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                
                for row in reader:
                    if len(row) >= 2:
                        name = row[1].strip()  # 目录项名称列
                        if name:
                            visited_texts.add(name)
                            
            self.logger.info(f"📋 从CSV读取已访问项目: {len(visited_texts)} 个")
            
        except Exception as e:
            self.logger.error(f"读取已访问项目失败: {e}")
    
    def resume_recursive_traverse(self, level: int, start_path_parts: List[int], visited_texts: set):
        """从指定位置开始的递归遍历"""
        max_depth = 10
        if level > max_depth:
            self.logger.warning(f"⚠️ 达到最大递归深度 {max_depth}，停止遍历")
            return
        
        indent = "  " * level
        self.logger.info(f"{indent}🌲 从断点续传位置开始第 {level + 1} 层遍历...")
        
        try:
            # 获取当前层级的所有项目
            current_items = self.find_sidebar_items_fresh()
            
            if not current_items:
                self.logger.info(f"{indent}📭 第 {level + 1} 层未找到项目")
                return
            
            # 确定开始的索引位置
            start_index = start_path_parts[level] if level < len(start_path_parts) else 1
            
            # 从指定索引开始处理
            for i in range(start_index, len(current_items) + 1):
                if i > len(current_items):
                    break
                
                item = current_items[i - 1]  # 转换为0基索引
                item_name = item['name']
                
                # 跳过已访问的项目
                if item_name in visited_texts:
                    self.logger.info(f"{indent}⏭️ 跳过已访问项目: {item_name}")
                    continue
                
                # 生成当前项目的路径
                current_path = start_path_parts[:level] + [i]
                path_str = "-".join(map(str, current_path))
                
                self.logger.info(f"{indent}📄 [{path_str}] 处理: {item_name}")
                
                # 标记为已访问
                visited_texts.add(item_name)
                
                # 访问控制
                if self.stats.get("successful_access", 0) > 0 or i > start_index:
                    delay = self.wait_with_respect()
                
                try:
                    # 重新获取元素并点击
                    fresh_element = self.find_element_by_text(item_name)
                    if not fresh_element:
                        self.logger.warning(f"{indent}⚠️ 无法重新定位元素: {item_name}")
                        continue
                    
                    click_success = self.click_element_safe(fresh_element, item_name)
                    if not click_success:
                        self.logger.warning(f"{indent}❌ 点击失败: {item_name}")
                        continue
                    
                    # 等待页面响应
                    time.sleep(2)
                    
                    # 提取并记录页面信息
                    page_info = self.extract_page_info()
                    if page_info:
                        page_info['directory_item'] = item_name
                        page_info['level'] = level + 1
                        page_info['index'] = path_str
                        
                        self.access_log.append(page_info)
                        self.stats["successful_access"] = self.stats.get("successful_access", 0) + 1
                        
                        # 立即保存到CSV
                        self.save_single_record_to_csv(page_info)
                        
                        self.logger.info(f"{indent}✅ 成功记录: {self.driver.title[:50]}...")
                    
                    # 检查是否有子项目
                    time.sleep(1)
                    items_after_click = self.find_sidebar_items_fresh()
                    
                    if len(items_after_click) > len(current_items):
                        self.logger.info(f"{indent}🔍 发现 {item_name} 的子目录，开始递归...")
                        self.resume_recursive_traverse(level + 1, current_path + [1], visited_texts)
                        
                        # 递归返回后重新获取DOM状态
                        current_items = self.find_sidebar_items_fresh()
                
                except Exception as e:
                    self.logger.error(f"{indent}❌ 处理项目 '{item_name}' 时出错: {e}")
                    self.failed_items.append({
                        'name': item_name,
                        'level': level + 1,
                        'reason': str(e),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    continue
            
            self.logger.info(f"{indent}✅ 第 {level + 1} 层断点续传遍历完成")
            
        except Exception as e:
            self.logger.error(f"{indent}❌ 第 {level + 1} 层断点续传遍历失败: {e}")