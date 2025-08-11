#!/usr/bin/env python3
"""
测试双击打开知识库文档
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

def test_double_click():
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        driver = webdriver.Chrome(options=chrome_options)
        
        # 切换到知识库标签页
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if 'zh3vobp856.feishu.cn' in driver.current_url:
                break
        
        print('🧪 测试双击打开文档...')
        
        # 查找文档节点
        doc_nodes = driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
        
        for node in doc_nodes:
            text = node.text.strip()
            if '新人须知' in text or '新人需知' in text:
                print(f'找到目标文档: {text}')
                parent = node.find_element(By.XPATH, './..')
                
                original_url = driver.current_url
                print(f'原始URL: ...{original_url[-40:]}')
                
                # 尝试双击
                print('执行双击操作...')
                ActionChains(driver).double_click(parent).perform()
                time.sleep(4)
                
                new_url = driver.current_url
                print(f'新URL: ...{new_url[-40:]}')
                
                if new_url != original_url:
                    print('✅ 双击成功！文档已打开')
                    return True
                else:
                    print('❌ 双击无效')
                    
                    # 尝试单击后按Enter
                    print('尝试点击+Enter...')
                    parent.click()
                    time.sleep(1)
                    parent.send_keys('\n')
                    time.sleep(3)
                    
                    final_url = driver.current_url
                    if final_url != original_url:
                        print('✅ 点击+Enter成功！')
                        return True
                    else:
                        print('❌ 点击+Enter也无效')
                
                break
        else:
            print('❌ 未找到目标文档')
            
        return False
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        return False

if __name__ == "__main__":
    test_double_click()