#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局快捷键控制器
实现全局快捷键监听和状态管理
"""

import time
import threading
from enum import Enum
from typing import Callable, Optional
from pynput import keyboard
import logging


class DownloadState(Enum):
    """下载器状态枚举"""
    READY = "准备"      # 脚本启动，等待用户操作
    RUNNING = "启动"    # 正在执行自动化下载
    STOPPED = "停止"    # 自动化操作已停止


class HotkeyController:
    """全局快捷键控制器"""
    
    def __init__(self, on_start_callback: Optional[Callable] = None, 
                 on_stop_callback: Optional[Callable] = None):
        self.logger = logging.getLogger(__name__)
        
        # 状态管理
        self._state = DownloadState.READY
        self._state_lock = threading.Lock()
        
        # 回调函数
        self.on_start_callback = on_start_callback
        self.on_stop_callback = on_stop_callback
        
        # 快捷键监听相关
        self._listener = None
        self._running = False
        
        # 空格键连击检测
        self._space_press_count = 0
        self._last_space_time = 0
        self._double_press_interval = 0.5  # 500ms内连击有效
        
    @property
    def state(self) -> DownloadState:
        """获取当前状态"""
        with self._state_lock:
            return self._state
    
    def _set_state(self, new_state: DownloadState):
        """设置新状态"""
        with self._state_lock:
            if self._state != new_state:
                old_state = self._state
                self._state = new_state
                self.logger.info(f"状态切换: {old_state.value} → {new_state.value}")
    
    def _on_key_press(self, key):
        """键盘按下事件处理"""
        try:
            current_time = time.time()
            
            # 处理空格键连击
            if key == keyboard.Key.space:
                if current_time - self._last_space_time <= self._double_press_interval:
                    self._space_press_count += 1
                else:
                    self._space_press_count = 1
                
                self._last_space_time = current_time
                
                # 检测双击空格
                if self._space_press_count == 2:
                    self._handle_start_command()
                    self._space_press_count = 0
            
            # 处理ESC键
            elif key == keyboard.Key.esc:
                self._handle_stop_command()
                
        except Exception as e:
            self.logger.error(f"按键处理错误: {e}")
    
    def _handle_start_command(self):
        """处理启动命令"""
        current_state = self.state
        
        if current_state in [DownloadState.READY, DownloadState.STOPPED]:
            self._set_state(DownloadState.RUNNING)
            self.logger.info("检测到双击空格键 - 启动自动化操作")
            
            # 执行启动回调
            if self.on_start_callback:
                try:
                    self.on_start_callback()
                except Exception as e:
                    self.logger.error(f"启动回调执行失败: {e}")
        else:
            self.logger.warning(f"当前状态 {current_state.value} 不允许启动操作")
    
    def _handle_stop_command(self):
        """处理停止命令"""
        current_state = self.state
        
        if current_state == DownloadState.RUNNING:
            self._set_state(DownloadState.STOPPED)
            self.logger.info("检测到ESC键 - 停止自动化操作")
            
            # 执行停止回调
            if self.on_stop_callback:
                try:
                    self.on_stop_callback()
                except Exception as e:
                    self.logger.error(f"停止回调执行失败: {e}")
        else:
            self.logger.warning(f"当前状态 {current_state.value} 不允许停止操作")
    
    def start_listening(self):
        """开始监听快捷键"""
        if self._running:
            self.logger.warning("快捷键监听已经在运行")
            return
        
        try:
            self._running = True
            self._listener = keyboard.Listener(on_press=self._on_key_press)
            self._listener.start()
            self.logger.info("全局快捷键监听已启动")
            self.logger.info("操作说明: 双击空格键启动，ESC键停止")
            
        except Exception as e:
            self._running = False
            self.logger.error(f"快捷键监听启动失败: {e}")
            raise
    
    def stop_listening(self):
        """停止监听快捷键"""
        if not self._running:
            return
        
        try:
            self._running = False
            if self._listener:
                self._listener.stop()
                self._listener = None
            self.logger.info("全局快捷键监听已停止")
            
        except Exception as e:
            self.logger.error(f"停止快捷键监听失败: {e}")
    
    def reset_to_ready(self):
        """重置状态到准备状态"""
        self._set_state(DownloadState.READY)
    
    def is_running(self) -> bool:
        """检查是否处于运行状态"""
        return self.state == DownloadState.RUNNING
    
    def is_stopped(self) -> bool:
        """检查是否处于停止状态"""
        return self.state == DownloadState.STOPPED
    
    def wait_for_start(self, timeout: Optional[float] = None) -> bool:
        """等待启动信号"""
        start_time = time.time()
        
        while self.state != DownloadState.RUNNING:
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)
        
        return True
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_listening()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop_listening()


# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    def on_start():
        print("🚀 启动回调被触发!")
    
    def on_stop():
        print("⏹️ 停止回调被触发!")
    
    # 创建控制器
    controller = HotkeyController(on_start, on_stop)
    
    try:
        print("快捷键测试程序启动...")
        print("操作说明:")
        print("- 双击空格键: 启动")
        print("- 按ESC键: 停止") 
        print("- Ctrl+C: 退出测试")
        print()
        
        with controller:
            # 保持程序运行
            while True:
                print(f"当前状态: {controller.state.value}")
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n测试程序退出")