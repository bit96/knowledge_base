#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书文档自动下载器
自动化批量下载飞书文档并记录下载信息
"""

import os
import csv
import json
import time
import random
import logging
import threading
import base64
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import pandas as pd
from hotkey_controller import HotkeyController, DownloadState
from floating_ui import FloatingUI


class FeishuDownloader:
    def __init__(self, download_dir: str = "/Users/abc/PycharmProjects/knowledge_base/.venv/output", 
                 debug_mode: bool = False):
        self.download_dir = download_dir
        self.debug_mode = debug_mode
        self.csv_file = "download_log.csv"
        self.progress_file = "progress.json"
        self.log_file = "download.log"
        self.screenshot_dir = os.path.join(download_dir, "debug_screenshots")
        
        # 初始化日志
        self.setup_logging()
        
        # 初始化下载统计
        self.stats = {
            "total_processed": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "skipped_documents": 0
        }
        
        # 批次计数器
        self.batch_counter = 0
        
        # Chrome驱动
        self.driver = None
        
        # 快捷键控制器
        self.hotkey_controller = None
        self.floating_ui = None
        
        # 控制标志
        self._stop_requested = False
        self._control_lock = threading.Lock()
        
        # 调试配置
        self.debug_config = {
            "save_screenshots": debug_mode,
            "detailed_logging": debug_mode,
            "interactive_mode": False,
            "max_links_to_analyze": 50
        }
        
        # 确保输出目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        if debug_mode:
            os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 初始化CSV文件
        self.init_csv_file()
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def init_csv_file(self):
        """初始化CSV记录文件"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['文档标题', 'URL', '下载时间', '状态'])
            self.logger.info(f"创建CSV记录文件: {self.csv_file}")
    
    def save_progress(self, current_index: int, document_list: List[Dict]):
        """保存当前进度"""
        progress_data = {
            "current_index": current_index,
            "total_documents": len(document_list),
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def load_progress(self) -> Optional[Dict]:
        """加载上次进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"无法加载进度文件: {e}")
        return None
    
    def setup_chrome_driver(self):
        """设置Chrome浏览器驱动 - 增强版"""
        try:
            self.logger.info("正在设置Chrome浏览器连接...")
            
            # 基础Chrome选项
            chrome_options = Options()
            
            # 优化Chrome性能和稳定性
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            
            # 修复连接池问题
            chrome_options.add_argument("--max-connections-per-host=10")
            chrome_options.add_argument("--max-concurrent-tab-loads=4")
            
            # 设置下载目录
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                # 禁用图片加载以提高速度（可选）
                "profile.managed_default_content_settings.images": 2 if not self.debug_mode else 1,
                # 禁用通知
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 尝试连接到现有Chrome会话
            success = False
            
            # 方式1: 连接到调试端口9222
            if not success:
                success = self._try_connect_debug_port(chrome_options, "9222")
            
            # 方式2: 尝试其他常用端口
            if not success:
                for port in ["9223", "9224", "9225"]:
                    if self._try_connect_debug_port(chrome_options, port):
                        success = True
                        break
            
            # 方式3: 启动新的Chrome会话
            if not success:
                success = self._start_new_chrome_session(chrome_options)
            
            if not success:
                raise Exception("无法创建或连接Chrome会话")
            
            # 设置等待时间和连接参数
            self.driver.implicitly_wait(5)  # 减少隐式等待时间
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            
            # 测试连接稳定性
            self._test_chrome_connection()
            
            # 初始化浮动UI
            self.floating_ui = FloatingUI(self.driver)
            
            self.logger.info("✅ Chrome浏览器设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Chrome驱动设置失败: {e}")
            if self.debug_mode:
                import traceback
                self.logger.error(traceback.format_exc())
            return False
    
    def _try_connect_debug_port(self, chrome_options: Options, port: str) -> bool:
        """尝试连接到指定调试端口"""
        try:
            debug_options = Options()
            # 复制基础选项
            for arg in chrome_options.arguments:
                debug_options.add_argument(arg)
            for key, value in chrome_options.experimental_options.items():
                debug_options.add_experimental_option(key, value)
            
            # 设置调试地址
            debug_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            
            self.driver = webdriver.Chrome(options=debug_options)
            self.logger.info(f"✅ 成功连接到现有Chrome会话 (端口 {port})")
            return True
            
        except WebDriverException as e:
            self.logger.debug(f"端口 {port} 连接失败: {e}")
            return False
        except Exception as e:
            self.logger.debug(f"端口 {port} 连接出错: {e}")
            return False
    
    def _start_new_chrome_session(self, chrome_options: Options) -> bool:
        """启动新的Chrome会话"""
        try:
            self.logger.info("启动新的Chrome会话...")
            
            # 清除调试地址选项
            new_options = Options()
            for arg in chrome_options.arguments:
                new_options.add_argument(arg)
            
            # 只保留非debuggerAddress的选项
            for key, value in chrome_options.experimental_options.items():
                if key != "debuggerAddress":
                    new_options.add_experimental_option(key, value)
            
            self.driver = webdriver.Chrome(options=new_options)
            self.logger.info("✅ 新Chrome会话启动成功")
            self.logger.warning("⚠️  请确保在新打开的浏览器中登录飞书账号并导航到文档列表页面")
            return True
            
        except Exception as e:
            self.logger.error(f"启动新Chrome会话失败: {e}")
            return False
    
    def _test_chrome_connection(self):
        """测试Chrome连接稳定性"""
        try:
            # 测试基本操作
            current_url = self.driver.current_url
            title = self.driver.title
            
            self.logger.debug(f"Chrome连接测试通过 - URL: {current_url[:50]}...")
            self.logger.debug(f"页面标题: {title[:30]}...")
            
            # 测试JavaScript执行
            ready_state = self.driver.execute_script("return document.readyState")
            self.logger.debug(f"页面状态: {ready_state}")
            
        except Exception as e:
            self.logger.warning(f"Chrome连接测试失败: {e}")
            raise
    
    def repair_chrome_connection(self) -> bool:
        """修复Chrome连接"""
        try:
            self.logger.info("尝试修复Chrome连接...")
            
            # 测试当前连接
            if self.driver:
                try:
                    self.driver.current_url
                    self.logger.info("Chrome连接正常，无需修复")
                    return True
                except:
                    self.logger.warning("检测到Chrome连接问题，重新建立连接")
            
            # 重新设置连接
            old_driver = self.driver
            self.driver = None
            
            if old_driver:
                try:
                    old_driver.quit()
                except:
                    pass
            
            # 重新建立连接
            success = self.setup_chrome_driver()
            
            if success:
                self.logger.info("✅ Chrome连接修复成功")
            else:
                self.logger.error("❌ Chrome连接修复失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Chrome连接修复过程中出错: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = 30):
        """等待页面完全加载"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # 额外等待确保动态内容加载完成
            time.sleep(random.uniform(2, 4))
            return True
        except TimeoutException:
            self.logger.warning("页面加载超时")
            return False
    
    def wait_for_dynamic_content(self, timeout: int = 30) -> bool:
        """智能等待动态内容加载"""
        try:
            # 1. 等待DOM完成
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 2. 等待可能的AJAX请求完成
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return window.jQuery ? jQuery.active == 0 : true")
            )
            
            # 3. 等待React/Vue组件渲染（检查是否有loading状态）
            try:
                WebDriverWait(self.driver, 5).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "[class*='loading'], [class*='spinner'], [class*='skeleton']"))
                )
            except TimeoutException:
                pass  # 没有loading元素是正常的
            
            # 4. 额外等待确保内容稳定
            time.sleep(random.uniform(1, 3))
            
            self.logger.debug("动态内容加载完成")
            return True
            
        except TimeoutException:
            self.logger.warning("动态内容加载超时，继续执行")
            return False
        except Exception as e:
            self.logger.warning(f"等待动态内容时出错: {e}")
            return False
    
    def take_screenshot(self, filename_suffix: str = "") -> Optional[str]:
        """保存页面截图用于调试"""
        if not self.debug_config["save_screenshots"] or not self.driver:
            return None
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"debug_{timestamp}_{filename_suffix}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            self.driver.save_screenshot(filepath)
            self.logger.debug(f"截图已保存: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.warning(f"截图保存失败: {e}")
            return None
    
    def diagnose_page(self) -> Dict:
        """诊断当前页面，输出调试信息"""
        try:
            # 基本页面信息
            current_url = self.driver.current_url
            page_title = self.driver.title
            page_source_length = len(self.driver.page_source)
            
            # URL分析
            parsed_url = urlparse(current_url)
            domain = parsed_url.netloc
            path = parsed_url.path
            
            # 检测页面类型
            page_type = self._detect_page_type(current_url, page_title)
            
            # 分析页面中的所有链接
            all_links = self._analyze_all_links()
            
            # 检测可能的文档容器
            containers = self._detect_document_containers()
            
            # 保存截图
            screenshot_path = self.take_screenshot("page_diagnosis")
            
            diagnosis = {
                "timestamp": datetime.now().isoformat(),
                "url": current_url,
                "domain": domain,
                "path": path,
                "title": page_title,
                "page_type": page_type,
                "page_source_length": page_source_length,
                "total_links": len(all_links),
                "potential_doc_links": len([link for link in all_links if self._is_potential_doc_link(link)]),
                "containers_found": len(containers),
                "screenshot": screenshot_path,
                "link_patterns": self._analyze_link_patterns(all_links),
                "containers": containers[:5],  # 只保存前5个容器信息
                "sample_links": all_links[:10]  # 只保存前10个链接作为样本
            }
            
            # 输出诊断信息
            self._print_diagnosis(diagnosis)
            
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"页面诊断失败: {e}")
            return {"error": str(e)}
    
    def _detect_page_type(self, url: str, title: str) -> str:
        """检测页面类型"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if '/wiki/' in url_lower or 'wiki' in title_lower:
            return "知识库/Wiki页面"
        elif '/docs/' in url_lower or '/docx/' in url_lower:
            return "文档页面"
        elif '/sheets/' in url_lower:
            return "表格页面"
        elif '/space/' in url_lower:
            return "空间页面"
        elif '/drive/' in url_lower or '/file/' in url_lower:
            return "文件驱动器页面"
        elif 'feishu' in url_lower or 'lark' in url_lower:
            return "飞书页面"
        else:
            return "未知页面类型"
    
    def _analyze_all_links(self) -> List[Dict]:
        """分析页面中的所有链接"""
        try:
            links = []
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in elements[:self.debug_config["max_links_to_analyze"]]:
                try:
                    href = element.get_attribute('href')
                    text = element.text.strip()
                    title = element.get_attribute('title') or ""
                    
                    if href:
                        links.append({
                            "href": href,
                            "text": text,
                            "title": title,
                            "is_visible": element.is_displayed(),
                            "tag_name": element.tag_name
                        })
                except:
                    continue
                    
            return links
            
        except Exception as e:
            self.logger.warning(f"链接分析失败: {e}")
            return []
    
    def _detect_document_containers(self) -> List[Dict]:
        """检测可能包含文档的容器元素"""
        try:
            containers = []
            
            # 常见的容器选择器
            container_selectors = [
                "[class*='file']",
                "[class*='doc']",
                "[class*='item']",
                "[class*='list']",
                "[class*='table']",
                "[data-testid]",
                ".lark-table-row",
                ".file-list-item"
            ]
            
            for selector in container_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        container_info = {
                            "selector": selector,
                            "count": len(elements),
                            "visible_count": len([e for e in elements if e.is_displayed()]),
                            "sample_text": elements[0].text.strip()[:100] if elements else ""
                        }
                        containers.append(container_info)
                except:
                    continue
                    
            return containers
            
        except Exception as e:
            self.logger.warning(f"容器检测失败: {e}")
            return []
    
    def _is_potential_doc_link(self, link: Dict) -> bool:
        """判断是否为潜在的文档链接"""
        href = link.get("href", "").lower()
        text = link.get("text", "").lower()
        
        # URL模式检测
        doc_patterns = [
            r'/docs?/', r'/docx/', r'/sheets?/', r'/wiki/', 
            r'/file/', r'/document/', r'/space/'
        ]
        
        if any(re.search(pattern, href) for pattern in doc_patterns):
            return True
            
        # 文本模式检测
        if any(keyword in text for keyword in ['文档', 'doc', '表格', 'sheet', '演示']):
            return True
            
        return False
    
    def _analyze_link_patterns(self, links: List[Dict]) -> Dict:
        """分析链接模式"""
        patterns = {}
        
        for link in links:
            href = link.get("href", "")
            if href:
                # 提取域名和路径模式
                try:
                    parsed = urlparse(href)
                    domain = parsed.netloc
                    path_parts = [part for part in parsed.path.split('/') if part]
                    
                    if domain:
                        patterns.setdefault("domains", {}).setdefault(domain, 0)
                        patterns["domains"][domain] += 1
                    
                    if path_parts:
                        first_part = path_parts[0]
                        patterns.setdefault("path_patterns", {}).setdefault(first_part, 0)
                        patterns["path_patterns"][first_part] += 1
                        
                except:
                    continue
                    
        return patterns
    
    def _print_diagnosis(self, diagnosis: Dict):
        """打印诊断信息"""
        if not self.debug_config["detailed_logging"]:
            return
            
        self.logger.info("=" * 60)
        self.logger.info("📋 页面诊断报告")
        self.logger.info("=" * 60)
        self.logger.info(f"🔗 URL: {diagnosis.get('url')}")
        self.logger.info(f"📄 标题: {diagnosis.get('title')}")
        self.logger.info(f"🏷️  页面类型: {diagnosis.get('page_type')}")
        self.logger.info(f"📊 页面源码长度: {diagnosis.get('page_source_length')} 字符")
        self.logger.info(f"🔗 总链接数: {diagnosis.get('total_links')}")
        self.logger.info(f"📄 潜在文档链接: {diagnosis.get('potential_doc_links')}")
        self.logger.info(f"📦 容器数量: {diagnosis.get('containers_found')}")
        
        if diagnosis.get('screenshot'):
            self.logger.info(f"📸 截图: {diagnosis.get('screenshot')}")
        
        # 链接模式信息
        patterns = diagnosis.get('link_patterns', {})
        if patterns.get('domains'):
            self.logger.info("🌐 域名分布:")
            for domain, count in sorted(patterns['domains'].items(), key=lambda x: x[1], reverse=True)[:5]:
                self.logger.info(f"   {domain}: {count} 个链接")
        
        if patterns.get('path_patterns'):
            self.logger.info("🛤️  路径模式:")
            for path, count in sorted(patterns['path_patterns'].items(), key=lambda x: x[1], reverse=True)[:5]:
                self.logger.info(f"   /{path}/: {count} 个链接")
        
        # 容器信息
        containers = diagnosis.get('containers', [])
        if containers:
            self.logger.info("📦 发现的容器:")
            for container in containers[:3]:
                self.logger.info(f"   {container['selector']}: {container['visible_count']}/{container['count']} 可见")
        
        self.logger.info("=" * 60)
    
    def get_document_links(self) -> List[Dict]:
        """获取当前页面的文档链接列表 - 增强版"""
        try:
            # 使用智能等待
            if not self.wait_for_dynamic_content():
                self.logger.warning("页面动态内容加载可能未完成，继续尝试...")
            
            # 如果启用调试模式，先进行页面诊断
            if self.debug_mode:
                diagnosis = self.diagnose_page()
                self.logger.info(f"页面诊断完成，发现 {diagnosis.get('potential_doc_links', 0)} 个潜在文档链接")
            
            # 多策略查找文档链接
            document_links = []
            
            # 策略1: 增强版选择器查找
            document_links.extend(self._find_links_by_enhanced_selectors())
            
            # 策略2: 智能链接分析
            if not document_links:
                document_links.extend(self._find_links_by_intelligent_analysis())
            
            # 策略3: 通用链接过滤（兜底方案）
            if not document_links:
                document_links.extend(self._find_links_by_pattern_matching())
            
            # 去重和验证
            document_links = self._deduplicate_and_validate_links(document_links)
            
            if document_links:
                self.logger.info(f"✅ 成功找到 {len(document_links)} 个文档链接")
                if self.debug_config["detailed_logging"]:
                    self._log_found_links(document_links)
            else:
                self.logger.error("❌ 未找到任何文档链接")
                if self.debug_mode:
                    self._suggest_troubleshooting()
                
            return document_links
            
        except Exception as e:
            self.logger.error(f"获取文档链接失败: {e}")
            if self.debug_mode:
                self.take_screenshot("get_links_error")
            return []
    
    def _find_links_by_enhanced_selectors(self) -> List[Dict]:
        """策略1: 使用增强版选择器查找"""
        document_links = []
        
        # 2024年最新飞书界面选择器
        enhanced_selectors = [
            # 新版飞书文档链接模式
            "a[href*='/wiki/']", "a[href*='/space/']", "a[href*='/file/']",
            "a[href*='/document/']", "a[href*='/base/']",
            
            # 传统文档链接
            "a[href*='/docs/']", "a[href*='/docx/']", "a[href*='/sheets/']",
            
            # React/Vue组件选择器
            "[data-testid*='file']", "[data-testid*='document']", "[data-testid*='doc']",
            "[data-testid*='wiki']", "[data-testid*='space']",
            
            # 新版UI组件类名
            ".lark-table-row a", ".file-list-item a", ".doc-list-item a",
            ".wiki-list-item a", ".space-item a",
            
            # 通用容器内的链接
            "[class*='file'] a", "[class*='doc'] a", "[class*='item'] a",
            "[class*='list'] a[href]", "[class*='table'] a[href]",
            
            # Ant Design / 其他UI框架
            ".ant-table-row a", ".ant-list-item a",
            
            # 自定义属性
            "[role='row'] a", "[role='gridcell'] a", "[role='link'][href]"
        ]
        
        for selector in enhanced_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    found_links = []
                    for element in elements:
                        link_info = self._extract_link_info(element)
                        if link_info and self._is_valid_document_link(link_info):
                            found_links.append(link_info)
                    
                    if found_links:
                        self.logger.info(f"选择器 '{selector}' 找到 {len(found_links)} 个有效链接")
                        document_links.extend(found_links)
                        # 找到有效链接就停止（优先级策略）
                        if len(document_links) >= 5:  # 找到足够的链接就停止
                            break
                        
            except Exception as e:
                self.logger.debug(f"选择器 '{selector}' 执行失败: {e}")
                continue
        
        return document_links
    
    def _find_links_by_intelligent_analysis(self) -> List[Dict]:
        """策略2: 智能分析页面中的所有链接"""
        try:
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            document_links = []
            
            self.logger.info(f"开始智能分析 {len(all_links)} 个链接...")
            
            for element in all_links:
                try:
                    link_info = self._extract_link_info(element)
                    if link_info and self._is_potential_document_link_advanced(link_info):
                        document_links.append(link_info)
                except:
                    continue
            
            if document_links:
                self.logger.info(f"智能分析找到 {len(document_links)} 个文档链接")
            
            return document_links
            
        except Exception as e:
            self.logger.warning(f"智能链接分析失败: {e}")
            return []
    
    def _find_links_by_pattern_matching(self) -> List[Dict]:
        """策略3: 通用模式匹配（兜底方案）"""
        try:
            # 获取所有链接进行模式匹配
            all_links = self.driver.find_elements(By.XPATH, "//a[@href]")
            document_links = []
            
            self.logger.info(f"执行兜底方案，分析 {len(all_links)} 个链接的模式...")
            
            for element in all_links:
                try:
                    href = element.get_attribute('href')
                    if href and self._matches_document_url_pattern(href):
                        link_info = self._extract_link_info(element)
                        if link_info:
                            document_links.append(link_info)
                except:
                    continue
            
            if document_links:
                self.logger.info(f"模式匹配找到 {len(document_links)} 个可能的文档链接")
            
            return document_links
            
        except Exception as e:
            self.logger.warning(f"模式匹配失败: {e}")
            return []
    
    def _extract_link_info(self, element) -> Optional[Dict]:
        """提取链接信息"""
        try:
            href = element.get_attribute('href')
            if not href:
                return None
                
            text = element.text.strip()
            title = element.get_attribute('title') or ""
            aria_label = element.get_attribute('aria-label') or ""
            
            # 合并所有可用的文本信息
            display_text = text or title or aria_label or "未知文档"
            
            return {
                'title': display_text,
                'url': href,
                'element': element,
                'text': text,
                'title_attr': title,
                'aria_label': aria_label,
                'is_visible': element.is_displayed(),
                'tag_name': element.tag_name
            }
            
        except Exception:
            return None
    
    def _is_valid_document_link(self, link_info: Dict) -> bool:
        """验证是否为有效的文档链接"""
        href = link_info.get('url', '').lower()
        text = link_info.get('title', '').lower()
        
        # 排除明显不是文档的链接
        exclude_patterns = [
            'javascript:', 'mailto:', '#', 'tel:',
            '/login', '/logout', '/settings', '/profile',
            '.jpg', '.png', '.gif', '.pdf', '.mp4'
        ]
        
        if any(pattern in href for pattern in exclude_patterns):
            return False
        
        # 必须是可见的链接（除非是调试模式）
        if not self.debug_mode and not link_info.get('is_visible', False):
            return False
        
        # 必须有一定长度的URL
        if len(href) < 10:
            return False
            
        # 必须有文本内容或者匹配文档URL模式
        if not text and not self._matches_document_url_pattern(href):
            return False
        
        return True
    
    def _is_potential_document_link_advanced(self, link_info: Dict) -> bool:
        """高级文档链接判断"""
        href = link_info.get('url', '').lower()
        text = link_info.get('title', '').lower()
        
        # 先进行基础验证
        if not self._is_valid_document_link(link_info):
            return False
        
        # URL模式匹配 - 更全面的模式
        doc_url_patterns = [
            r'/wiki/', r'/docs?/', r'/docx/', r'/sheets?/', r'/base/',
            r'/file/', r'/document/', r'/space/', r'/drive/',
            r'/knowledge/', r'/kb/', r'/pages?/'
        ]
        
        url_match = any(re.search(pattern, href) for pattern in doc_url_patterns)
        
        # 文本内容匹配
        text_keywords = [
            '文档', 'document', 'doc', '表格', 'sheet', 'excel',
            'wiki', '知识', 'knowledge', '演示', 'presentation',
            '笔记', 'note', '页面', 'page'
        ]
        
        text_match = any(keyword in text for keyword in text_keywords)
        
        # 综合判断
        if url_match:
            return True
        if text_match and len(text) > 2:
            return True
        
        # 特殊情况：飞书域名下的链接给予额外权重
        if any(domain in href for domain in ['feishu.cn', 'larksuite.com', 'bytedance.net']):
            return url_match or text_match
        
        return False
    
    def _matches_document_url_pattern(self, url: str) -> bool:
        """检查URL是否匹配文档模式"""
        url_lower = url.lower()
        
        # 飞书文档URL模式
        feishu_patterns = [
            r'feishu\.cn/wiki/',
            r'feishu\.cn/docs?/',
            r'feishu\.cn/sheets?/',
            r'feishu\.cn/file/',
            r'feishu\.cn/base/',
            r'larksuite\.com/wiki/',
            r'larksuite\.com/docs?/',
        ]
        
        return any(re.search(pattern, url_lower) for pattern in feishu_patterns)
    
    def _deduplicate_and_validate_links(self, links: List[Dict]) -> List[Dict]:
        """去重和最终验证链接"""
        seen_urls = set()
        unique_links = []
        
        for link in links:
            url = link.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_links.append(link)
        
        self.logger.debug(f"去重后保留 {len(unique_links)} 个唯一链接")
        return unique_links
    
    def _log_found_links(self, links: List[Dict]):
        """记录找到的链接详情"""
        self.logger.info("📋 发现的文档链接:")
        for i, link in enumerate(links[:10], 1):  # 只显示前10个
            title = link.get('title', '')[:50] + ('...' if len(link.get('title', '')) > 50 else '')
            url = link.get('url', '')[:80] + ('...' if len(link.get('url', '')) > 80 else '')
            self.logger.info(f"   {i}. {title}")
            self.logger.info(f"      {url}")
        
        if len(links) > 10:
            self.logger.info(f"   ... 还有 {len(links) - 10} 个链接")
    
    def _suggest_troubleshooting(self):
        """提供故障排除建议"""
        self.logger.info("🔧 故障排除建议:")
        self.logger.info("1. 确认当前页面是飞书文档列表页面")
        self.logger.info("2. 检查页面是否完全加载（等待动画结束）")
        self.logger.info("3. 尝试手动滚动页面加载更多内容")
        self.logger.info("4. 检查是否需要登录或权限")
        self.logger.info("5. 查看调试截图了解页面状态")
        
        current_url = self.driver.current_url if self.driver else "未知"
        self.logger.info(f"当前URL: {current_url}")
        
        # 保存额外的调试截图
        self.take_screenshot("troubleshooting")
    
    def download_document(self, doc_info: Dict) -> bool:
        """下载单个文档"""
        max_retries = 3
        retry_interval = 60  # 1分钟
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始下载文档: {doc_info['title']} (尝试 {attempt + 1}/{max_retries})")
                
                # 点击文档链接进入详情页
                if 'element' in doc_info:
                    # 滚动到元素可见
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", doc_info['element'])
                    time.sleep(1)
                    
                    # 点击链接
                    doc_info['element'].click()
                else:
                    # 直接导航到URL
                    self.driver.get(doc_info['url'])
                
                # 等待文档页面加载
                if not self.wait_for_page_load():
                    raise TimeoutException("文档页面加载超时")
                
                # 获取实际的文档标题和URL
                actual_title = self.driver.title
                actual_url = self.driver.current_url
                
                # 查找并点击更多操作按钮（三个点）
                more_button_selectors = [
                    "[data-testid='more-actions']",
                    ".more-actions-btn",
                    "[aria-label*='更多']",
                    "button[title*='更多']",
                    ".header-more-btn",
                    "button:has(svg):last-child"  # 最后一个包含SVG的按钮
                ]
                
                more_button = None
                for selector in more_button_selectors:
                    try:
                        more_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not more_button:
                    raise NoSuchElementException("未找到更多操作按钮")
                
                # 点击更多按钮
                more_button.click()
                time.sleep(1)
                
                # 查找并点击下载选项
                download_selectors = [
                    "[data-testid='download']",
                    "button:contains('下载')",
                    "a:contains('下载')",
                    "[aria-label*='下载']",
                    ".download-btn"
                ]
                
                download_button = None
                for selector in download_selectors:
                    try:
                        download_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not download_button:
                    raise NoSuchElementException("未找到下载按钮")
                
                # 点击下载按钮
                download_button.click()
                time.sleep(2)
                
                # 选择下载格式（根据文档类型）
                self.select_download_format()
                
                # 等待下载开始
                time.sleep(3)
                
                # 记录成功下载
                self.record_download(actual_title, actual_url, "成功")
                self.stats["successful_downloads"] += 1
                
                self.logger.info(f"文档下载成功: {actual_title}")
                
                # 返回到列表页面
                self.driver.back()
                self.wait_for_page_load()
                
                return True
                
            except Exception as e:
                self.logger.warning(f"文档下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"等待 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                    # 确保回到列表页面
                    try:
                        self.driver.back()
                        self.wait_for_page_load()
                    except:
                        pass
                else:
                    # 最后一次尝试失败，记录失败
                    self.record_download(doc_info['title'], doc_info.get('url', ''), "失败")
                    self.stats["failed_downloads"] += 1
                    return False
        
        return False
    
    def select_download_format(self):
        """根据文档类型选择下载格式"""
        try:
            # 查找格式选择选项
            format_selectors = [
                "button:contains('Word')",
                "button:contains('Excel')", 
                "button:contains('PDF')",
                "[data-format='docx']",
                "[data-format='xlsx']",
                "[data-format='pdf']"
            ]
            
            # 默认选择第一个可用格式
            for selector in format_selectors:
                try:
                    format_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    format_button.click()
                    self.logger.debug(f"选择下载格式: {selector}")
                    return
                except TimeoutException:
                    continue
            
            # 如果没有找到特定格式，尝试点击第一个下载选项
            self.logger.debug("使用默认下载格式")
            
        except Exception as e:
            self.logger.debug(f"格式选择失败，使用默认格式: {e}")
    
    def record_download(self, title: str, url: str, status: str):
        """记录下载信息到CSV"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([title, url, timestamp, status])
                
        except Exception as e:
            self.logger.error(f"记录下载信息失败: {e}")
    
    def _on_start_callback(self):
        """启动回调函数"""
        with self._control_lock:
            self._stop_requested = False
        self.logger.info("收到启动信号，开始自动化操作")
        if self.floating_ui:
            self.floating_ui.update_status(DownloadState.RUNNING)
    
    def _on_stop_callback(self):
        """停止回调函数"""
        with self._control_lock:
            self._stop_requested = True
        self.logger.info("收到停止信号，暂停自动化操作")
        if self.floating_ui:
            self.floating_ui.update_status(DownloadState.STOPPED)
    
    def _is_stop_requested(self) -> bool:
        """检查是否请求停止"""
        with self._control_lock:
            return self._stop_requested
    
    def _wait_for_start_or_stop(self, timeout: Optional[float] = None) -> bool:
        """等待启动信号，如果收到停止信号则返回False"""
        if not self.hotkey_controller:
            return True  # 没有控制器时默认继续
        
        start_time = time.time()
        while True:
            if self.hotkey_controller.is_running():
                return True
            if self._is_stop_requested():
                return False
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)
    
    def anti_crawl_delay(self):
        """防反爬延迟"""
        base_delay = 10  # 基础延迟10秒
        random_delay = random.uniform(0, 20)  # 随机0-20秒
        total_delay = base_delay + random_delay
        
        self.logger.info(f"防反爬延迟: {total_delay:.1f} 秒")
        time.sleep(total_delay)
        
        # 检查是否需要批次休息
        self.batch_counter += 1
        if self.batch_counter >= 100:
            self.logger.info("已处理100个文档，休息30分钟...")
            time.sleep(30 * 60)  # 30分钟
            self.batch_counter = 0
    
    def run(self, start_index: int = 0, enable_hotkeys: bool = True):
        """运行主下载流程 - 增强版"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🚀 飞书文档自动下载器 v2.0 启动")
            self.logger.info("=" * 60)
            
            if self.debug_mode:
                self.logger.info("🔧 调试模式已启用")
                self.logger.info(f"📸 截图保存目录: {self.screenshot_dir}")
            
            # 设置Chrome驱动（增强版）
            if not self.setup_chrome_driver():
                self.logger.error("❌ Chrome驱动设置失败")
                if self.debug_mode:
                    self._interactive_debug_chrome_issue()
                return
            
            # 初始化快捷键控制器
            if enable_hotkeys:
                self.hotkey_controller = HotkeyController(
                    on_start_callback=self._on_start_callback,
                    on_stop_callback=self._on_stop_callback
                )
                self.hotkey_controller.start_listening()
                self.logger.info("🎮 快捷键控制已启用: 双击空格键启动，ESC键停止")
            
            # 注入悬浮UI并设置为准备状态
            if self.floating_ui:
                self.floating_ui.inject_ui()
                self.floating_ui.update_status(DownloadState.READY)
                self.logger.info("🎛️ 悬浮状态UI已激活")
            
            self.logger.info(f"📁 下载目录: {self.download_dir}")
            
            # 获取文档列表（增强版）
            self.logger.info("🔍 正在扫描文档列表...")
            document_links = self.get_document_links()
            
            if not document_links:
                self.logger.error("❌ 未找到可下载的文档")
                if self.debug_mode:
                    self._interactive_debug_no_links()
                return
            
            self.logger.info(f"✅ 发现 {len(document_links)} 个文档")
            
            # 调试模式下的交互式确认
            if self.debug_mode and self.debug_config.get("interactive_mode", False):
                if not self._interactive_confirm_links(document_links):
                    self.logger.info("用户取消操作")
                    return
            
            if enable_hotkeys:
                self.logger.info("⏳ 等待用户操作...")
                self.logger.info("   双击空格键开始下载，ESC键可随时停止")
                
                # 等待启动信号
                if not self._wait_for_start_or_stop():
                    self.logger.info("用户取消操作")
                    return
            
            self.logger.info("🚀 开始批量下载...")
            
            # 从指定索引开始处理
            for i in range(start_index, len(document_links)):
                # 检查停止请求和连接状态
                if enable_hotkeys and self._is_stop_requested():
                    self.logger.info(f"⏸️  用户停止操作，已处理 {i}/{len(document_links)} 个文档")
                    break
                
                # 检查Chrome连接状态
                if not self._check_and_repair_connection():
                    self.logger.error("Chrome连接无法修复，终止下载")
                    break
                
                doc_info = document_links[i]
                self.logger.info(f"📄 处理文档 {i+1}/{len(document_links)}: {doc_info['title'][:50]}...")
                
                # 检查UI并修复（如果页面刷新）
                if self.floating_ui:
                    self.floating_ui.check_and_repair()
                
                # 保存进度
                self.save_progress(i, document_links)
                
                # 下载文档（带增强错误处理）
                success = self._download_document_with_recovery(doc_info)
                self.stats["total_processed"] += 1
                
                if success:
                    self.logger.info(f"✅ 文档 {i+1} 下载成功")
                else:
                    self.logger.error(f"❌ 文档 {i+1} 下载失败")
                    if self.debug_mode:
                        self.take_screenshot(f"download_failed_{i}")
                
                # 防反爬延迟（除了最后一个文档）
                if i < len(document_links) - 1:
                    self.anti_crawl_delay()
                    
                    # 在延迟过程中检查是否要求停止
                    if enable_hotkeys and self._is_stop_requested():
                        self.logger.info("⏸️  在延迟过程中收到停止信号")
                        break
                
                # 如果停止状态下等待重新启动
                if enable_hotkeys and self.hotkey_controller and self.hotkey_controller.is_stopped():
                    self.logger.info("⏸️  等待用户重新启动...")
                    if not self._wait_for_start_or_stop():
                        self.logger.info("用户确认停止")
                        break
            
            # 输出最终统计
            self.print_final_stats()
            
        except KeyboardInterrupt:
            self.logger.info("⏸️  用户中断下载")
            self.print_final_stats()
        except Exception as e:
            self.logger.error(f"💥 运行时错误: {e}")
            if self.debug_mode:
                import traceback
                self.logger.error(traceback.format_exc())
                self.take_screenshot("runtime_error")
            raise
        finally:
            # 清理资源
            self._cleanup_resources()
    
    def _interactive_debug_chrome_issue(self):
        """交互式调试Chrome连接问题"""
        self.logger.info("🔧 Chrome连接问题交互式调试:")
        self.logger.info("1. 请检查Chrome是否在调试模式运行:")
        self.logger.info("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        self.logger.info("2. 检查端口9222是否被占用")
        self.logger.info("3. 尝试重启Chrome浏览器")
        
        try:
            response = input("\n是否要我尝试其他端口? (y/n): ").strip().lower()
            if response == 'y':
                for port in ["9223", "9224", "9225"]:
                    self.logger.info(f"尝试端口 {port}...")
                    if self._try_connect_debug_port(Options(), port):
                        self.logger.info(f"✅ 端口 {port} 连接成功!")
                        return
                self.logger.error("❌ 所有端口都无法连接")
        except (EOFError, KeyboardInterrupt):
            self.logger.info("跳过交互式调试")
    
    def _interactive_debug_no_links(self):
        """交互式调试无法找到链接的问题"""
        self.logger.info("🔧 无法找到文档链接 - 交互式调试:")
        
        try:
            response = input("\n是否要查看页面详细信息? (y/n): ").strip().lower()
            if response == 'y':
                diagnosis = self.diagnose_page()
                self.logger.info("页面诊断完成，请查看上方的诊断报告")
                
                response = input("\n是否要启用交互模式手动确认链接? (y/n): ").strip().lower()
                if response == 'y':
                    self.debug_config["interactive_mode"] = True
                    self.logger.info("✅ 交互模式已启用")
                    
        except (EOFError, KeyboardInterrupt):
            self.logger.info("跳过交互式调试")
    
    def _interactive_confirm_links(self, document_links: List[Dict]) -> bool:
        """交互式确认找到的链接"""
        try:
            self.logger.info("🔍 交互式链接确认模式:")
            self.logger.info(f"发现 {len(document_links)} 个潜在文档链接:")
            
            for i, link in enumerate(document_links[:10], 1):
                title = link.get('title', '').strip()[:50]
                url = link.get('url', '')[:60]
                self.logger.info(f"  {i}. {title}")
                self.logger.info(f"     {url}")
            
            if len(document_links) > 10:
                self.logger.info(f"  ... 还有 {len(document_links) - 10} 个链接")
            
            response = input("\n这些链接看起来正确吗? (y/n): ").strip().lower()
            return response == 'y'
            
        except (EOFError, KeyboardInterrupt):
            return False
    
    def _check_and_repair_connection(self) -> bool:
        """检查并修复Chrome连接"""
        try:
            if self.driver:
                # 简单的连接测试
                self.driver.current_url
                return True
        except:
            self.logger.warning("检测到Chrome连接问题，尝试修复...")
            return self.repair_chrome_connection()
        
        return False
    
    def _download_document_with_recovery(self, doc_info: Dict) -> bool:
        """带恢复机制的文档下载"""
        max_connection_retries = 2
        
        for attempt in range(max_connection_retries):
            try:
                return self.download_document(doc_info)
            except WebDriverException as e:
                if "disconnected" in str(e).lower() or "connection" in str(e).lower():
                    self.logger.warning(f"连接中断 (尝试 {attempt + 1}/{max_connection_retries}), 尝试修复...")
                    if attempt < max_connection_retries - 1:
                        if self.repair_chrome_connection():
                            continue
                        else:
                            break
                else:
                    raise
            except Exception as e:
                self.logger.error(f"下载过程中出现非连接错误: {e}")
                break
        
        return False
    
    def _cleanup_resources(self):
        """清理资源"""
        self.logger.info("🧹 清理资源...")
        
        if self.hotkey_controller:
            try:
                self.hotkey_controller.stop_listening()
                self.logger.debug("快捷键监听已停止")
            except:
                pass
        
        if self.floating_ui:
            try:
                self.floating_ui.remove_ui()
                self.logger.debug("悬浮UI已移除")
            except:
                pass
        
        # 不关闭浏览器，保持会话
        if self.driver:
            self.logger.info("💡 Chrome会话保持开启状态")
        
        self.logger.info("✅ 资源清理完成")
    
    def print_final_stats(self):
        """打印最终统计信息"""
        self.logger.info("=" * 50)
        self.logger.info("下载完成统计:")
        self.logger.info(f"总处理数量: {self.stats['total_processed']}")
        self.logger.info(f"成功下载: {self.stats['successful_downloads']}")
        self.logger.info(f"下载失败: {self.stats['failed_downloads']}")
        self.logger.info(f"跳过文档: {self.stats['skipped_documents']}")
        self.logger.info(f"CSV记录文件: {self.csv_file}")
        self.logger.info(f"下载目录: {self.download_dir}")
        self.logger.info("=" * 50)


def main():
    """主函数 - 增强版"""
    print("🚀 飞书文档自动下载器 v2.0 - 增强调试版")
    print("=" * 60)
    
    # 检查是否需要调试模式
    debug_mode = False
    try:
        import sys
        if "--debug" in sys.argv or "-d" in sys.argv:
            debug_mode = True
            print("🔧 调试模式已启用")
        elif "--help" in sys.argv or "-h" in sys.argv:
            print_help()
            return
    except:
        pass
    
    # 初始化下载器
    downloader = FeishuDownloader(debug_mode=debug_mode)
    
    # 检查是否有之前的进度
    progress = downloader.load_progress()
    start_index = 0
    
    if progress:
        print(f"📋 发现上次中断的进度:")
        print(f"   已处理: {progress['current_index']}/{progress['total_documents']}")
        
        try:
            response = input("\n是否继续上次的下载? (y/n): ").strip().lower()
            if response == 'y':
                start_index = progress['current_index']
                downloader.stats = progress.get('stats', downloader.stats)
                print(f"✅ 从第 {start_index + 1} 个文档继续下载")
            else:
                print("🔄 将从头开始下载")
        except EOFError:
            # 非交互式环境，默认继续上次进度
            start_index = progress['current_index']
            downloader.stats = progress.get('stats', downloader.stats)
            print(f"🤖 非交互式环境，自动从第 {start_index + 1} 个文档继续下载")
    
    # 显示功能说明
    print("\n✨ v2.0 增强功能:")
    print("🎮 快捷键控制 - 双击空格键启动，ESC键停止")
    print("🎛️  状态显示 - 页面左上角悬浮框实时显示状态")
    print("🔍 智能识别 - 多策略文档链接识别")
    print("🔧 故障诊断 - 自动页面诊断和截图")
    print("🛡️  连接修复 - 自动检测和修复Chrome连接")
    
    if debug_mode:
        print("\n🔧 调试模式功能:")
        print("📸 自动截图 - 失败时自动保存页面截图")
        print("📋 详细日志 - 显示详细的调试信息")
        print("🔍 页面诊断 - 自动分析页面结构和链接")
        print("💬 交互调试 - 问题出现时提供交互式调试选项")
    
    print("\n📋 使用前请确保:")
    print("1. ✅ Chrome浏览器已登录飞书账号")
    print("2. ✅ 当前页面为需要下载的文档列表页面")
    print("3. ✅ 网络连接正常稳定")
    
    if debug_mode:
        print("4. 🔧 如遇问题将自动启用调试功能")
    
    try:
        response = input("\n按回车键启动程序 (或输入 'q' 退出): ").strip()
        if response.lower() == 'q':
            print("👋 程序退出")
            return
    except EOFError:
        print("\n🤖 检测到非交互式环境，自动启动程序...")
    
    print("\n" + "=" * 60)
    print("🚀 程序启动中...")
    print("=" * 60)
    
    try:
        # 运行下载器
        downloader.run(start_index)
    except KeyboardInterrupt:
        print("\n⏸️  用户中断程序")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        if debug_mode:
            import traceback
            print("\n🔍 详细错误信息:")
            traceback.print_exc()
            print(f"\n📸 错误截图可能已保存到: {downloader.screenshot_dir}")
        else:
            print("💡 提示: 使用 --debug 参数可获得更详细的错误信息")

def print_help():
    """打印帮助信息"""
    print("🚀 飞书文档自动下载器 v2.0")
    print("=" * 50)
    print("用法:")
    print("  python3 feishu_downloader2.py [选项]")
    print()
    print("选项:")
    print("  --debug, -d    启用调试模式")
    print("  --help, -h     显示此帮助信息")
    print()
    print("调试模式功能:")
    print("  📸 自动截图保存")
    print("  📋 详细日志输出")
    print("  🔍 页面结构分析")
    print("  💬 交互式问题诊断")
    print("  🛡️  增强错误恢复")
    print()
    print("快捷键:")
    print("  双击空格键  - 启动/继续下载")
    print("  ESC键       - 暂停下载")
    print("  Ctrl+C      - 退出程序")
    print()
    print("使用步骤:")
    print("1. 启动Chrome调试模式:")
    print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print("2. 在Chrome中登录飞书并导航到文档列表页面")
    print("3. 运行此程序")
    print("4. 双击空格键开始下载")
    print()
    print("输出文件:")
    print("  download_log.csv     - 下载记录")
    print("  download.log         - 详细日志")
    print("  progress.json        - 进度文件")
    print("  debug_screenshots/   - 调试截图 (调试模式)")
    print("=" * 50)


if __name__ == "__main__":
    main()