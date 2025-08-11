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
    
    def build_path_name_mapping(self) -> dict:
        """从CSV文件构建路径-名称映射表"""
        csv_file = os.path.join(self.output_dir, "directory_traverse_log.csv")
        path_mapping = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                
                for row in reader:
                    if len(row) >= 2:
                        path = row[0].strip()
                        name = row[1].strip()
                        if path and name:
                            path_mapping[path] = name
                            
            self.logger.info(f"📋 构建路径映射表: {len(path_mapping)} 个路径")
            return path_mapping
            
        except Exception as e:
            self.logger.error(f"构建路径映射表失败: {e}")
            return {}
    
    def get_navigation_path(self, target_path: str, path_mapping: dict) -> list:
        """获取导航名称路径"""
        try:
            # 解析路径层级: "1-2-2" -> ["1", "1-2", "1-2-2"]
            path_parts = target_path.split('-')
            navigation_path = []
            
            for i in range(len(path_parts)):
                current_path = '-'.join(path_parts[:i+1])
                if current_path in path_mapping:
                    navigation_path.append(path_mapping[current_path])
                else:
                    self.logger.warning(f"⚠️ 路径 {current_path} 在映射表中不存在")
                    return []
            
            return navigation_path
            
        except Exception as e:
            self.logger.error(f"解析导航路径失败: {e}")
            return []
    
    def find_item_by_name(self, target_name: str):
        """在当前层级通过名称查找项目"""
        try:
            current_items = self.find_sidebar_items_fresh()
            
            for item in current_items:
                if item['name'] == target_name:
                    self.logger.debug(f"  ✅ 找到目标项目: {target_name}")
                    return item
            
            self.logger.debug(f"  ❌ 未找到目标项目: {target_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"按名称查找项目失败: {e}")
            return None
    
    def navigate_to_resume_position(self, target_path: str, target_name: str) -> bool:
        """导航到指定的断点续传位置 - 基于路径-名称映射"""
        self.logger.info(f"🎯 开始路径-名称映射导航")
        self.logger.info(f"📋 目标路径: {target_path} → {target_name}")
        
        try:
            # 步骤1: 构建路径-名称映射表
            path_mapping = self.build_path_name_mapping()
            if not path_mapping:
                self.logger.error("❌ 无法构建路径映射表")
                return False
            
            # 步骤2: 获取导航名称路径
            navigation_path = self.get_navigation_path(target_path, path_mapping)
            if not navigation_path:
                self.logger.error("❌ 无法解析导航路径")
                return False
            
            self.logger.info(f"📍 导航路径: {navigation_path}")
            
            # 步骤3: 逐级名称导航
            for level, level_target_name in enumerate(navigation_path[:-1]):
                self.logger.info(f"第{level + 1}层导航:")
                self.logger.info(f"🔍 查找目标: {level_target_name}")
                
                # 在当前层级查找目标项目
                target_item = self.find_item_by_name(level_target_name)
                if not target_item:
                    self.logger.error(f"❌ 第{level + 1}层未找到目标: {level_target_name}")
                    return False
                
                self.logger.info(f"✅ 找到并准备点击: {level_target_name}")
                
                # 找到对应的DOM元素并点击
                fresh_element = self.find_element_by_text(level_target_name)
                if not fresh_element:
                    self.logger.error(f"❌ 无法找到DOM元素: {level_target_name}")
                    return False
                
                # 点击展开下一层
                click_success = self.click_element_safe(fresh_element, level_target_name)
                if not click_success:
                    self.logger.error(f"❌ 点击失败: {level_target_name}")
                    return False
                
                # 等待下一层加载
                time.sleep(2)
                self.logger.info(f"✅ 成功展开: {level_target_name}")
            
            # 步骤4: 验证最终目标
            final_target = navigation_path[-1]
            self.logger.info(f"第{len(navigation_path)}层验证:")
            self.logger.info(f"🔍 查找目标: {final_target}")
            
            final_item = self.find_item_by_name(final_target)
            if final_item and final_item['name'] == target_name:
                self.logger.info(f"✅ 成功定位到断点续传位置: {target_name}")
                return True
            else:
                self.logger.error(f"❌ 最终验证失败，期望: {target_name}, 实际: {final_item['name'] if final_item else 'None'}")
                return False
            
        except Exception as e:
            self.logger.error(f"路径-名称映射导航失败: {e}")
            return False
    
    def calculate_next_position(self, current_path: str, current_name: str) -> str:
        """简化的下一个序号计算"""
        try:
            self.logger.info(f"🔍 检查 {current_name} 是否有子项目...")
            
            # 检查当前项目是否有子项目
            if self.has_children(current_name):
                next_path = f"{current_path}-1"
                self.logger.info(f"✅ 发现 {current_name} 有子项目，下一个位置: {next_path}")
                return next_path
            
            # 如果没有子项目，继续同级的下一个
            path_parts = current_path.split('-')
            path_parts[-1] = str(int(path_parts[-1]) + 1)  # 最后一级+1
            next_path = '-'.join(path_parts)
            
            self.logger.info(f"📍 下一个同级位置: {next_path}")
            return next_path
            
        except Exception as e:
            self.logger.error(f"计算下一个位置失败: {e}")
            # 默认返回下一个同级位置
            path_parts = current_path.split('-')
            path_parts[-1] = str(int(path_parts[-1]) + 1)
            return '-'.join(path_parts)
    
    def has_children(self, item_name: str) -> bool:
        """简单检查项目是否有子项目"""
        try:
            # 记录当前DOM状态
            items_before = self.find_sidebar_items_fresh()
            count_before = len(items_before)
            
            # 点击项目
            fresh_element = self.find_element_by_text(item_name)
            if fresh_element:
                click_success = self.click_element_safe(fresh_element, item_name)
                if click_success:
                    time.sleep(1)  # 等待可能的子项目加载
                    
                    # 检查是否有新项目出现
                    items_after = self.find_sidebar_items_fresh()
                    count_after = len(items_after)
                    
                    return count_after > count_before
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查子项目失败: {e}")
            return False
    
    def start_from_resume_position(self, resume_path: str, resume_name: str) -> bool:
        """从断点续传位置开始遍历"""
        self.logger.info("🔄 启动断点续传模式")
        
        # 导航到断点位置
        if not self.navigate_to_resume_position(resume_path, resume_name):
            self.logger.error("❌ 无法导航到断点续传位置")
            return False
        
        # 计算下一个要处理的位置
        next_path_str = self.calculate_next_position(resume_path, resume_name)
        
        self.logger.info(f"▶️ 从 {next_path_str} 开始继续遍历...")
        
        # 从计算出的下一个位置开始遍历
        next_path_parts = [int(x) for x in next_path_str.split('-')]
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