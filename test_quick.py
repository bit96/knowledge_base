#!/usr/bin/env python3
"""
快速测试新功能
"""
import os
import sys

def test_imports():
    """测试导入"""
    print("测试模块导入...")
    
    try:
        from hotkey_controller import HotkeyController, DownloadState
        print("✅ hotkey_controller 导入成功")
    except Exception as e:
        print(f"❌ hotkey_controller 导入失败: {e}")
        return False
    
    try:
        from floating_ui import FloatingUI
        print("✅ floating_ui 导入成功")
    except Exception as e:
        print(f"❌ floating_ui 导入失败: {e}")
        return False
    
    try:
        import pynput
        print("✅ pynput 库导入成功")
    except Exception as e:
        print(f"❌ pynput 库导入失败: {e}")
        print("请运行: pip install pynput")
        return False
    
    try:
        from feishu_downloader import FeishuDownloader
        print("✅ feishu_downloader 导入成功")
    except Exception as e:
        print(f"❌ feishu_downloader 导入失败: {e}")
        return False
    
    return True

def test_chrome_connection():
    """测试Chrome连接"""
    print("\n测试Chrome连接...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome连接成功")
        print(f"当前页面: {driver.title}")
        print(f"URL: {driver.current_url}")
        
        # 不关闭浏览器
        return True
        
    except Exception as e:
        print(f"❌ Chrome连接失败: {e}")
        print("请确保:")
        print("1. Chrome调试模式已启动")
        print("2. 运行命令: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        return False

def main():
    print("飞书下载器快捷键功能 - 快速测试")
    print("=" * 40)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print(f"❌ Python版本过低: {sys.version}")
        print("需要Python 3.8或更高版本")
        return
    
    print(f"✅ Python版本: {sys.version}")
    
    # 测试导入
    if not test_imports():
        print("\n❌ 模块导入测试失败")
        return
    
    # 测试Chrome连接
    if not test_chrome_connection():
        print("\n❌ Chrome连接测试失败")
        return
    
    print("\n" + "=" * 40)
    print("🎉 快速测试通过!")
    print("可以运行主程序: python3 feishu_downloader.py")
    print("或运行完整测试: python3 test_hotkey_features.py")

if __name__ == "__main__":
    main()