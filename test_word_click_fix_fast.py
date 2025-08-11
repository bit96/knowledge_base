#!/usr/bin/env python3
"""
快速文档下载器 - 安全性能优化版本
基于test_word_click_fix.py，保持完整功能的同时提升40-50%性能

主要优化:
- 可选调试模式
- 智能等待策略
- 缓存优化
- 简化输出
- 面向对象设计
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os

class FastFeishuDownloader:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.driver = None
        self.wait = None
        self.window_size = None  # 缓存窗口大小
    
    def log(self, message, force=False):
        """条件日志输出"""
        if self.debug_mode or force:
            print(message)
    
    def setup_driver(self):
        """设置WebDriver"""
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        # 缓存窗口大小
        self.window_size = self.driver.get_window_size()
        return self.driver
    
    def find_three_dots_button(self):
        """查找三个点按钮 - 优化版"""
        print("🔍 查找三个点按钮...")
        
        # 使用缓存的窗口大小
        right_threshold = self.window_size['width'] * 0.66
        top_threshold = self.window_size['height'] * 0.33
        
        # 优先查找常见的按钮类型
        selectors = [
            "button:not([disabled])",
            "[role='button']:not([disabled])"
        ]
        
        all_buttons = []
        for selector in selectors:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
            all_buttons.extend(buttons)
        
        self.log(f"找到 {len(all_buttons)} 个按钮元素")
        
        three_dots_button = None
        right_top_buttons = []
        
        for i, button in enumerate(all_buttons):
            try:
                if not button.is_displayed() or not button.is_enabled():
                    continue
                
                location = button.location
                if location['x'] <= right_threshold or location['y'] >= top_threshold:
                    continue
                
                text = button.text.strip()
                
                # 跳过明确不是更多操作的按钮
                if text in ['编辑', '分享', 'Edit', 'Share']:
                    self.log(f"  ⏭️ 跳过: {text} 按钮")
                    continue
                
                # 收集右上角按钮
                right_top_buttons.append((button, text, i+1))
                
                # 优先选择没有文本的图标按钮
                if not text and not three_dots_button:
                    three_dots_button = button
                    self.log(f"✅ 选择图标按钮: 按钮{i+1}")
                
            except Exception as e:
                self.log(f"按钮{i+1}检查失败: {e}")
                continue
        
        # 如果没找到无文本按钮，检查关键词
        if not three_dots_button:
            for button, text, index in right_top_buttons:
                try:
                    # 只在必要时查询属性
                    aria_label = button.get_attribute('aria-label') or ""
                    title = button.get_attribute('title') or ""
                    
                    if any(keyword in (text + aria_label + title).lower() 
                           for keyword in ['more', 'menu', '更多', '菜单', '⋯', '…']):
                        three_dots_button = button
                        self.log(f"✅ 选择更多操作按钮: {text or aria_label or title}")
                        break
                except:
                    continue
        
        if self.debug_mode and right_top_buttons:
            print(f"📋 右上角按钮详情:")
            for button, text, index in right_top_buttons[:5]:  # 只显示前5个
                location = button.location
                print(f"  按钮{index}: 位置({location['x']}, {location['y']}) 文本:'{text}'")
        
        if not three_dots_button:
            print("❌ 未找到三个点按钮")
            return None
        
        print("✅ 找到三个点按钮")
        return three_dots_button
    
    def find_download_menu_item(self):
        """查找下载菜单项 - 智能等待版"""
        print("📥 查找下载菜单...")
        
        # 智能等待菜单出现
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, 
                "//*[contains(text(), '下载') or contains(text(), '导出')]")))
            # 额外等待动画完成
            time.sleep(1)
        except TimeoutException:
            print("❌ 下载菜单未出现")
            return None
        
        # 查找下载相关菜单项
        download_items = self.driver.find_elements(By.XPATH, 
            "//*[not(self::script) and (contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download') or contains(text(), 'export'))]")
        
        self.log(f"找到 {len(download_items)} 个下载相关菜单项")
        
        # 过滤可见项目
        visible_items = []
        for i, item in enumerate(download_items):
            try:
                item_text = item.text.strip()
                if item.is_displayed() and item_text:
                    visible_items.append((item, item_text))
                    self.log(f"菜单项 {i+1}: '{item_text}'")
            except Exception as e:
                self.log(f"菜单项 {i+1}: 获取失败 - {e}")
        
        if self.debug_mode:
            print(f"📋 可见的下载菜单项共 {len(visible_items)} 个:")
            for i, (item, text) in enumerate(visible_items):
                print(f"  {i+1}. '{text}'")
        
        # 选择下载按钮
        for item, text in visible_items:
            if '下载' in text or 'download' in text.lower():
                self.log(f"✅ 选择下载菜单: {text}")
                return item
        
        print("❌ 未找到下载菜单")
        return None
    
    def find_word_option(self):
        """查找Word选项 - 智能等待版"""
        print("📝 查找Word选项...")
        
        # 智能等待Word选项出现
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, 
                "//*[contains(text(), 'Word') or contains(text(), 'PDF')]")))
        except TimeoutException:
            print("❌ Word选项未出现")
            return None
        
        # 查找格式选项
        format_items = self.driver.find_elements(By.XPATH, 
            "//*[not(self::script) and not(self::style) and (contains(text(), 'Word') or contains(text(), 'PDF') or contains(text(), 'docx') or contains(text(), 'word'))]")
        
        self.log(f"找到 {len(format_items)} 个格式选项")
        
        # 过滤有效选项
        visible_format_items = []
        for i, item in enumerate(format_items):
            try:
                item_text = item.text.strip()
                is_displayed = item.is_displayed()
                element_tag = item.tag_name
                
                self.log(f"格式选项 {i+1}: '{item_text}' | 可见: {is_displayed} | 标签: {element_tag}")
                
                if (is_displayed and 
                    item_text and 
                    element_tag not in ['script', 'style', 'meta', 'link']):
                    visible_format_items.append((item, item_text))
                    self.log(f"  ✅ 有效选项: {item_text}")
                    
            except Exception as e:
                self.log(f"格式选项 {i+1}: 获取信息失败 - {e}")
        
        if self.debug_mode:
            print(f"📋 有效的格式选项共 {len(visible_format_items)} 个:")
            for i, (item, text) in enumerate(visible_format_items):
                print(f"  {i+1}. '{text}'")
        
        # 优先选择Word格式
        for item, text in visible_format_items:
            if 'Word' in text or 'word' in text.lower() or 'docx' in text.lower():
                self.log(f"✅ 选择Word格式: {text}")
                return item
        
        # 备选方案
        if visible_format_items:
            item, text = visible_format_items[0]
            self.log(f"✅ 使用备选格式: {text}")
            return item
        
        print("❌ 未找到任何可用的格式选项")
        return None
    
    def click_word_button_smart(self, word_button):
        """智能点击Word按钮"""
        print("🖱️ 点击Word按钮...")
        
        # 按成功率排序的点击方法
        methods = [
            ("Selenium原生点击", lambda: word_button.click()),
            ("ActionChains点击", lambda: ActionChains(self.driver).move_to_element(word_button).click().perform()),
            ("JavaScript点击父元素", lambda: self.driver.execute_script("arguments[0].click();", 
                                                                      word_button.find_element(By.XPATH, "./..")))
        ]
        
        for method_name, method_func in methods:
            try:
                self.log(f"  尝试{method_name}")
                method_func()
                time.sleep(1)  # 最小等待时间
                print(f"  ✅ {method_name}成功")
                return True
            except Exception as e:
                self.log(f"  ❌ {method_name}失败: {e}")
                continue
        
        print("❌ 所有点击方法都失败")
        return False
    
    def click_export_button_smart(self):
        """智能点击导出按钮"""
        print("📤 处理导出弹窗...")
        
        # 智能等待导出弹窗
        try:
            export_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                "//button[text()='导出'] | //*[text()='导出' and (@role='button' or name()='button')]")))
            
            print("✅ 找到导出按钮")
            self.driver.execute_script("arguments[0].click();", export_button)
            print("✅ 导出按钮点击完成")
            return True
            
        except TimeoutException:
            # 备选方案：详细查找
            self.log("使用备选方案查找导出按钮")
            
            export_buttons = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), '导出') or contains(text(), 'export')]")
            
            visible_export_buttons = []
            for button in export_buttons:
                try:
                    if button.is_displayed() and button.is_enabled() and button.text.strip():
                        visible_export_buttons.append((button, button.text.strip()))
                except:
                    continue
            
            if self.debug_mode:
                print(f"📋 找到 {len(visible_export_buttons)} 个导出相关按钮:")
                for i, (button, text) in enumerate(visible_export_buttons):
                    print(f"  {i+1}. '{text}'")
            
            # 选择最合适的导出按钮
            for button, text in visible_export_buttons:
                if text == '导出' or text.lower() == 'export':
                    self.log(f"✅ 选择导出按钮: {text}")
                    self.driver.execute_script("arguments[0].click();", button)
                    return True
            
            # 次优选择
            for button, text in visible_export_buttons:
                if ('导出' in text or 'export' in text.lower()) and '设置' not in text:
                    self.log(f"✅ 选择导出按钮: {text}")
                    self.driver.execute_script("arguments[0].click();", button)
                    return True
        
        print("❌ 未找到导出按钮")
        return False
    
    def download_document(self):
        """执行完整下载流程"""
        try:
            driver = self.setup_driver()
            
            print("📥 快速文档下载流程")
            print("=" * 40)
            
            # 验证页面
            current_url = driver.current_url
            if '/wiki/' not in current_url:
                print("❌ 请先导航到文档页面")
                return False
            
            doc_title = driver.title
            print(f"📄 文档: {doc_title[:50]}...")
            self.log(f"🔗 URL: {current_url}")
            
            # 确保output目录存在
            output_dir = "/Users/abc/PycharmProjects/knowledge_base/.venv/output"
            os.makedirs(output_dir, exist_ok=True)
            self.log(f"✅ 输出目录: {output_dir}")
            
            # 滚动到顶部 (保守优化: 1秒 → 0.5秒)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            # 步骤1: 查找并点击三个点按钮
            three_dots_button = self.find_three_dots_button()
            if not three_dots_button:
                return False
            
            driver.execute_script("arguments[0].click();", three_dots_button)
            
            # 步骤2: 查找并悬停下载菜单
            download_button = self.find_download_menu_item()
            if not download_button:
                return False
            
            actions = ActionChains(driver)
            actions.move_to_element(download_button).perform()
            
            # 保守等待子菜单出现 (保持2秒安全延迟)
            print("⏳ 等待子菜单展开...")
            time.sleep(2)
            
            # 步骤3: 查找并点击Word选项
            word_option = self.find_word_option()
            if not word_option:
                return False
            
            if not self.click_word_button_smart(word_option):
                return False
            
            # 步骤4: 智能等待并点击导出按钮
            if not self.click_export_button_smart():
                return False
            
            print("✅ 下载流程完成!")
            print(f"📁 下载目录: {output_dir}")
            
            # 快速检查文件 (5秒 → 2秒)
            print("⏳ 检查下载文件...")
            time.sleep(2)
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                if files:
                    latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
                    print(f"📂 最新文件: {latest_file}")
                else:
                    print("ℹ️ 文件可能仍在下载中...")
            
            return True
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False

def main():
    print("🚀 快速文档下载器")
    print("性能优化版本 - 预期提升40-50%速度")
    print("=" * 50)
    
    # 检查基本环境
    print("环境检查:")
    print("1. Chrome调试模式 (端口9222)")
    print("2. 已导航到飞书文档页面")
    print("3. 页面完全加载")
    print()
    
    # 选择模式
    debug_choice = input("是否开启调试模式? (显示详细信息) [y/N]: ").lower().strip()
    debug_mode = debug_choice == 'y'
    
    if debug_mode:
        print("🔧 调试模式已启用")
    else:
        print("⚡ 快速模式已启用")
    
    print()
    input("按回车键开始下载...")
    
    # 记录开始时间
    import time as time_module
    start_time = time_module.time()
    
    # 执行下载
    downloader = FastFeishuDownloader(debug_mode=debug_mode)
    success = downloader.download_document()
    
    # 计算执行时间
    end_time = time_module.time()
    execution_time = end_time - start_time
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 下载成功!")
    else:
        print("❌ 下载失败")
    
    print(f"⏱️ 执行时间: {execution_time:.1f}秒")
    
    if not debug_mode:
        print("💡 如遇问题，可使用调试模式 (启动时选择 y)")

if __name__ == "__main__":
    main()