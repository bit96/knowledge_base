#!/usr/bin/env python3
"""
调试页面元素识别
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

def debug_current_page():
    """调试当前页面的元素"""
    print("调试页面元素识别...")
    
    try:
        # 连接到Chrome
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"当前页面标题: {driver.title}")
        print(f"当前页面URL: {driver.current_url}")
        print("-" * 50)
        
        # 查找所有可能的文档链接
        selectors_to_test = [
            "a[href*='/docs/']",
            "a[href*='/docx/']", 
            "a[href*='/sheets/']",
            "a[href*='/slides/']",
            ".file-item a",
            ".doc-item a", 
            "[data-testid*='doc'] a",
            "a",  # 所有链接
        ]
        
        for i, selector in enumerate(selectors_to_test):
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"{i+1}. 选择器: {selector}")
                print(f"   找到 {len(elements)} 个元素")
                
                if elements and len(elements) <= 10:  # 只显示前10个
                    for j, element in enumerate(elements[:10]):
                        try:
                            text = element.text.strip()
                            href = element.get_attribute('href')
                            if text and href:
                                print(f"   [{j+1}] 文本: {text[:50]}...")
                                print(f"       链接: {href}")
                        except:
                            pass
                print()
                        
            except Exception as e:
                print(f"{i+1}. 选择器: {selector} - 错误: {e}")
        
        # 检查页面源码关键词
        page_source = driver.page_source.lower()
        keywords = ['docs', 'docx', 'sheets', 'slides', '文档', 'document']
        
        print("页面关键词检查:")
        for keyword in keywords:
            count = page_source.count(keyword)
            print(f"  '{keyword}': {count} 次")
        
        print(f"\n页面源码长度: {len(page_source)} 字符")
        
        # 不关闭浏览器
        print("\n调试完成，浏览器保持打开状态")
        
    except WebDriverException:
        print("❌ 无法连接到Chrome，请先启动Chrome调试模式:")
        print('/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222')
    except Exception as e:
        print(f"调试失败: {e}")

if __name__ == "__main__":
    debug_current_page()