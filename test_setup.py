#!/usr/bin/env python3
"""
测试飞书下载器的基础设置
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

def test_chrome_connection():
    """测试Chrome连接"""
    print("测试Chrome浏览器连接...")
    
    # 方法1：尝试连接调试端口
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ 成功连接到现有Chrome会话")
        print(f"当前页面: {driver.title}")
        print(f"URL: {driver.current_url}")
        
        # 不关闭浏览器，只是断开连接
        driver.quit()
        return True
        
    except WebDriverException as e:
        print(f"❌ 无法连接到Chrome调试端口: {e}")
        
    # 方法2：启动新Chrome会话
    try:
        print("尝试启动新Chrome会话...")
        chrome_options = Options()
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ 成功启动新Chrome会话")
        print("⚠️  请在这个新窗口中登录飞书账号")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Chrome启动失败: {e}")
        return False

def test_output_directory():
    """测试输出目录"""
    print("\n测试输出目录...")
    
    output_dir = "/Users/abc/PycharmProjects/knowledge_base/.venv/output"
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # 测试写入权限
        test_file = os.path.join(output_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        print(f"✅ 输出目录可用: {output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 输出目录问题: {e}")
        return False

def main():
    print("飞书文档下载器 - 基础环境测试")
    print("=" * 40)
    
    # 测试输出目录
    dir_ok = test_output_directory()
    
    # 测试Chrome连接
    chrome_ok = test_chrome_connection()
    
    print("\n测试结果:")
    print("=" * 40)
    
    if dir_ok and chrome_ok:
        print("✅ 环境测试通过，可以运行主程序")
        print("\n下一步:")
        print("1. 确保Chrome中已登录飞书")
        print("2. 导航到文档列表页面") 
        print("3. 运行: python feishu_downloader.py")
    else:
        print("❌ 环境测试未通过，请检查上述问题")
        
        if not chrome_ok:
            print("\n解决Chrome连接问题:")
            print("方法1: 启动Chrome调试模式")
            print('/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222')
            print("方法2: 让脚本启动新Chrome窗口（需要重新登录飞书）")

if __name__ == "__main__":
    main()