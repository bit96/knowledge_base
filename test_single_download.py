#!/usr/bin/env python3
"""
测试单个文档的完整下载流程
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def test_single_document_download():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        print("🎯 测试单个文档完整下载流程")
        
        # 确保在正确的文档页面
        current_url = driver.current_url
        if '/wiki/' not in current_url:
            print("❌ 请先导航到具体的文档页面")
            return False
            
        print(f"📄 当前文档: {driver.title}")
        print(f"🔗 URL: {current_url}")
        
        # 滚动到顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 第一步：查找右上角按钮（采用成功的方法）
        print("\n🔍 第一步：查找右上角按钮")
        all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
        window_size = driver.get_window_size()
        
        print(f"页面大小: {window_size['width']} x {window_size['height']}")
        print(f"找到 {len(all_buttons)} 个按钮元素")
        
        right_top_buttons = []
        
        for i, button in enumerate(all_buttons):
            try:
                if button.is_displayed() and button.is_enabled():
                    location = button.location
                    
                    # 检查是否在右上角
                    is_right_top = (location['x'] > window_size['width'] * 0.66 and 
                                   location['y'] < window_size['height'] * 0.33)
                    
                    if is_right_top:
                        text = button.text.strip()
                        right_top_buttons.append((button, text, i+1))
                        print(f"找到右上角按钮 {i+1}: 位置({location['x']}, {location['y']}) 文本:'{text}'")
            except Exception as e:
                continue
        
        if not right_top_buttons:
            print("❌ 未找到右上角按钮")
            return False
        
        print(f"✅ 共找到 {len(right_top_buttons)} 个右上角按钮")
        
        # 第二步：测试每个按钮
        print("\n🧪 第二步：测试每个右上角按钮")
        
        success_button = None
        for button, text, index in right_top_buttons:
            print(f"\n测试按钮 {index}: '{text}'")
            
            try:
                # 点击按钮
                driver.execute_script("arguments[0].click();", button)
                time.sleep(2)
                
                # 查找下载相关菜单
                download_items = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download')]")
                
                if download_items:
                    print(f"✅ 点击后找到 {len(download_items)} 个下载相关菜单项:")
                    
                    for item in download_items:
                        if item.is_displayed():
                            print(f"  - {item.text}")
                    
                    # 找到有效按钮，进行完整测试
                    success_button = button
                    
                    # 第三步：点击下载菜单
                    print("\n📥 第三步：点击下载菜单")
                    download_item = None
                    for item in download_items:
                        if item.is_displayed() and '下载' in item.text:
                            download_item = item
                            break
                    
                    if download_item:
                        print(f"点击: {download_item.text}")
                        driver.execute_script("arguments[0].click();", download_item)
                        time.sleep(2)
                        
                        # 第四步：查找格式选项
                        print("\n📋 第四步：查找格式选项")
                        format_items = driver.find_elements(By.XPATH, 
                            "//*[contains(text(), 'Word') or contains(text(), 'PDF') or contains(text(), 'docx')]")
                        
                        print(f"找到 {len(format_items)} 个格式选项:")
                        for item in format_items:
                            if item.is_displayed():
                                print(f"  - {item.text}")
                        
                        # 选择Word格式
                        word_item = None
                        for item in format_items:
                            if item.is_displayed() and ('Word' in item.text or 'word' in item.text.lower()):
                                word_item = item
                                break
                        
                        if word_item:
                            print(f"选择格式: {word_item.text}")
                            driver.execute_script("arguments[0].click();", word_item)
                            time.sleep(3)
                            
                            print("✅ 下载流程完成！")
                            return True
                        else:
                            print("❌ 未找到Word格式")
                    else:
                        print("❌ 未找到下载菜单项")
                    
                    break  # 找到有效按钮，不继续测试其他按钮
                    
                else:
                    print("❌ 点击后未出现下载菜单")
                    # 点击空白处关闭可能的菜单
                    driver.execute_script("document.body.click();")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ 测试按钮失败: {e}")
        
        if not success_button:
            print("❌ 所有右上角按钮都无效")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_single_document_download()