#!/usr/bin/env python3
"""
检查当前页面的文档链接
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def check_current_page():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        current_url = driver.current_url
        page_title = driver.title
        
        print("🔍 当前页面信息:")
        print(f"URL: {current_url}")
        print(f"标题: {page_title}")
        print("-" * 60)
        
        if 'zh3vobp856.feishu.cn' not in current_url:
            print("❌ 请先导航到您的知识库页面:")
            print("https://zh3vobp856.feishu.cn/wiki/JPGPwwEBIirtlqkNF9gcIqYtn1f?fromScene=spaceOverview")
            return
        
        print("✅ 正在知识库域名，检查文档链接...")
        time.sleep(3)  # 等待页面完全加载
        
        # 知识库专用选择器
        selectors_to_try = [
            'a[href*="/wiki/"]',
            'table a',
            'tbody a', 
            'tr a',
            'td a',
            '[class*="doc"] a',
            '[class*="file"] a',
            '.lark-table a',
            '.lark-row a',
            'a[data-testid]',
            'a:not([href*="javascript"]):not([href*="mailto"])',
        ]
        
        found_links = []
        
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"📎 选择器 '{selector}': 找到 {len(elements)} 个链接")
                    
                    for element in elements:
                        try:
                            href = element.get_attribute('href')
                            text = element.text.strip()
                            
                            if href and text and len(text) > 0:
                                # 过滤出看起来像文档的链接
                                if any(keyword in text for keyword in ['新人', '文档', '须知', '贴士', '计划', '文化', '必读']):
                                    found_links.append({
                                        'text': text,
                                        'href': href,
                                        'selector': selector
                                    })
                                    print(f"  ✓ {text} -> {href}")
                        except:
                            continue
                            
            except Exception as e:
                print(f"选择器 {selector} 出错: {e}")
        
        print(f"\n📊 总共找到相关文档链接: {len(found_links)} 个")
        
        if found_links:
            print("\n🎯 建议测试这些链接:")
            for i, link in enumerate(found_links[:5]):
                print(f"  {i+1}. {link['text']}")
        else:
            print("\n❓ 未找到文档链接，可能需要:")
            print("1. 确保页面完全加载")
            print("2. 检查是否需要展开文件夹")
            print("3. 滚动页面查看更多内容")
            
        return found_links
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return []

if __name__ == "__main__":
    check_current_page()