#!/usr/bin/env python3
"""
最简单的飞书目录深度遍历脚本
基于 run_traverser_modular.py 简化而来
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime


class SimpleDeepTraverser:
    """简单深度遍历器"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.visited_texts = set()
        self.results = []
        
    def setup_chrome(self):
        """连接到Chrome调试模式"""
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            print(f"✅ 成功连接Chrome，当前页面: {self.driver.title}")
            print(f"🔗 当前URL: {self.driver.current_url}")
            return True
            
        except Exception as e:
            print(f"❌ Chrome连接失败: {e}")
            print("💡 请确保Chrome以调试模式启动:")
            print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
            return False
    
    def find_sidebar_items(self):
        """查找左侧目录项"""
        selectors = [
            '.workspace-tree-view-node-content',  # 飞书专用
            '[class*="tree-view-node"]',
            '[class*="tree"] span[class*="content"]',
            '.sidebar a[href]',  # 兜底方案
            'nav a[href]'
        ]
        
        items = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.strip()
                        if text and len(text) > 0 and len(text) < 100:
                            # 检查是否在左侧（x坐标小于400）
                            location = element.location
                            if location['x'] < 400:
                                items.append({
                                    'element': element,
                                    'text': text,
                                    'href': element.get_attribute('href') or f"#node-{text}"
                                })
                                
                if items:
                    print(f"🔍 使用选择器 '{selector}' 找到 {len(items)} 个目录项")
                    break
                    
            except Exception as e:
                print(f"⚠️ 选择器 '{selector}' 查找失败: {e}")
                continue
        
        return items
    
    def click_item_safe(self, item):
        """安全点击目录项"""
        try:
            element = item['element']
            text = item['text']
            
            # 滚动到可见位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 点击
            element.click()
            print(f"✅ 成功点击: {text}")
            
            # 等待页面加载
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ 点击失败 '{text}': {e}")
            return False
    
    def extract_current_page_info(self):
        """提取当前页面信息"""
        try:
            return {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except:
            return None
    
    def recursive_traverse(self, level=0, max_depth=5):
        """递归深度遍历"""
        if level > max_depth:
            print(f"⚠️ 达到最大深度 {max_depth}，停止遍历")
            return
            
        indent = "  " * level
        print(f"{indent}🌲 开始第 {level + 1} 层遍历...")
        
        # 查找当前层级的目录项
        items = self.find_sidebar_items()
        if not items:
            print(f"{indent}📭 第 {level + 1} 层未找到目录项")
            return
        
        # 过滤已访问的项目
        new_items = []
        for item in items:
            if item['text'] not in self.visited_texts:
                new_items.append(item)
                self.visited_texts.add(item['text'])
        
        print(f"{indent}📋 发现 {len(new_items)} 个新目录项")
        
        # 遍历每个项目
        for i, item in enumerate(new_items, 1):
            text = item['text']
            print(f"{indent}📄 [{i}/{len(new_items)}] 处理: {text}")
            
            # 访问延迟（2-3秒）
            if i > 1:
                delay = random.uniform(2, 3)
                print(f"{indent}⏳ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
            
            # 点击项目
            if self.click_item_safe(item):
                # 提取页面信息
                page_info = self.extract_current_page_info()
                if page_info:
                    page_info['directory_item'] = text
                    page_info['level'] = level + 1
                    self.results.append(page_info)
                    print(f"{indent}💾 记录页面: {page_info['title']}")
                
                # 递归遍历下一层
                self.recursive_traverse(level + 1, max_depth)
            
            # 尝试返回上一级（如果URL改变了）
            try:
                self.driver.back()
                time.sleep(1)
            except:
                pass
    
    def save_results(self):
        """保存遍历结果"""
        if not self.results:
            print("📭 没有结果可保存")
            return
            
        # 保存为简单的文本文件
        filename = f"traversal_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("飞书目录深度遍历结果\n")
            f.write("=" * 50 + "\n\n")
            
            for i, result in enumerate(self.results, 1):
                f.write(f"{i}. {result['directory_item']} (层级 {result['level']})\n")
                f.write(f"   标题: {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   时间: {result['timestamp']}\n\n")
        
        print(f"💾 结果已保存到: {filename}")
        print(f"📊 总共遍历 {len(self.results)} 个页面")
    
    def run(self):
        """主运行函数"""
        print("🚀 飞书目录深度遍历器 (简化版)")
        print("=" * 40)
        
        # 连接Chrome
        if not self.setup_chrome():
            return
        
        print("\n⚠️ 请确保当前页面是飞书知识库的目录页面")
        input("确认后按回车键开始遍历...")
        
        try:
            # 开始深度遍历
            print("\n🌲 开始深度遍历...")
            start_time = time.time()
            
            self.recursive_traverse(max_depth=3)  # 最大3层深度
            
            # 计算耗时
            duration = time.time() - start_time
            print(f"\n🎉 遍历完成！耗时 {duration:.1f} 秒")
            
            # 保存结果
            self.save_results()
            
        except KeyboardInterrupt:
            print("\n⏸️ 用户中断遍历")
            self.save_results()
        except Exception as e:
            print(f"\n❌ 遍历出错: {e}")
            self.save_results()
        finally:
            if self.driver:
                print("🔚 遍历结束")


def main():
    traverser = SimpleDeepTraverser()
    traverser.run()


if __name__ == "__main__":
    main()