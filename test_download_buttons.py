#!/usr/bin/env python3
"""
测试飞书文档页面的下载按钮查找
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def test_download_buttons():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        print("🔍 测试下载按钮查找...")
        current_url = driver.current_url
        print(f"当前页面: {current_url}")
        
        # 确保在文档页面
        if '/wiki/' not in current_url:
            print("❌ 请先导航到具体的文档页面")
            return
        
        # 滚动到页面顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 查找所有可能的按钮
        print("\n📋 查找页面中的所有按钮:")
        all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
        
        window_size = driver.get_window_size()
        print(f"窗口大小: {window_size['width']} x {window_size['height']}")
        
        right_top_buttons = []
        
        for i, button in enumerate(all_buttons):
            try:
                if button.is_displayed():
                    location = button.location
                    size = button.size
                    text = button.text.strip()
                    aria_label = button.get_attribute('aria-label') or ""
                    title = button.get_attribute('title') or ""
                    class_name = button.get_attribute('class') or ""
                    
                    # 检查是否在右上角区域
                    is_right_top = (location['x'] > window_size['width'] * 0.66 and 
                                   location['y'] < window_size['height'] * 0.33)
                    
                    info = f"按钮{i+1}: 位置({location['x']}, {location['y']}) 大小({size['width']}x{size['height']})"
                    
                    if text:
                        info += f" 文本:'{text}'"
                    if aria_label:
                        info += f" 标签:'{aria_label}'"
                    if title:
                        info += f" 标题:'{title}'"
                    if class_name:
                        info += f" 类名:'{class_name[:50]}...'"
                    
                    if is_right_top:
                        info += " ✅ 右上角"
                        right_top_buttons.append((button, text, aria_label, title))
                    
                    print(info)
                    
            except Exception as e:
                print(f"按钮{i+1}: 获取信息失败 - {e}")
        
        print(f"\n🎯 找到 {len(right_top_buttons)} 个右上角按钮")
        
        if right_top_buttons:
            print("\n🧪 测试点击右上角按钮:")
            
            for i, (button, text, aria_label, title) in enumerate(right_top_buttons):
                desc = text or aria_label or title or f"按钮{i+1}"
                print(f"\n测试按钮: {desc}")
                
                try:
                    # 点击按钮
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    
                    # 查找下拉菜单
                    menu_items = driver.find_elements(By.XPATH, "//*[contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download') or contains(text(), 'export')]")
                    
                    if menu_items:
                        print(f"✅ 点击后出现菜单，找到 {len(menu_items)} 个相关选项:")
                        for item in menu_items:
                            if item.is_displayed():
                                print(f"  - {item.text}")
                        
                        # 测试点击"下载为"或类似选项
                        download_item = None
                        for item in menu_items:
                            if item.is_displayed() and ('下载' in item.text or 'download' in item.text.lower()):
                                download_item = item
                                break
                        
                        if download_item:
                            print(f"🖱️ 点击: {download_item.text}")
                            driver.execute_script("arguments[0].click();", download_item)
                            time.sleep(2)
                            
                            # 查找格式选项
                            format_options = driver.find_elements(By.XPATH, "//*[contains(text(), 'Word') or contains(text(), 'PDF') or contains(text(), 'docx')]")
                            
                            if format_options:
                                print("✅ 找到下载格式选项:")
                                for option in format_options:
                                    if option.is_displayed():
                                        print(f"  - {option.text}")
                            else:
                                print("❌ 未找到下载格式选项")
                        else:
                            print("❌ 未找到下载相关选项")
                        
                        # 点击空白处关闭菜单
                        driver.execute_script("document.body.click();")
                        time.sleep(1)
                        
                    else:
                        print("❌ 点击后未出现相关菜单")
                        
                except Exception as e:
                    print(f"❌ 测试按钮失败: {e}")
        
        else:
            print("❌ 未找到右上角按钮")
            print("\n💡 建议手动操作:")
            print("1. 查看页面右上角是否有三个点按钮")
            print("2. 点击后查看是否有'下载为'选项")
            print("3. 确认下载格式选项")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_download_buttons()