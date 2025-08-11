#!/usr/bin/env python3
"""
测试正确的三个点按钮选择
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def test_correct_button_selection():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        print("🎯 测试正确的三个点按钮选择")
        
        # 确保在文档页面
        current_url = driver.current_url
        if '/wiki/' not in current_url:
            print("❌ 请先导航到具体的文档页面")
            return False
            
        print(f"📄 当前文档: {driver.title}")
        
        # 滚动到顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 查找右上角按钮
        print("\n🔍 查找右上角按钮")
        all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
        window_size = driver.get_window_size()
        
        print(f"页面大小: {window_size['width']} x {window_size['height']}")
        
        right_top_buttons = []
        selected_button = None
        
        for i, button in enumerate(all_buttons):
            try:
                if button.is_displayed() and button.is_enabled():
                    location = button.location
                    
                    # 检查是否在右上角
                    is_right_top = (location['x'] > window_size['width'] * 0.66 and 
                                   location['y'] < window_size['height'] * 0.33)
                    
                    if is_right_top:
                        text = button.text.strip()
                        aria_label = button.get_attribute('aria-label') or ""
                        title = button.get_attribute('title') or ""
                        
                        print(f"找到右上角按钮 {i+1}: 位置({location['x']}, {location['y']}) "
                              f"文本:'{text}' 标签:'{aria_label}' 标题:'{title}'")
                        
                        # 应用新的选择逻辑
                        if text in ['编辑', '分享', 'Edit', 'Share']:
                            print(f"  ⏭️ 跳过: {text} 按钮")
                            continue
                        
                        right_top_buttons.append((button, text, aria_label, title, i+1))
                        
                        # 优先选择没有文本的图标按钮（通常是三个点）
                        if not text and not selected_button:
                            selected_button = button
                            print(f"✅ 选择图标按钮: 按钮{i+1}")
                        # 或者选择包含"更多"、"菜单"等关键词的按钮
                        elif any(keyword in (text + aria_label + title).lower() 
                               for keyword in ['more', 'menu', '更多', '菜单', '⋯', '…']):
                            if not selected_button:
                                selected_button = button
                                print(f"✅ 选择更多操作按钮: {text or aria_label or title}")
                        
            except Exception as e:
                continue
        
        print(f"\n📊 总结:")
        print(f"- 找到 {len(right_top_buttons)} 个有效的右上角按钮")
        
        if selected_button:
            print("✅ 已选择按钮进行测试")
            
            # 测试选择的按钮
            print("\n🧪 测试选择的按钮:")
            try:
                driver.execute_script("arguments[0].click();", selected_button)
                time.sleep(2)
                
                # 查找下载菜单
                download_items = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download')]")
                
                if download_items:
                    print(f"✅ 成功！找到 {len(download_items)} 个下载相关选项:")
                    for item in download_items:
                        if item.is_displayed():
                            print(f"  - {item.text}")
                    
                    # 测试点击下载选项
                    download_item = None
                    for item in download_items:
                        if item.is_displayed() and '下载' in item.text:
                            download_item = item
                            print(f"找到下载选项: {item.text}")
                            break
                    
                    if download_item:
                        print("🖱️ 点击下载选项...")
                        driver.execute_script("arguments[0].click();", download_item)
                        time.sleep(2)
                        
                        # 查找格式选项
                        format_items = driver.find_elements(By.XPATH, 
                            "//*[contains(text(), 'Word') or contains(text(), 'PDF') or contains(text(), 'docx')]")
                        
                        if format_items:
                            print(f"✅ 找到 {len(format_items)} 个格式选项:")
                            for item in format_items:
                                if item.is_displayed():
                                    print(f"  - {item.text}")
                            return True
                        else:
                            print("❌ 未找到格式选项")
                    else:
                        print("❌ 未找到有效的下载选项")
                
                else:
                    print("❌ 点击后未找到下载菜单")
                    
            except Exception as e:
                print(f"❌ 测试按钮失败: {e}")
        else:
            print("❌ 未选择到合适的按钮")
            
            if right_top_buttons:
                print("\n🔧 可选择测试的按钮:")
                for button, text, aria_label, title, index in right_top_buttons:
                    desc = text or aria_label or title or f"按钮{index}"
                    print(f"  - {desc}")
        
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_correct_button_selection()