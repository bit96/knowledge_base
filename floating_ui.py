#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器悬浮UI管理器
在浏览器页面添加状态显示悬浮框
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from hotkey_controller import DownloadState


class FloatingUI:
    """浏览器悬浮UI管理器"""
    
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
            # 使用DOM创建方式避免字符串编码问题
            self.driver.execute_script("""
                // 移除旧的UI
                var oldStatus = document.getElementById('feishu-downloader-status');
                var oldStyle = document.getElementById('feishu-downloader-style');
                if (oldStatus) oldStatus.remove();
                if (oldStyle) oldStyle.remove();
                
                // 创建样式
                var style = document.createElement('style');
                style.id = 'feishu-downloader-style';
                style.textContent = `
                    #feishu-downloader-status {
                        position: fixed;
                        top: 20px;
                        left: 20px;
                        z-index: 999999;
                        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                        color: white;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        font-size: 14px;
                        font-weight: 600;
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                        min-width: 120px;
                        text-align: center;
                        user-select: none;
                        pointer-events: none;
                        transition: all 0.3s ease;
                    }
                    
                    #feishu-downloader-status.ready {
                        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                    }
                    
                    #feishu-downloader-status.running {
                        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
                        animation: pulse 2s infinite;
                    }
                    
                    #feishu-downloader-status.stopped {
                        background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
                    }
                    
                    @keyframes pulse {
                        0% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); }
                        50% { box-shadow: 0 8px 32px rgba(0, 184, 148, 0.4); }
                        100% { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); }
                    }
                `;
                document.head.appendChild(style);
                
                // 创建状态框
                var statusDiv = document.createElement('div');
                statusDiv.id = 'feishu-downloader-status';
                statusDiv.className = 'ready';
                
                var iconSpan = document.createElement('span');
                iconSpan.className = 'status-icon';
                iconSpan.style.display = 'inline-block';
                iconSpan.style.marginRight = '8px';
                iconSpan.style.fontSize = '16px';
                iconSpan.textContent = '🔧';
                
                var textSpan = document.createElement('span');
                textSpan.className = 'status-text';
                textSpan.textContent = '准备';
                
                statusDiv.appendChild(iconSpan);
                statusDiv.appendChild(textSpan);
                document.body.appendChild(statusDiv);
                
                return 'UI注入成功';
            """)
            
            self._ui_injected = True
            self.logger.info("悬浮UI注入成功")
            
        except Exception as e:
            self.logger.error(f"悬浮UI注入失败: {e}")
    
    def update_status(self, state: DownloadState):
        """更新状态显示"""
        if not self._ui_injected:
            self.inject_ui()
        
        if self._current_state == state:
            return  # 状态未变化，无需更新
        
        try:
            # 状态映射
            state_config = {
                DownloadState.READY: {
                    'class': 'ready',
                    'icon': '🔧',
                    'text': '准备'
                },
                DownloadState.RUNNING: {
                    'class': 'running', 
                    'icon': '🚀',
                    'text': '启动'
                },
                DownloadState.STOPPED: {
                    'class': 'stopped',
                    'icon': '⏹️',
                    'text': '停止'
                }
            }
            
            config = state_config.get(state)
            if not config:
                self.logger.warning(f"未知状态: {state}")
                return
            
            # 更新UI
            self.driver.execute_script("""
                var statusElement = document.getElementById('feishu-downloader-status');
                if (statusElement) {
                    statusElement.className = arguments[0];
                    statusElement.querySelector('.status-icon').textContent = arguments[1];
                    statusElement.querySelector('.status-text').textContent = arguments[2];
                }
            """, config['class'], config['icon'], config['text'])
            
            self._current_state = state
            self.logger.debug(f"状态显示更新为: {state.value}")
            
        except WebDriverException as e:
            self.logger.error(f"状态更新失败: {e}")
            # 尝试重新注入UI
            self._ui_injected = False
            self.inject_ui()
            self.update_status(state)  # 递归重试一次
        except Exception as e:
            self.logger.error(f"状态更新异常: {e}")
    
    def remove_ui(self):
        """移除悬浮UI"""
        if not self._ui_injected:
            return
        
        try:
            self.driver.execute_script("""
                var statusElement = document.getElementById('feishu-downloader-status');
                var styleElement = document.getElementById('feishu-downloader-style');
                if (statusElement) statusElement.remove();
                if (styleElement) styleElement.remove();
            """)
            
            self._ui_injected = False
            self._current_state = None
            self.logger.info("悬浮UI已移除")
            
        except Exception as e:
            self.logger.error(f"移除悬浮UI失败: {e}")
    
    def is_injected(self) -> bool:
        """检查UI是否已注入"""
        return self._ui_injected
    
    def check_and_repair(self):
        """检查并修复UI（如果页面刷新导致UI丢失）"""
        try:
            # 检查UI元素是否存在
            ui_exists = self.driver.execute_script("""
                return document.getElementById('feishu-downloader-status') !== null;
            """)
            
            if not ui_exists and self._ui_injected:
                self.logger.info("检测到UI丢失，重新注入")
                self._ui_injected = False
                self.inject_ui()
                if self._current_state:
                    self.update_status(self._current_state)
                    
        except Exception as e:
            self.logger.error(f"UI检查修复失败: {e}")


# 测试代码  
if __name__ == "__main__":
    import time
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("浮动UI测试程序启动...")
        
        # 连接Chrome
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 创建UI管理器
        ui = FloatingUI(driver)
        
        print("注入悬浮UI...")
        ui.inject_ui()
        
        # 测试状态切换
        states = [DownloadState.READY, DownloadState.RUNNING, DownloadState.STOPPED]
        
        for i, state in enumerate(states * 2):  # 重复两轮
            print(f"更新状态为: {state.value}")
            ui.update_status(state)
            time.sleep(3)
        
        print("测试完成，5秒后移除UI...")
        time.sleep(5)
        ui.remove_ui()
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()