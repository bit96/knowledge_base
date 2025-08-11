#!/usr/bin/env python3
"""
手动调试 - 检查飞书页面是否可以识别文档
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def manual_debug():
    try:
        print("正在连接Chrome...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"✅ 连接成功!")
        print(f"页面标题: {driver.title}")
        print(f"页面URL: {driver.current_url}")
        
        # 等待页面加载
        time.sleep(3)
        
        # 尝试最常见的飞书文档选择器
        common_selectors = [
            # 飞书新版界面
            ".doc-list-item a",
            ".file-list-item a", 
            ".file-item a",
            "[data-testid='file-item'] a",
            
            # 通用文档链接
            "a[href*='docs.feishu']",
            "a[href*='/docs/']",
            "a[href*='/sheets/']",
            "a[href*='/docx/']",
            
            # 包含文档关键词的链接
            "a[title*='文档']",
            "a[title*='表格']", 
            "a[title*='演示文稿']",
        ]
        
        found_links = []
        
        for selector in common_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ 找到 {len(elements)} 个匹配元素: {selector}")
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        try:
                            text = elem.text.strip()
                            href = elem.get_attribute('href')
                            if text and href:
                                print(f"   [{i+1}] {text[:30]}... -> {href[:50]}...")
                                found_links.append({'text': text, 'href': href, 'element': elem})
                        except Exception as e:
                            print(f"   元素{i+1}获取失败: {e}")
                    print()
                    break  # 找到第一个有效选择器就停止
            except Exception as e:
                print(f"❌ {selector}: {e}")
        
        if not found_links:
            print("❌ 未找到任何文档链接")
            print("\n手动检查建议:")
            print("1. 确认当前页面确实是飞书文档列表页面")
            print("2. 页面是否完全加载完成")
            print("3. 是否需要先点击展开文件夹")
            
            # 输出页面基本信息用于分析
            print(f"\n页面信息:")
            print(f"标题: {driver.title}")
            print(f"URL: {driver.current_url}")
            
            # 查找所有链接
            all_links = driver.find_elements(By.TAG_NAME, "a")
            print(f"页面总链接数: {len(all_links)}")
            
            # 显示前5个链接供分析
            print("前5个链接:")
            for i, link in enumerate(all_links[:5]):
                try:
                    text = link.text.strip()
                    href = link.get_attribute('href')
                    if href:
                        print(f"  {i+1}. {text[:30]}... -> {href[:50]}...")
                except:
                    pass
                    
        else:
            print(f"✅ 总共找到 {len(found_links)} 个潜在的文档链接")
            
            # 测试点击第一个链接
            print("\n测试点击第一个文档...")
            try:
                first_link = found_links[0]['element']
                original_url = driver.current_url
                
                # 滚动到元素可见
                driver.execute_script("arguments[0].scrollIntoView(true);", first_link)
                time.sleep(1)
                
                # 点击链接
                first_link.click()
                time.sleep(3)
                
                new_url = driver.current_url
                new_title = driver.title
                
                print(f"✅ 点击成功!")
                print(f"新页面标题: {new_title}")
                print(f"新页面URL: {new_url}")
                
                # 返回原页面
                driver.back()
                time.sleep(2)
                print("✅ 已返回原页面")
                
            except Exception as e:
                print(f"❌ 点击测试失败: {e}")
        
        print("\n调试完成，Chrome保持打开状态")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        print("\n请确保:")
        print("1. Chrome已启动调试模式: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222")
        print("2. Chrome中已登录飞书并在文档列表页面")

if __name__ == "__main__":
    manual_debug()