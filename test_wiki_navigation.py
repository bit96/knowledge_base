#!/usr/bin/env python3
"""
测试知识库导航和文档访问
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

def test_wiki_navigation():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        # 切换到知识库标签页
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if 'zh3vobp856.feishu.cn' in driver.current_url:
                break
        
        print('🎯 分析知识库页面结构...')
        print(f'当前URL: {driver.current_url}')
        
        # 查找左侧导航树中的文档节点
        doc_nodes = driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
        print(f'找到 {len(doc_nodes)} 个导航节点')
        
        clickable_docs = []
        
        for node in doc_nodes:
            text = node.text.strip()
            if text and ('新人' in text or '部门' in text or '组织' in text):
                print(f'\n📄 文档节点: "{text}"')
                
                # 检查父级元素
                parent = node.find_element(By.XPATH, './..')
                grandparent = parent.find_element(By.XPATH, './..')
                
                # 检查是否可点击
                for element in [parent, grandparent]:
                    cursor = element.value_of_css_property('cursor')
                    onclick = element.get_attribute('onclick')
                    
                    if cursor == 'pointer' or onclick:
                        print(f'  ✅ {element.tag_name} 可点击 (cursor: {cursor})')
                        clickable_docs.append({'element': element, 'text': text})
                        break
                else:
                    print(f'  ❌ 节点不可点击')
        
        print(f'\n🎯 找到 {len(clickable_docs)} 个可点击的文档')
        
        if clickable_docs:
            # 测试点击
            doc_to_test = clickable_docs[0]
            print(f'\n🧪 测试点击: {doc_to_test["text"]}')
            
            original_url = driver.current_url
            
            # 点击
            ActionChains(driver).click(doc_to_test['element']).perform()
            time.sleep(3)
            
            new_url = driver.current_url
            
            if new_url != original_url:
                print('✅ 点击成功！导航到新页面')
                print(f'新URL: {new_url}')
                
                # 这里可以继续测试下载功能
                return True
            else:
                print('❌ 点击无效，可能需要双击或其他操作')
                return False
        else:
            print('❌ 没有找到可点击的文档节点')
            
            # 尝试其他方法
            print('\n🔍 尝试查找其他可能的文档链接...')
            all_clickable = driver.find_elements(By.CSS_SELECTOR, '[style*="cursor: pointer"], [onclick], button, .clickable')
            print(f'找到 {len(all_clickable)} 个可点击元素')
            
            return False
            
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_wiki_navigation()