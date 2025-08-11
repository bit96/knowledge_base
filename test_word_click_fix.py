#!/usr/bin/env python3
"""
测试脚本：基于test_current_page_download.py优化，添加导出弹窗处理
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def click_export_button_in_popup(driver):
    """点击弹窗中的导出按钮"""
    try:
        print("\n📤 第4步：处理导出弹窗")
        # 等待弹窗完全加载
        time.sleep(2)
        
        # 查找导出按钮 - 根据截图，应该是蓝色的"导出"按钮
        export_buttons = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '导出') or contains(text(), 'export') or contains(text(), '确定') or contains(text(), 'OK')]")
        
        print(f"找到 {len(export_buttons)} 个可能的导出按钮")
        
        # 查找可见的导出按钮
        visible_export_buttons = []
        for i, button in enumerate(export_buttons):
            try:
                if button.is_displayed() and button.is_enabled():
                    button_text = button.text.strip()
                    button_class = button.get_attribute('class') or ""
                    button_tag = button.tag_name
                    
                    print(f"按钮 {i+1}: '{button_text}' | 标签: {button_tag} | 类名: {button_class[:30]}...")
                    
                    if button_text:
                        visible_export_buttons.append((button, button_text))
            except:
                continue
        
        print(f"\n📋 可见的导出按钮共 {len(visible_export_buttons)} 个:")
        for i, (button, text) in enumerate(visible_export_buttons):
            print(f"  {i+1}. '{text}'")
        
        # 优先选择文本为"导出"的按钮（精确匹配）
        export_button = None
        for button, text in visible_export_buttons:
            # 首先尝试精确匹配"导出"
            if text == '导出' or text.lower() == 'export':
                export_button = button
                print(f"✅ 选择导出按钮: {text}")
                break
        
        # 如果没找到精确匹配，再查找包含"导出"的按钮（排除设置类）
        if not export_button:
            for button, text in visible_export_buttons:
                if ('导出' in text or 'export' in text.lower()) and '设置' not in text and 'setting' not in text.lower():
                    export_button = button
                    print(f"✅ 选择导出按钮: {text}")
                    break
        
        # 如果没找到"导出"，选择第一个可用按钮
        if not export_button and visible_export_buttons:
            export_button, text = visible_export_buttons[0]
            print(f"✅ 使用备选按钮: {text}")
        
        if not export_button:
            print("❌ 未找到导出按钮")
            return False
        
        # 点击导出按钮
        print("🖱️ 点击导出按钮...")
        driver.execute_script("arguments[0].click();", export_button)
        time.sleep(3)  # 等待下载开始
        
        print("✅ 导出按钮点击完成")
        return True
            
    except Exception as e:
        print(f"❌ 点击导出按钮失败: {e}")
        return False

def test_current_page_download():
    """测试当前页面文档下载（基于原test_current_page_download.py）"""
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        print("📥 测试当前页面文档下载")
        print("=" * 50)
        
        # 检查当前页面
        current_url = driver.current_url
        if '/wiki/' not in current_url:
            print("❌ 请先导航到具体的文档页面")
            print("💡 确保URL包含'/wiki/'")
            return False
            
        doc_title = driver.title
        print(f"📄 当前文档: {doc_title}")
        print(f"🔗 URL: {current_url}")
        
        # 确保output目录存在
        output_dir = "/Users/abc/PycharmProjects/knowledge_base/.venv/output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"✅ 创建输出目录: {output_dir}")
        else:
            print(f"✅ 输出目录已存在: {output_dir}")
        
        # 滚动到页面顶部
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # 第1步：查找并点击右上角三个点按钮
        print("\n🔍 第1步：查找右上角三个点按钮")
        
        all_buttons = driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
        window_size = driver.get_window_size()
        print(f"页面大小: {window_size['width']} x {window_size['height']}")
        print(f"找到 {len(all_buttons)} 个按钮元素")
        
        three_dots_button = None
        
        for i, button in enumerate(all_buttons):
            try:
                if button.is_displayed() and button.is_enabled():
                    location = button.location
                    
                    # 检查是否在右上角区域
                    is_right_top = (location['x'] > window_size['width'] * 0.66 and 
                                   location['y'] < window_size['height'] * 0.33)
                    
                    if is_right_top:
                        text = button.text.strip()
                        aria_label = button.get_attribute('aria-label') or ""
                        title = button.get_attribute('title') or ""
                        
                        print(f"找到右上角按钮 {i+1}: 位置({location['x']}, {location['y']}) "
                              f"文本:'{text}' 标签:'{aria_label}' 标题:'{title}'")
                        
                        # 跳过"编辑"、"分享"等明确不是更多操作的按钮
                        if text in ['编辑', '分享', 'Edit', 'Share']:
                            print(f"  ⏭️ 跳过: {text} 按钮")
                            continue
                        
                        # 优先选择没有文本的图标按钮（通常是三个点）
                        if not text and not three_dots_button:
                            three_dots_button = button
                            print(f"✅ 选择图标按钮: 按钮{i+1}")
                        # 或者选择包含"更多"、"菜单"等关键词的按钮
                        elif any(keyword in (text + aria_label + title).lower() 
                               for keyword in ['more', 'menu', '更多', '菜单', '⋯', '…']):
                            if not three_dots_button:
                                three_dots_button = button
                                print(f"✅ 选择更多操作按钮: {text or aria_label or title}")
                        
            except Exception as e:
                continue
        
        if not three_dots_button:
            print("❌ 未找到三个点按钮")
            return False
        
        # 点击三个点按钮
        print("🖱️ 点击三个点按钮...")
        driver.execute_script("arguments[0].click();", three_dots_button)
        time.sleep(2)
        
        # 第2步：查找并悬停"下载为"按钮
        print("\n📥 第2步：查找下载为按钮")
        
        # 等待菜单出现
        time.sleep(1)
        
        # 查找下载相关菜单项，但只考虑可见的非script元素
        download_items = driver.find_elements(By.XPATH, 
            "//*[not(self::script) and (contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download') or contains(text(), 'export'))]")
        
        print(f"找到 {len(download_items)} 个下载相关菜单项")
        
        # 详细列出所有下载相关菜单项
        visible_items = []
        for i, item in enumerate(download_items):
            try:
                item_text = item.text.strip()
                is_displayed = item.is_displayed()
                element_tag = item.tag_name
                element_class = item.get_attribute('class') or ""
                element_id = item.get_attribute('id') or ""
                
                print(f"菜单项 {i+1}: '{item_text}' | 可见: {is_displayed} | 标签: {element_tag} | 类名: {element_class[:50]}...")
                
                if is_displayed:
                    visible_items.append((item, item_text))
                    
            except Exception as e:
                print(f"菜单项 {i+1}: 获取信息失败 - {e}")
        
        print(f"\n📋 可见的下载菜单项共 {len(visible_items)} 个:")
        for i, (item, text) in enumerate(visible_items):
            print(f"  {i+1}. '{text}'")
        
        download_button = None
        for item, text in visible_items:
            # 优先选择"下载为"或包含"下载"的选项
            if '下载' in text or 'download' in text.lower():
                download_button = item
                print(f"✅ 选择下载菜单: {text}")
                break
        
        if not download_button:
            print("❌ 未找到下载为按钮")
            return False
        
        # 鼠标悬停到下载为按钮上（不是点击）
        print("🖱️ 鼠标悬停到下载为按钮上...")
        actions = ActionChains(driver)
        actions.move_to_element(download_button).perform()
        time.sleep(2)  # 等待右侧子菜单出现
        
        # 第3步：查找并点击Word按钮（在右侧弹出的子菜单中）
        print("\n📝 第3步：查找Word按钮（右侧子菜单）")
        
        # 等待子菜单完全显示
        time.sleep(1)
        
        # 查找格式选项，排除script和style标签
        format_items = driver.find_elements(By.XPATH, 
            "//*[not(self::script) and not(self::style) and (contains(text(), 'Word') or contains(text(), 'PDF') or contains(text(), 'docx') or contains(text(), 'word'))]")
        
        print(f"找到 {len(format_items)} 个格式选项")
        
        # 详细列出所有格式选项，进一步过滤
        visible_format_items = []
        for i, item in enumerate(format_items):
            try:
                item_text = item.text.strip()
                is_displayed = item.is_displayed()
                element_tag = item.tag_name
                element_class = item.get_attribute('class') or ""
                
                print(f"格式选项 {i+1}: '{item_text}' | 可见: {is_displayed} | 标签: {element_tag} | 类名: {element_class[:50]}...")
                
                # 只选择可见的、有文本内容的、非样式标签的元素
                if (is_displayed and 
                    item_text and 
                    element_tag not in ['script', 'style', 'meta', 'link'] and
                    len(item_text) > 0):
                    visible_format_items.append((item, item_text))
                    print(f"  ✅ 有效选项: {item_text}")
                    
            except Exception as e:
                print(f"格式选项 {i+1}: 获取信息失败 - {e}")
        
        print(f"\n📋 有效的格式选项共 {len(visible_format_items)} 个:")
        for i, (item, text) in enumerate(visible_format_items):
            print(f"  {i+1}. '{text}'")
        
        word_button = None
        for item, text in visible_format_items:
            # 优先选择Word格式
            if 'Word' in text or 'word' in text.lower() or 'docx' in text.lower():
                word_button = item
                print(f"✅ 选择Word格式: {text}")
                break
        
        if not word_button and visible_format_items:
            # 如果没找到Word，选择第一个可用的格式
            word_button, text = visible_format_items[0]
            print(f"✅ 使用备选格式: {text}")
        
        if not word_button:
            print("❌ 未找到任何可用的格式选项")
            return False
        
        # 尝试多种点击方法
        print(f"\n🖱️ 尝试点击Word按钮...")
        click_success = False
        
        # 跳过方法1，直接从方法2开始
        click_success = False
        
        # 方法2: Selenium原生点击
        if not click_success:
            try:
                print("  方法2: Selenium原生点击")
                word_button.click()
                time.sleep(2)
                print("  ✅ Selenium点击执行成功")
                click_success = True
            except Exception as e:
                print(f"  ❌ Selenium点击失败: {e}")
        
        # 方法3: ActionChains点击
        if not click_success:
            try:
                print("  方法3: ActionChains点击")
                actions = ActionChains(driver)
                actions.move_to_element(word_button).click().perform()
                time.sleep(2)
                print("  ✅ ActionChains点击执行成功")
                click_success = True
            except Exception as e:
                print(f"  ❌ ActionChains点击失败: {e}")
        
        # 方法4: 查找可点击的父元素
        if not click_success:
            try:
                print("  方法4: 尝试点击父元素")
                parent = word_button.find_element(By.XPATH, "./..")
                parent_tag = parent.tag_name
                parent_class = parent.get_attribute('class') or ""
                print(f"    父元素: {parent_tag}, 类名: {parent_class[:50]}...")
                
                driver.execute_script("arguments[0].click();", parent)
                time.sleep(2)
                print("  ✅ 父元素点击执行成功")
                click_success = True
            except Exception as e:
                print(f"  ❌ 父元素点击失败: {e}")
        
        if not click_success:
            print("❌ 所有点击方法都失败了")
            return False
        
        # 等待弹窗出现
        time.sleep(3)
        
        # 第4步：处理导出弹窗
        export_success = click_export_button_in_popup(driver)
        
        if not export_success:
            print("❌ 导出弹窗处理失败")
            return False
        
        print("\n✅ 完整下载流程完成!")
        print(f"📁 文档应该下载到: {output_dir}")
        print(f"📄 文档标题: {doc_title}")
        
        # 等待一下让下载开始
        time.sleep(5)
        
        # 检查是否有新文件
        if os.path.exists(output_dir):
            files_after = os.listdir(output_dir)
            if files_after:
                print(f"📂 输出目录中的文件:")
                for f in files_after:
                    print(f"  - {f}")
            else:
                print("ℹ️ 输出目录中暂无文件（下载可能需要一些时间）")
        
        return True
        
    except Exception as e:
        print(f"❌ 下载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 启动优化版文档下载测试")
    print("完整流程包含：")
    print("1. 点击右上角三个点按钮")
    print("2. 鼠标悬停到下载为按钮") 
    print("3. 点击Word按钮")
    print("4. 点击弹窗中的导出按钮")
    print()
    print("基于test_current_page_download.py优化，添加导出弹窗处理")
    print("请确保已导航到飞书文档页面")
    print()
    
    input("按回车键开始测试...")
    
    success = test_current_page_download()
    
    if success:
        print("\n🎉 测试成功完成!")
    else:
        print("\n❌ 测试失败，请检查错误信息")