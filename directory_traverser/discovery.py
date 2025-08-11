#!/usr/bin/env python3
"""
发现模块
处理目录发现、元素查找、验证等功能
"""

from selenium.webdriver.common.by import By
from typing import List, Dict


class DiscoveryMixin:
    """目录发现功能混入类"""
    
    def find_sidebar_items(self) -> List[Dict]:
        """查找左侧目录的所有项目"""
        try:
            self.logger.info("🔍 开始搜索左侧目录项...")
            
            # 多种策略查找侧边栏目录项
            sidebar_selectors = [
                # 飞书目录树特定选择器（基于分析结果）
                '.workspace-tree-view-node-content',
                '[class*="workspace-tree"]',
                '[class*="tree-view-node"]',
                
                # 树形结构选择器
                '[class*="tree"] span[class*="content"]',
                '[class*="tree"] [class*="node"]',
                '[class*="folder"]',
                
                # 展开/折叠相关选择器
                '[class*="expand"]',
                '[class*="collapse"]',
                
                # 传统链接选择器（兜底）
                '.sidebar a[href]',
                '[class*="side"] a[href]',
                '[class*="nav"] a[href]',
                'nav a[href]',
                'aside a[href]'
            ]
            
            all_items = []
            found_selectors = []
            
            for selector in sidebar_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        found_selectors.append((selector, len(elements)))
                        
                        for element in elements:
                            try:
                                # 检查元素是否可见和可点击
                                if not element.is_displayed() or not element.is_enabled():
                                    continue
                                
                                text = element.text.strip()
                                
                                # 获取href（如果有的话）
                                href = element.get_attribute('href')
                                
                                # 对于目录树节点，可能没有href，但有文本内容
                                if not text:
                                    continue
                                
                                # 检查是否在左侧区域
                                location = element.location
                                if location['x'] > 400:  # 左侧区域宽度限制
                                    continue
                                
                                # 过滤明显不是目录项的文本
                                if self.is_valid_directory_item(text, href):
                                    # 对于没有href的可点击元素，使用文本作为标识
                                    item_href = href if href else f"javascript:void(0)#{text}"
                                    
                                    item_info = {
                                        'element': element,
                                        'name': text,
                                        'href': item_href,
                                        'location': location,
                                        'is_clickable_node': not bool(href)  # 标记是否为可点击节点
                                    }
                                    
                                    all_items.append(item_info)
                                
                            except Exception as e:
                                continue
                                
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 查找失败: {e}")
                    continue
            
            # 去重（基于href）
            seen_hrefs = set()
            unique_items = []
            for item in all_items:
                if item['href'] not in seen_hrefs:
                    seen_hrefs.add(item['href'])
                    unique_items.append(item)
            
            self.logger.info(f"📋 找到 {len(unique_items)} 个唯一的目录项")
            if found_selectors:
                self.logger.info("使用的选择器:")
                for selector, count in found_selectors[:3]:  # 只显示前3个有效的选择器
                    self.logger.info(f"  - {selector}: {count} 个元素")
            
            return unique_items
            
        except Exception as e:
            self.logger.error(f"查找侧边栏项目失败: {e}")
            return []
    
    def find_sidebar_items_fresh(self) -> List[Dict]:
        """重新获取侧边栏项目（避免stale element问题）"""
        try:
            # 使用相同的逻辑重新查找，但每次都是新的元素引用
            selector = '.workspace-tree-view-node-content'
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            items = []
            for element in elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.strip()
                        location = element.location
                        
                        # 检查是否在左侧区域
                        if location['x'] < 400 and text and self.is_valid_directory_item(text):
                            items.append({
                                'element': element,
                                'name': text,
                                'href': f"javascript:void(0)#{text}",
                                'location': location,
                                'is_clickable_node': True
                            })
                except:
                    continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"重新获取侧边栏项目失败: {e}")
            return []
    
    def find_element_by_text(self, text: str):
        """根据文本内容重新查找元素"""
        try:
            # 使用contains来匹配类名和文本，更灵活
            xpath = f"//*[contains(@class,'workspace-tree-view-node-content') and contains(text(),'{text}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)
            self.logger.debug(f"找到 {len(elements)} 个匹配元素，XPath: {xpath}")
            
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return element
            
            return None
            
        except Exception as e:
            self.logger.debug(f"根据文本查找元素失败: {e}")
            return None
    
    def is_valid_document_link(self, href: str) -> bool:
        """判断是否是有效的文档链接"""
        if not href:
            return False
        
        href_lower = href.lower()
        
        # 排除外部链接（但保留飞书域名）
        if href.startswith('http') and not any(domain in href_lower for domain in ['feishu', 'lark', 'bytedance']):
            return False
        
        # 排除特殊链接
        exclude_patterns = [
            'javascript:', 'mailto:', 'tel:', '#',
            '/login', '/logout', '/settings', '/profile',
            '/search', '/help', '/support', '?tab='
        ]
        
        if any(pattern in href_lower for pattern in exclude_patterns):
            return False
        
        # 包含文档相关路径的链接（扩展模式）
        doc_patterns = [
            '/wiki/', '/docs/', '/docx/', '/sheets/', '/base/',
            '/file/', '/document/', '/space/', '/drive/',
            # 飞书特殊模式
            'fromscene=', 'wiki?', 'docx?', 'sheets?'
        ]
        
        return any(pattern in href_lower for pattern in doc_patterns)
    
    def is_valid_directory_item(self, text: str, href: str = None) -> bool:
        """判断是否是有效的目录项"""
        if not text or len(text.strip()) < 2:
            return False
        
        text_lower = text.lower()
        
        # 排除明显的UI元素文本
        exclude_texts = [
            'search', 'menu', 'home', 'settings', 'profile', 'login', 'logout',
            '搜索', '菜单', '首页', '设置', '个人资料', '登录', '登出',
            '目录', '返回', 'back', 'close', '关闭', '展开', '收起',
            'expand', 'collapse', 'toggle'
        ]
        
        # 如果文本过短或在排除列表中，跳过
        if any(exclude in text_lower for exclude in exclude_texts):
            return False
        
        # 如果文本过长（可能是整个页面内容），跳过
        if len(text) > 100:
            return False
        
        # 检查是否包含换行符（可能是复合内容）
        if '\n' in text and len(text.split('\n')) > 3:
            return False
        
        # 如果有href，使用原有的链接验证
        if href and href.startswith('http'):
            return self.is_valid_document_link(href)
        
        # 对于可点击节点，如果文本看起来像目录名称，接受它
        return True
    
    def expand_collapsed_items(self):
        """展开所有折叠的目录项"""
        try:
            self.logger.info("🔓 尝试展开折叠的目录项...")
            
            # 查找展开按钮的选择器
            expand_selectors = [
                '[class*="expand"]',
                '[class*="collapse"]', 
                '[class*="toggle"]',
                '.tree-expand',
                '.tree-toggle',
                '[aria-expanded="false"]'
            ]
            
            expanded_count = 0
            
            for selector in expand_selectors:
                try:
                    expand_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for button in expand_buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                # 检查是否是展开按钮（未展开状态）
                                aria_expanded = button.get_attribute('aria-expanded')
                                if aria_expanded == 'false':
                                    self.driver.execute_script("arguments[0].click();", button)
                                    expanded_count += 1
                                    time.sleep(0.5)  # 等待展开动画
                                    
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            if expanded_count > 0:
                self.logger.info(f"✅ 展开了 {expanded_count} 个折叠项目")
                time.sleep(2)  # 等待所有展开动画完成
            else:
                self.logger.info("ℹ️ 没有找到需要展开的折叠项目")
                
        except Exception as e:
            self.logger.warning(f"展开折叠项目时出错: {e}")