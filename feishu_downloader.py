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
from datetime import datetime
from typing import List, Dict, Optional
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
    def __init__(self, download_dir: str = "/Users/abc/PycharmProjects/knowledge_base/.venv/output"):
        self.download_dir = download_dir
        self.csv_file = "download_log.csv"
        self.progress_file = "progress.json"
        self.log_file = "download.log"
        
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
        
        # 确保输出目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
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
        """设置Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            
            # 设置下载目录
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 连接到现有Chrome会话（如果可用）
            try:
                # 尝试连接到调试端口
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("成功连接到现有Chrome会话")
            except WebDriverException:
                # 如果无法连接现有会话，启动新会话
                self.logger.info("无法连接现有Chrome会话，启动新会话")
                chrome_options = Options()
                chrome_options.add_experimental_option("prefs", prefs)
                self.driver = webdriver.Chrome(options=chrome_options)
                self.logger.warning("请确保在新打开的浏览器中登录飞书账号")
                
            # 设置等待时间
            self.driver.implicitly_wait(10)
            
            # 初始化浮动UI
            self.floating_ui = FloatingUI(self.driver)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome驱动设置失败: {e}")
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
    
    def get_document_links(self) -> List[Dict]:
        """获取当前页面的文档链接列表"""
        try:
            self.wait_for_page_load()
            
            # 飞书文档列表的常见选择器（需要根据实际页面调整）
            possible_selectors = [
                "a[href*='/docs/']",  # 包含docs的链接
                "a[href*='/docx/']",  # 包含docx的链接  
                "a[href*='/sheets/']", # 包含sheets的链接
                ".file-item a",       # 文件项链接
                ".doc-item a",        # 文档项链接
                "[data-testid*='doc'] a"  # 测试ID包含doc的链接
            ]
            
            document_links = []
            
            for selector in possible_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            href = element.get_attribute('href')
                            text = element.text.strip()
                            
                            if href and text:
                                document_links.append({
                                    'title': text,
                                    'url': href,
                                    'element': element
                                })
                        
                        if document_links:
                            self.logger.info(f"使用选择器 {selector} 找到 {len(document_links)} 个文档")
                            break
                            
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 查找失败: {e}")
                    continue
            
            if not document_links:
                self.logger.warning("未找到文档链接，请检查页面是否为文档列表页面")
                
            return document_links
            
        except Exception as e:
            self.logger.error(f"获取文档链接失败: {e}")
            return []
    
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
        """运行主下载流程"""
        try:
            # 设置Chrome驱动
            if not self.setup_chrome_driver():
                self.logger.error("Chrome驱动设置失败")
                return
            
            # 初始化快捷键控制器
            if enable_hotkeys:
                self.hotkey_controller = HotkeyController(
                    on_start_callback=self._on_start_callback,
                    on_stop_callback=self._on_stop_callback
                )
                self.hotkey_controller.start_listening()
                self.logger.info("快捷键控制已启用: 双击空格键启动，ESC键停止")
            
            # 注入悬浮UI并设置为准备状态
            if self.floating_ui:
                self.floating_ui.inject_ui()
                self.floating_ui.update_status(DownloadState.READY)
            
            self.logger.info("飞书文档自动下载器启动")
            self.logger.info(f"下载目录: {self.download_dir}")
            
            # 获取文档列表
            self.logger.info("正在获取文档列表...")
            document_links = self.get_document_links()
            
            if not document_links:
                self.logger.error("未找到可下载的文档")
                return
            
            self.logger.info(f"找到 {len(document_links)} 个文档")
            
            if enable_hotkeys:
                self.logger.info("等待用户操作...")
                self.logger.info("双击空格键开始下载，ESC键可随时停止")
                
                # 等待启动信号
                if not self._wait_for_start_or_stop():
                    self.logger.info("用户取消操作")
                    return
            
            # 从指定索引开始处理
            for i in range(start_index, len(document_links)):
                # 检查停止请求
                if enable_hotkeys and self._is_stop_requested():
                    self.logger.info(f"用户停止操作，已处理 {i}/{len(document_links)} 个文档")
                    break
                
                doc_info = document_links[i]
                self.logger.info(f"处理文档 {i+1}/{len(document_links)}: {doc_info['title']}")
                
                # 检查UI并修复（如果页面刷新）
                if self.floating_ui:
                    self.floating_ui.check_and_repair()
                
                # 保存进度
                self.save_progress(i, document_links)
                
                # 下载文档
                success = self.download_document(doc_info)
                self.stats["total_processed"] += 1
                
                if success:
                    self.logger.info(f"✓ 文档 {i+1} 下载成功")
                else:
                    self.logger.error(f"✗ 文档 {i+1} 下载失败")
                
                # 防反爬延迟（除了最后一个文档）
                if i < len(document_links) - 1:
                    self.anti_crawl_delay()
                    
                    # 在延迟过程中检查是否要求停止
                    if enable_hotkeys and self._is_stop_requested():
                        self.logger.info("在延迟过程中收到停止信号")
                        break
                
                # 如果停止状态下等待重新启动
                if enable_hotkeys and self.hotkey_controller.is_stopped():
                    self.logger.info("等待用户重新启动...")
                    if not self._wait_for_start_or_stop():
                        self.logger.info("用户确认停止")
                        break
            
            # 输出最终统计
            self.print_final_stats()
            
        except KeyboardInterrupt:
            self.logger.info("用户中断下载")
            self.print_final_stats()
        except Exception as e:
            self.logger.error(f"运行时错误: {e}")
            raise
        finally:
            # 清理资源
            if self.hotkey_controller:
                self.hotkey_controller.stop_listening()
            if self.floating_ui:
                self.floating_ui.remove_ui()
            if self.driver:
                self.logger.info("清理资源...")
                # 不关闭浏览器，保持会话
                # self.driver.quit()
    
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
    """主函数"""
    print("飞书文档自动下载器 v2.0 - 快捷键控制版")
    print("=" * 60)
    
    # 初始化下载器
    downloader = FeishuDownloader()
    
    # 检查是否有之前的进度
    progress = downloader.load_progress()
    start_index = 0
    
    if progress:
        print(f"发现上次中断的进度:")
        print(f"已处理: {progress['current_index']}/{progress['total_documents']}")
        
        try:
            response = input("是否继续上次的下载? (y/n): ").strip().lower()
            if response == 'y':
                start_index = progress['current_index']
                downloader.stats = progress.get('stats', downloader.stats)
                print(f"从第 {start_index + 1} 个文档继续下载")
        except EOFError:
            # 非交互式环境，默认继续上次进度
            start_index = progress['current_index']
            downloader.stats = progress.get('stats', downloader.stats)
            print(f"非交互式环境，自动从第 {start_index + 1} 个文档继续下载")
    
    # 新版使用说明
    print("\n✨ 新功能 - 快捷键控制:")
    print("📍 双击空格键 - 启动/重启自动化下载")
    print("⏹️  按ESC键 - 停止自动化下载")
    print("🎛️  状态显示 - 页面左上角悬浮框实时显示状态")
    print()
    
    # 确认开始
    print("请确保:")
    print("1. Chrome浏览器已登录飞书账号")
    print("2. 当前页面为需要下载的文档列表页面")
    print("3. 网络连接正常")
    
    try:
        input("\n按回车键启动程序...")
    except EOFError:
        print("\n检测到非交互式环境，自动启动程序...")
    
    try:
        # 运行下载器
        downloader.run(start_index)
    except Exception as e:
        print(f"程序异常退出: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()