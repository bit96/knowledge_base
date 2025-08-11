#!/usr/bin/env python3
"""
飞书知识库目录遍历器
基于test_word_click_fix_fast3.py，自动遍历左侧目录树并记录页面信息

主要特性:
- 严格的访问频率控制（2-5秒延迟）
- 权限检查和尊重机制
- 智能目录识别和展开
- 详细的访问日志记录
- 容错和重试机制
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import csv
import json
import random
from datetime import datetime
from typing import List, Dict, Set, Optional
import logging


class FeishuDirectoryTraverser:
    def __init__(self, output_dir: str = "/Users/abc/PycharmProjects/knowledge_base/output"):
        self.output_dir = output_dir
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
        
        # 设置日志
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志记录"""
        log_file = os.path.join(self.output_dir, "traverser.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """设置WebDriver - 复用fast3的逻辑"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # 检查是否在正确的页面
            current_url = self.driver.current_url
            if 'feishu' not in current_url and 'lark' not in current_url:
                self.logger.warning("当前页面可能不是飞书页面，请确认")
            
            self.logger.info(f"✅ 成功连接Chrome，当前页面: {self.driver.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Chrome连接失败: {e}")
            return False
    
    def wait_with_respect(self):
        """尊重性访问等待 - 2-5秒随机延迟"""
        delay = random.uniform(*self.access_delay)
        self.logger.info(f"⏳ 尊重访问频率，等待 {delay:.1f} 秒...")
        time.sleep(delay)
        return delay
    
    def check_access_permission(self) -> bool:
        """检查页面访问权限"""
        try:
            # 检查URL是否包含权限相关关键词
            current_url = self.driver.current_url.lower()
            forbidden_url_indicators = [
                'login', 'signin', 'auth', '403', 'forbidden', 'denied'
            ]
            
            if any(indicator in current_url for indicator in forbidden_url_indicators):
                return False
            
            # 检查页面内容是否包含权限相关信息
            try:
                page_source = self.driver.page_source.lower()
                forbidden_content_indicators = [
                    '403', 'forbidden', '权限不足', '登录', 'login',
                    '需要权限', 'access denied', '无权访问', '权限错误',
                    'permission denied', '未授权', 'unauthorized'
                ]
                
                if any(indicator in page_source for indicator in forbidden_content_indicators):
                    return False
                
            except Exception:
                # 如果无法获取页面源码，假设有权限
                pass
            
            # 检查页面标题
            try:
                title = self.driver.title.lower()
                if any(indicator in title for indicator in ['登录', 'login', '错误', 'error', '403']):
                    return False
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            self.logger.warning(f"权限检查时出错: {e}")
            return True  # 出错时假设有权限，避免误判
    
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
    
    def click_directory_item(self, item: Dict) -> bool:
        """点击目录项并等待页面加载"""
        try:
            element = item['element']
            item_name = item['name']
            is_clickable_node = item.get('is_clickable_node', False)
            
            self.logger.info(f"🖱️ 点击项目: {item_name}")
            
            # 滚动到元素可见位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 对于可点击节点（目录树节点），使用特殊的点击策略
            if is_clickable_node:
                try:
                    # 对于目录树节点，可能需要点击父元素或特定的点击区域
                    parent_element = element.find_element(By.XPATH, "..")
                    
                    # 尝试点击节点本身或其父容器
                    click_targets = [element, parent_element]
                    
                    for target in click_targets:
                        try:
                            if target.is_displayed() and target.is_enabled():
                                self.driver.execute_script("arguments[0].click();", target)
                                time.sleep(2)  # 等待目录节点响应
                                
                                # 检查是否有页面变化或新内容加载
                                current_url_after = self.driver.current_url
                                if current_url_after != self.driver.current_url:
                                    return True
                                    
                                # 检查页面标题是否改变
                                time.sleep(1)
                                return True
                                
                        except Exception:
                            continue
                            
                except Exception:
                    pass
            
            # 传统的链接点击方法
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform()
            ]
            
            for method in click_methods:
                try:
                    method()
                    time.sleep(1)  # 等待页面开始加载
                    break
                except Exception:
                    continue
            else:
                self.logger.warning(f"所有点击方法都失败: {item_name}")
                return False
            
            # 等待页面加载完成
            try:
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(1)  # 额外等待确保内容加载
                return True
            except TimeoutException:
                self.logger.warning(f"页面加载超时: {item_name}")
                return True  # 即使超时也继续，可能页面已部分加载
                
        except Exception as e:
            self.logger.error(f"点击目录项失败: {e}")
            return False
    
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
    
    def recursive_traverse_directory(self, level: int = 0, visited_texts: Set[str] = None):
        """递归遍历多层级目录结构"""
        if visited_texts is None:
            visited_texts = set()
        
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
                
                self.logger.info(f"{indent}📄 [{level + 1}-{i}] 处理: {item_name}")
                
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
                    
                    # 提取并记录页面信息
                    page_info = self.extract_page_info()
                    if page_info:
                        page_info['directory_item'] = item_name
                        page_info['level'] = level + 1
                        page_info['index'] = len(self.access_log) + 1
                        
                        self.access_log.append(page_info)
                        self.stats["successful_access"] = self.stats.get("successful_access", 0) + 1
                        
                        self.logger.info(f"{indent}✅ 成功记录: {current_title[:50]}...")
                    
                    # 递归检查是否有更深层的目录（延迟一点时间让DOM稳定）
                    time.sleep(1)
                    deeper_items = self.find_sidebar_items_fresh()
                    
                    # 如果发现了新的更深层项目，递归遍历
                    if len(deeper_items) > len(current_items):
                        self.logger.info(f"{indent}🔍 发现更深层目录，开始递归...")
                        self.recursive_traverse_directory(level + 1, visited_texts)
                    
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
            xpath = f"//*[@class='workspace-tree-view-node-content' and text()='{text}']"
            elements = self.driver.find_elements(By.XPATH, xpath)
            
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return element
            
            return None
            
        except Exception as e:
            self.logger.debug(f"根据文本查找元素失败: {e}")
            return None
    
    def click_element_safe(self, element, item_name: str) -> bool:
        """安全点击元素，包含多种重试策略"""
        try:
            # 滚动到元素可见位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 尝试多种点击方法
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
                # 尝试点击父元素
                lambda: self.driver.execute_script("arguments[0].click();", element.find_element(By.XPATH, ".."))
            ]
            
            for i, method in enumerate(click_methods):
                try:
                    method()
                    time.sleep(1)
                    return True
                except Exception as e:
                    if i == len(click_methods) - 1:
                        self.logger.debug(f"点击方法 {i+1} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"安全点击元素失败: {e}")
            return False
    
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
                    '序号', '目录项名称', '页面标题', 'URL', 
                    '访问时间', '响应时间(秒)', '状态'
                ])
                
                # 写入数据行
                for item in self.access_log:
                    writer.writerow([
                        item.get('index', ''),
                        item.get('directory_item', ''),
                        item.get('title', ''),
                        item.get('url', ''),
                        item.get('timestamp', ''),
                        item.get('response_time', ''),
                        '成功'
                    ])
            
            self.logger.info(f"📄 CSV文件已保存: {csv_file}")
            self.logger.info(f"   包含 {len(self.access_log)} 条成功访问记录")
            
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")
    
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
                    f.write(f"   链接: {item['href']}\n")
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


def main():
    print("🚀 飞书知识库目录遍历器 v1.0")
    print("基于 test_word_click_fix_fast3.py 架构开发")
    print("="*60)
    
    print("✨ 主要特性:")
    print("  🕒 严格的访问频率控制 (2-5秒延迟)")
    print("  🛡️ 自动权限检查和尊重机制")
    print("  🔍 智能左侧目录识别")
    print("  📊 详细的统计和日志记录")
    print("  💾 多格式数据输出 (CSV/JSON/TXT)")
    print()
    
    print("📋 使用前请确保:")
    print("1. ✅ Chrome调试模式运行中 (端口9222)")
    print("2. ✅ 已登录飞书账号")
    print("3. ✅ 当前页面是【知识库的文件列表页面】，而不是单个文档页面")
    print("4. ✅ 左侧有完整的目录树结构，包含多个文档链接")
    print("5. ✅ 网络连接稳定")
    print()
    
    print("🎯 正确的页面特征:")
    print("  • 页面显示多个文档/文件的列表")
    print("  • 左侧有目录树，包含文件夹和文档")
    print("  • URL通常是知识库主页，不包含'?'参数")
    print("  • 页面中有几十个或更多的文档链接")
    print()
    
    print("⚠️ 重要提醒:")
    print("  • 程序将严格遵循2-5秒访问间隔")
    print("  • 自动跳过无权限访问的页面")
    print("  • 过程中可随时按 Ctrl+C 安全中断")
    print("  • 结果将保存到指定的output目录")
    print()
    
    print("⚠️ 最后确认: 请确认您当前在【知识库目录页面】，而不是单个文档页面")
    
    try:
        response = input("🚀 确认页面正确后，按回车键开始遍历 (输入 'q' 退出): ").strip()
        if response.lower() == 'q':
            print("👋 程序退出")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n👋 程序退出")
        return
    
    print("\n" + "="*60)
    print("🚀 开始遍历...")
    print("="*60)
    
    # 记录总开始时间
    total_start_time = time.time()
    
    # 创建遍历器实例
    traverser = FeishuDirectoryTraverser()
    
    try:
        # 设置Chrome连接
        print("🔧 正在连接Chrome...")
        if not traverser.setup_driver():
            print("❌ Chrome连接失败")
            print("\n💡 解决建议:")
            print("1. 确保Chrome以调试模式启动:")
            print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
            print("2. 检查端口9222是否被占用")
            print("3. 重启Chrome浏览器")
            return
        
        # 开始遍历
        print("🎯 开始目录遍历...")
        traverser.traverse_all_items()
        
        # 计算总耗时
        total_duration = time.time() - total_start_time
        
        # 最终结果展示
        print("\n" + "🎉"*20)
        print("遍历任务完成！")
        print("🎉"*20)
        
        print(f"\n📊 最终统计:")
        print(f"   ✅ 成功访问: {traverser.stats['successful_access']} 个页面")
        print(f"   ⚠️ 权限限制: {traverser.stats['permission_denied']} 个页面")
        print(f"   ❌ 访问失败: {traverser.stats['access_failed']} 个页面")
        print(f"   ⏱️ 总耗时: {traverser.format_duration(total_duration)}")
        
        if traverser.stats['successful_access'] > 0:
            success_rate = (traverser.stats['successful_access'] / traverser.stats['total_items_found']) * 100
            print(f"   📈 成功率: {success_rate:.1f}%")
        
        print(f"\n📁 结果文件位置:")
        print(f"   📂 {traverser.output_dir}")
        print(f"   📄 主要数据: directory_traverse_log.csv")
        print(f"   📊 统计摘要: traverse_summary.json")
        
        print(f"\n💡 提示:")
        print(f"   • 可以使用Excel或其他工具打开CSV文件查看结果")
        print(f"   • JSON文件包含完整的统计信息")
        print(f"   • 日志文件记录了详细的执行过程")
        
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断遍历")
        print("📊 部分结果已保存")
        if traverser.stats.get('successful_access', 0) > 0:
            print(f"✅ 已成功记录 {traverser.stats['successful_access']} 个页面")
            print(f"📁 结果保存在: {traverser.output_dir}")
        
    except Exception as e:
        print(f"\n❌ 遍历过程中出错: {e}")
        print("\n🔍 错误详情:")
        import traceback
        traceback.print_exc()
        
        print(f"\n💡 可能的解决方案:")
        print("1. 检查Chrome连接状态")
        print("2. 确认页面是否正确加载")
        print("3. 检查网络连接")
        print("4. 查看详细日志文件获取更多信息")
    
    finally:
        print(f"\n📝 详细日志保存在: {traverser.output_dir}/traverser.log")


if __name__ == "__main__":
    main()