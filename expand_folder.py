#!/usr/bin/env python3
"""
展开知识库文件夹查看子文档
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def expand_folder_and_find_docs():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if 'zh3vobp856.feishu.cn' in driver.current_url:
                break
        
        print('🎯 查找并展开"新人园地-通关宝典"文件夹...')
        
        # 查找目标文件夹
        doc_nodes = driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
        target_folder = None
        
        for node in doc_nodes:
            text = node.text.strip()
            if '新人园地-通关宝典' == text:
                print(f'✅ 找到文件夹: {text}')
                target_folder = node.find_element(By.XPATH, './..')
                break
        
        if not target_folder:
            print('❌ 未找到"新人园地-通关宝典"文件夹')
            return []
        
        # 点击展开文件夹
        print('点击展开文件夹...')
        target_folder.click()
        time.sleep(3)
        
        # 查找展开后的内容
        print('\n📋 查找展开后的子文档:')
        time.sleep(2)  # 等待展开动画完成
        
        # 重新获取所有节点
        all_nodes = driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
        found_docs = []
        
        for i, node in enumerate(all_nodes):
            text = node.text.strip()
            if text and any(keyword in text for keyword in ['新人须知', '新人办公', '部门初相识', '新人学习', '新人培养', '新人必读', '组织文化']):
                print(f'{len(found_docs)+1}. 找到文档: "{text}"')
                parent = node.find_element(By.XPATH, './..')
                found_docs.append({
                    'text': text,
                    'element': parent,
                    'node': node
                })
        
        if found_docs:
            print(f'\n✅ 共找到 {len(found_docs)} 个相关文档')
            
            # 尝试点击第一个文档
            first_doc = found_docs[0]
            print(f'\n🧪 测试打开第一个文档: {first_doc["text"]}')
            
            original_url = driver.current_url
            
            # 双击尝试打开
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver).double_click(first_doc['element']).perform()
            time.sleep(4)
            
            new_url = driver.current_url
            if new_url != original_url:
                print('✅ 文档打开成功!')
                print(f'新URL: {new_url}')
                return True
            else:
                print('❌ 双击无效，文档可能已在右侧显示')
                
                # 检查页面内容是否改变
                page_text = driver.page_source
                if first_doc['text'] in page_text:
                    print('✅ 文档内容可能已在页面右侧显示')
                    return True
        else:
            print('❌ 展开后未找到相关文档')
            
        return found_docs
        
    except Exception as e:
        print(f'❌ 操作失败: {e}')
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    expand_folder_and_find_docs()