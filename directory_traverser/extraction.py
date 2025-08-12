#!/usr/bin/env python3
"""
提取模块
处理页面信息提取、数据获取等功能
"""

import time
from datetime import datetime
from typing import Optional, Dict, List, Set
from selenium.webdriver.common.by import By
from urllib.parse import urlparse


class ExtractionMixin:
    """数据提取功能混入类"""
    
    def extract_page_info(self) -> Optional[Dict]:
        """提取当前页面信息"""
        try:
            start_time = time.time()
            
            # 等待页面加载完成
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            response_time = time.time() - start_time
            
            # 检查是否是有效的内容页面
            if not page_title or page_title.strip() == "":
                return None
            
            page_info = {
                'url': current_url,
                'title': page_title,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'response_time': round(response_time, 2)
            }
            
            self.logger.debug(f"提取页面信息: {page_title[:50]}...")
            return page_info
            
        except Exception as e:
            self.logger.error(f"提取页面信息失败: {e}")
            return None
    
    def _diagnose_current_page(self):
        """诊断当前页面，帮助用户了解问题"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # 分析页面中的所有链接
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            # 统计左侧区域的链接
            left_links = []
            for link in all_links:
                try:
                    if link.is_displayed():
                        location = link.location
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        if location['x'] < 400 and href and text:
                            left_links.append({
                                'text': text,
                                'href': href,
                                'x': location['x'],
                                'y': location['y']
                            })
                except:
                    continue
            
            # 评估页面状态
            is_doc_page = '/wiki/' in current_url and '?' in current_url
            has_enough_links = len(left_links) >= 10
            
            self.logger.info("📊 页面状态分析")
            self.logger.info("-" * 30)
            self.logger.info(f"📄 页面标题: {page_title[:60]}...")
            self.logger.info(f"🔗 页面总链接: {len(all_links)} 个")
            self.logger.info(f"👈 左侧区域链接: {len(left_links)} 个")
            
            # 状态判断
            if is_doc_page:
                self.logger.info("❌ 页面类型: 文档详情页（不适合遍历）")
            elif has_enough_links:
                self.logger.info("✅ 页面类型: 看起来像目录页面")
            else:
                self.logger.info("⚠️ 页面类型: 目录页面但链接较少")
            
            self.logger.info("")
            
            if left_links:
                self.logger.info("📋 发现的左侧链接（前5个）:")
                for i, link in enumerate(left_links[:5], 1):
                    self.logger.info(f"   {i}. {link['text'][:40]}")
                    
                if len(left_links) > 5:
                    self.logger.info(f"   ... 还有 {len(left_links) - 5} 个链接")
            else:
                self.logger.info("❌ 左侧区域未发现可遍历的链接")
            
            self.logger.info("")
            
            # 根据分析结果给出具体建议
            if is_doc_page:
                self.logger.info("🎯 解决方案: 这是文档阅读页面")
                self.logger.info("   👆 点击浏览器【返回】按钮")
                self.logger.info("   🏠 或导航到知识库主页面")
            elif len(left_links) < 3:
                self.logger.info("🎯 解决方案: 当前页面链接太少")
                self.logger.info("   📂 检查左侧目录树是否需要展开")
                self.logger.info("   📋 确保当前页面显示文档列表")
            else:
                self.logger.info("🎯 情况: 页面结构可能不匹配")
                self.logger.info("   🔍 请检查页面是否为标准的飞书知识库界面")
            
        except Exception as e:
            self.logger.error(f"页面诊断失败: {e}")
    
    def recursive_traverse_directory(self, level: int = 0, visited_texts: set = None, path: list = None, resume_mode: bool = False):
        """递归遍历多层级目录结构"""
        if visited_texts is None:
            visited_texts = set()
        if path is None:
            path = []
        
        # 检查是否启用断点续传
        if level == 0 and not resume_mode:
            resume_progress = self.check_resume_progress()
            if resume_progress:
                resume_path, resume_name = resume_progress
                self.logger.info(f"🔄 检测到上次中断位置: {resume_path} - {resume_name}")
                
                response = input(f"是否从 '{resume_name}' 位置继续？(y/n): ").strip().lower()
                if response == 'y' or response == 'yes':
                    return self.start_from_resume_position(resume_path, resume_name)
                else:
                    self.logger.info("📝 选择重新开始，将清空现有进度")
                    # 清空CSV文件，重新开始
                    self.clear_csv_file()
        
        max_depth = 10  # 防止无限递归
        if level > max_depth:
            self.logger.warning(f"⚠️ 达到最大递归深度 {max_depth}，停止遍历")
            return
        
        indent = "  " * level
        self.logger.info(f"{indent}🌲 开始第 {level + 1} 层目录遍历...")
        
        try:
            # 重新获取当前层级的所有目录项（解决stale element问题）
            current_items = self.find_sidebar_items_fresh()
            
            if not current_items:
                self.logger.info(f"{indent}📭 第 {level + 1} 层未找到新的目录项")
                return
            
            # 过滤已访问过的项目（基于文本内容）
            new_items = []
            for item in current_items:
                item_text = item['name']
                if item_text not in visited_texts:
                    new_items.append(item)
                    visited_texts.add(item_text)
            
            self.logger.info(f"{indent}📋 第 {level + 1} 层发现 {len(new_items)} 个新目录项")
            
            for i, item in enumerate(new_items, 1):
                item_name = item['name']
                
                # 生成路径式标识
                current_path = path + [i]
                path_str = "-".join(map(str, current_path))
                
                self.logger.info(f"{indent}📄 [{path_str}] 处理: {item_name}")
                
                # 访问频率控制
                if self.stats.get("successful_access", 0) > 0 or i > 1:
                    delay = self.wait_with_respect()
                
                try:
                    # 重新获取元素（避免stale reference）
                    fresh_element = self.find_element_by_text(item_name)
                    if not fresh_element:
                        self.logger.warning(f"{indent}⚠️ 无法重新定位元素: {item_name}")
                        continue
                    
                    # 点击元素
                    click_success = self.click_element_safe(fresh_element, item_name)
                    if not click_success:
                        self.logger.warning(f"{indent}❌ 点击失败: {item_name}")
                        self.failed_items.append({
                            'name': item_name,
                            'level': level + 1,
                            'reason': '点击失败',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        continue
                    
                    # 等待页面响应
                    time.sleep(2)
                    
                    # 检查是否有页面变化（URL或标题改变）
                    current_url = self.driver.current_url
                    current_title = self.driver.title
                    
                    # 【第一步：先记录父目录】
                    page_info = self.extract_page_info()
                    if page_info:
                        page_info['directory_item'] = item_name
                        page_info['level'] = level + 1
                        page_info['index'] = path_str  # 使用路径字符串作为序号
                        
                        self.access_log.append(page_info)
                        self.stats["successful_access"] = self.stats.get("successful_access", 0) + 1
                        
                        # 立即保存到CSV文件
                        self.save_single_record_to_csv(page_info)
                        
                        self.logger.info(f"{indent}✅ 成功记录父项: {current_title[:50]}...")
                    
                    # 【可选：下载当前文档】
                    if hasattr(self, 'enable_download') and self.enable_download:
                        self.attempt_download_current_document(indent, item_name)
                    
                    # 【第二步：检查并处理子目录】
                    time.sleep(1)
                    items_after_click = self.find_sidebar_items_fresh()
                    
                    # 如果点击后出现新项目，说明当前项有子目录
                    if len(items_after_click) > len(current_items):
                        self.logger.info(f"{indent}🔍 发现 {item_name} 的子目录，开始递归...")
                        
                        # 递归处理子目录，父路径是current_path
                        self.recursive_traverse_directory(level + 1, visited_texts, current_path, resume_mode=True)
                        
                        # 递归返回后重新获取DOM状态（子目录可能已收起）
                        current_items = self.find_sidebar_items_fresh()
                        self.logger.info(f"{indent}🔄 完成 {item_name} 子目录处理，继续同级遍历...")
                    
                except Exception as e:
                    self.logger.error(f"{indent}❌ 处理项目 '{item_name}' 时出错: {e}")
                    self.failed_items.append({
                        'name': item_name,
                        'level': level + 1,
                        'reason': str(e),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    continue
            
            self.logger.info(f"{indent}✅ 第 {level + 1} 层遍历完成")
            
        except Exception as e:
            self.logger.error(f"{indent}❌ 第 {level + 1} 层遍历失败: {e}")