#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版悬浮UI管理器 - 解决字符编码问题
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from hotkey_controller import DownloadState


class FloatingUISimple:
    """简化版浏览器悬浮UI管理器"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self._ui_injected = False
        self._current_state = None
    
    def inject_ui(self):
        """注入悬浮UI到页面"""
        if self._ui_injected:
            return
        
        try:
            # 分步骤创建，避免复杂字符串
            
            # 1. 清理旧UI
            self.driver.execute_script("""
                var old = document.getElementById('status-ui');
                if (old) old.remove();
            """)
            
            # 2. 创建容器
            self.driver.execute_script("""
                var div = document.createElement('div');
                div.id = 'status-ui';
                div.style.cssText = 'position:fixed;top:20px;left:20px;z-index:999999;background:#3498db;color:white;padding:12px 20px;border-radius:8px;font-size:14px;font-weight:600;min-width:100px;text-align:center;';
                document.body.appendChild(div);
            """)
            
            # 3. 设置初始内容
            self.driver.execute_script("""
                var el = document.getElementById('status-ui');
                if (el) el.textContent = arguments[0];
            """, "🔧 准备")
            
            self._ui_injected = True
            self.logger.info("悬浮UI注入成功")
            
        except Exception as e:
            self.logger.error(f"悬浮UI注入失败: {e}")
    
    def update_status(self, state: DownloadState):
        """更新状态显示"""
        if not self._ui_injected:
            self.inject_ui()
        
        if self._current_state == state:
            return
        
        try:
            # 状态配置
            config = {
                DownloadState.READY: {'text': '🔧 准备', 'color': '#3498db'},
                DownloadState.RUNNING: {'text': '🚀 启动', 'color': '#27ae60'},
                DownloadState.STOPPED: {'text': '⏹️ 停止', 'color': '#e74c3c'}
            }
            
            state_info = config.get(state)
            if not state_info:
                return
            
            # 更新UI
            self.driver.execute_script("""
                var el = document.getElementById('status-ui');
                if (el) {
                    el.textContent = arguments[0];
                    el.style.background = arguments[1];
                }
            """, state_info['text'], state_info['color'])
            
            self._current_state = state
            self.logger.debug(f"状态显示更新为: {state.value}")
            
        except Exception as e:
            self.logger.error(f"状态更新失败: {e}")
    
    def remove_ui(self):
        """移除悬浮UI"""
        try:
            self.driver.execute_script("""
                var el = document.getElementById('status-ui');
                if (el) el.remove();
            """)
            self._ui_injected = False
            self._current_state = None
            self.logger.info("悬浮UI已移除")
        except Exception as e:
            self.logger.error(f"移除悬浮UI失败: {e}")
    
    def is_injected(self):
        """检查UI是否已注入"""
        return self._ui_injected


# 测试代码
if __name__ == "__main__":
    import time
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("简化版悬浮UI测试...")
        
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        ui = FloatingUISimple(driver)
        
        print("注入UI...")
        ui.inject_ui()
        
        # 测试状态切换
        states = [DownloadState.READY, DownloadState.RUNNING, DownloadState.STOPPED]
        
        for state in states:
            print(f"更新状态: {state.value}")
            ui.update_status(state)
            time.sleep(3)
        
        print("测试完成，5秒后清理...")
        time.sleep(5)
        ui.remove_ui()
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()