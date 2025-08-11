#!/usr/bin/env python3
"""
初始化模块
处理系统初始化、Chrome连接、日志配置等
"""

import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class InitializationMixin:
    """初始化功能混入类"""
    
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