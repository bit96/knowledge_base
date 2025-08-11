#!/usr/bin/env python3
"""
带重试机制的快速文档下载器
基于test_word_click_fix_fast2.py，添加智能重试机制

主要特性:
- 智能等待策略
- 缓存优化  
- 精简输出
- 面向对象设计
- 纯快速模式，无调试开销
- 智能重试机制：任意步骤失败后等待10秒重试，最多重试3次
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
    def __init__(self):
        self.driver = None
        self.wait = None
        self.window_size = None  # 缓存窗口大小
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 10  # 重试等待时间（秒）
    
    def setup_driver(self):
        """设置WebDriver"""
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        # 缓存窗口大小
        self.window_size = self.driver.get_window_size()
        return self.driver
    
    def reset_page_state(self):
        """重置页面状态，为重试准备"""
        try:
            print("🔄 重置页面状态...")
            # 滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            # 尝试点击页面其他区域关闭可能打开的菜单
            self.driver.execute_script("document.body.click();")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ 页面重置异常: {e}")
    
    def find_three_dots_button(self):
        """查找三个点按钮 - 快速版"""
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
        
        three_dots_button = None
        right_top_buttons = []
        
        # 先收集所有右上角按钮
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
                    continue
                
                right_top_buttons.append((button, text))
                
                # 优先选择没有文本的图标按钮
                if not text and not three_dots_button:
                    three_dots_button = button
                
            except Exception as e:
                continue
        
        # 如果没找到无文本按钮，检查关键词
        if not three_dots_button:
            for button, text in right_top_buttons:
                try:
                    # 查询属性
                    aria_label = button.get_attribute('aria-label') or ""
                    title = button.get_attribute('title') or ""
                    
                    if any(keyword in (text + aria_label + title).lower() 
                           for keyword in ['more', 'menu', '更多', '菜单', '⋯', '…']):
                        three_dots_button = button
                        break
                except Exception as e:
                    continue
        
        if not three_dots_button:
            print("❌ 未找到三个点按钮")
            return None
        
        print("✅ 找到三个点按钮")
        return three_dots_button
    
    def find_download_menu_item(self):
        """查找下载菜单项 - 快速版"""
        print("📥 查找下载菜单...")
        
        # 智能等待菜单出现
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, 
                "//*[contains(text(), '下载') or contains(text(), '导出')]")))
            # 等待动画完成
            time.sleep(1)
        except TimeoutException:
            print("❌ 下载菜单未出现")
            return None
        
        # 查找下载相关菜单项
        download_items = self.driver.find_elements(By.XPATH, 
            "//*[not(self::script) and (contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download') or contains(text(), 'export'))]")
        
        # 过滤可见项目
        visible_items = []
        for item in download_items:
            try:
                item_text = item.text.strip()
                if item.is_displayed() and item_text:
                    visible_items.append((item, item_text))
            except:
                continue
        
        # 选择下载按钮
        for item, text in visible_items:
            if '下载' in text or 'download' in text.lower():
                return item
        
        print("❌ 未找到下载菜单")
        return None
    
    def find_word_option(self):
        """查找Word选项 - 快速版"""
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
        
        # 过滤有效选项
        visible_format_items = []
        for item in format_items:
            try:
                item_text = item.text.strip()
                is_displayed = item.is_displayed()
                element_tag = item.tag_name
                
                # 过滤掉无效元素和脚本标签
                if (is_displayed and 
                    item_text and 
                    element_tag not in ['script', 'style', 'meta', 'link']):
                    visible_format_items.append((item, item_text))
            except Exception as e:
                continue
        
        # 优先选择Word格式
        for item, text in visible_format_items:
            if 'Word' in text or 'word' in text.lower() or 'docx' in text.lower():
                return item
        
        # 备选方案
        if visible_format_items:
            item, text = visible_format_items[0]
            return item
        
        print("❌ 未找到任何可用的格式选项")
        return None
    
    def click_word_button_smart(self, word_button):
        """智能点击Word按钮"""
        print("🖱️ 点击Word按钮...")
        
        # 按成功率排序的点击方法
        methods = [
            lambda: word_button.click(),
            lambda: ActionChains(self.driver).move_to_element(word_button).click().perform(),
            lambda: self.driver.execute_script("arguments[0].click();", 
                                              word_button.find_element(By.XPATH, "./.."))
        ]
        
        for method_func in methods:
            try:
                method_func()
                time.sleep(1)  # 最小等待时间
                print("  ✅ Word按钮点击成功")
                return True
            except Exception as e:
                continue
        
        print("❌ 所有点击方法都失败")
        return False
    
    def find_and_click_export_content_comments(self):
        """查找并点击"导出正文及评论"选项"""
        print("📝 查找导出选项...")
        
        # 等待导出设置弹窗出现
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, 
                "//*[contains(text(), '导出正文及评论') or contains(text(), '仅正文')]")))
            time.sleep(1)  # 等待弹窗完全加载
        except TimeoutException:
            print("❌ 导出设置弹窗未出现")
            return False
        
        # 查找"导出正文及评论"选项
        try:
            # 多种选择器策略查找单选按钮
            selectors = [
                # 直接查找包含"导出正文及评论"文本的元素
                "//*[contains(text(), '导出正文及评论')]",
                # 查找单选按钮类型的input元素
                "//input[@type='radio']//following-sibling::*[contains(text(), '导出正文及评论')] | //input[@type='radio']//preceding-sibling::*[contains(text(), '导出正文及评论')]",
                # 查找label元素
                "//label[contains(text(), '导出正文及评论')]"
            ]
            
            export_option_element = None
            
            for selector in selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed():
                            export_option_element = element
                            break
                    except:
                        continue
                if export_option_element:
                    break
            
            if not export_option_element:
                print("❌ 未找到'导出正文及评论'选项")
                return False
            
            print("✅ 找到'导出正文及评论'选项")
            
            # 尝试点击该选项
            # 方法1: 直接点击元素
            try:
                export_option_element.click()
                print("✅ 成功点击'导出正文及评论'选项")
                time.sleep(0.5)
                return True
            except:
                pass
            
            # 方法2: JavaScript点击
            try:
                self.driver.execute_script("arguments[0].click();", export_option_element)
                print("✅ 通过JavaScript成功点击'导出正文及评论'选项")
                time.sleep(0.5)
                return True
            except:
                pass
            
            # 方法3: 查找对应的radio按钮
            try:
                # 查找附近的单选按钮
                parent = export_option_element.find_element(By.XPATH, "./..")
                radio_button = parent.find_element(By.XPATH, ".//input[@type='radio']")
                if not radio_button.is_selected():
                    radio_button.click()
                    print("✅ 成功点击单选按钮选择'导出正文及评论'")
                    time.sleep(0.5)
                    return True
            except:
                pass
            
            print("❌ 无法点击'导出正文及评论'选项")
            return False
            
        except Exception as e:
            print(f"❌ 处理导出选项时出错: {e}")
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
            # 备选方案：简化查找
            export_buttons = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), '导出') or contains(text(), 'export')]")
            
            visible_export_buttons = []
            for button in export_buttons:
                try:
                    if button.is_displayed() and button.is_enabled() and button.text.strip():
                        visible_export_buttons.append((button, button.text.strip()))
                except Exception as e:
                    continue
            
            # 选择最合适的导出按钮
            for button, text in visible_export_buttons:
                if text == '导出' or text.lower() == 'export':
                    self.driver.execute_script("arguments[0].click();", button)
                    return True
            
            # 次优选择
            for button, text in visible_export_buttons:
                if ('导出' in text or 'export' in text.lower()) and '设置' not in text:
                    self.driver.execute_script("arguments[0].click();", button)
                    return True
        
        print("❌ 未找到导出按钮")
        return False
    
    def execute_download_steps(self):
        """执行下载步骤的核心逻辑（不包含重试）"""
        # 验证页面
        current_url = self.driver.current_url
        if '/wiki/' not in current_url:
            print("❌ 请先导航到文档页面")
            return False
        
        doc_title = self.driver.title
        print(f"📄 文档: {doc_title[:50]}...")
        
        # 确保output目录存在
        output_dir = "/Users/abc/PycharmProjects/knowledge_base/.venv/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 滚动到顶部
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # 步骤1: 查找并点击三个点按钮
        three_dots_button = self.find_three_dots_button()
        if not three_dots_button:
            return False
        
        self.driver.execute_script("arguments[0].click();", three_dots_button)
        
        # 步骤2: 查找并悬停下载菜单
        download_button = self.find_download_menu_item()
        if not download_button:
            return False
        
        actions = ActionChains(self.driver)
        actions.move_to_element(download_button).perform()
        
        # 等待子菜单出现
        print("⏳ 等待子菜单展开...")
        time.sleep(2)
        
        # 步骤3: 查找并点击Word选项
        word_option = self.find_word_option()
        if not word_option:
            return False
        
        if not self.click_word_button_smart(word_option):
            return False
        
        # 步骤4: 处理导出设置 - 选择"导出正文及评论"
        if not self.find_and_click_export_content_comments():
            print("⚠️ 无法选择导出选项，将继续使用默认设置")
            # 不直接返回False，因为这可能是可选功能
        
        # 步骤5: 智能等待并点击导出按钮
        if not self.click_export_button_smart():
            return False
        
        print("✅ 下载流程完成!")
        print(f"📁 下载目录: {output_dir}")
        
        # 快速检查文件
        print("⏳ 检查下载文件...")
        time.sleep(2)
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print(f"📂 找到 {len(files)} 个文件")
            else:
                print("ℹ️ 文件可能仍在下载中...")
        
        return True
    
    def download_document(self):
        """带重试机制的完整下载流程"""
        try:
            driver = self.setup_driver()
            
            print("📥 带重试机制的快速文档下载流程")
            print("=" * 40)
            
            for attempt in range(self.max_retries + 1):  # 0, 1, 2, 3 - 总共4次尝试
                if attempt > 0:
                    print(f"\n🔄 第 {attempt} 次重试 (共 {self.max_retries} 次)")
                    print(f"⏳ 等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                    
                    # 重置页面状态
                    self.reset_page_state()
                
                print(f"\n📋 尝试 {attempt + 1}/{self.max_retries + 1}")
                print("-" * 30)
                
                # 执行下载步骤
                success = self.execute_download_steps()
                
                if success:
                    if attempt > 0:
                        print(f"🎉 第 {attempt} 次重试成功!")
                    return True
                else:
                    if attempt < self.max_retries:
                        print(f"❌ 第 {attempt + 1} 次尝试失败")
                    else:
                        print("❌ 所有重试尝试都已失败")
            
            # 所有重试都失败了，记录详细失败日志
            print("\n" + "=" * 60)
            print("🔴 **下载最终失败报告**")
            print("=" * 60)
            print(f"📊 总尝试次数: {self.max_retries + 1} 次")
            print(f"⏱️ 重试间隔: {self.retry_delay} 秒")
            print(f"🔗 当前URL: {driver.current_url}")
            print(f"📄 页面标题: {driver.title}")
            print(f"🖥️ 窗口大小: {self.window_size}")
            print("💡 建议检查:")
            print("   1. 确保Chrome调试模式正常运行 (端口9222)")
            print("   2. 确认当前页面是飞书文档页面")
            print("   3. 检查页面是否完全加载")
            print("   4. 确认文档有下载权限")
            print("   5. 检查网络连接状态")
            print("=" * 60)
            
            return False
            
        except Exception as e:
            print(f"❌ 系统级错误: {e}")
            print("💡 这通常表示Chrome连接或WebDriver问题")
            return False

def main():
    print("🚀 带重试机制的快速文档下载器")
    print("智能重试：失败后自动等待10秒重试，最多重试3次")
    print("=" * 60)
    
    # 检查基本环境
    print("环境检查:")
    print("1. Chrome调试模式 (端口9222)")
    print("2. 已导航到飞书文档页面")
    print("3. 页面完全加载")
    print()
    
    print("开始智能下载...")
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行下载
    downloader = FastFeishuDownloader()
    success = downloader.download_document()
    
    # 计算执行时间
    end_time = time.time()
    execution_time = end_time - start_time
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 下载成功!")
    else:
        print("❌ 下载最终失败")
    
    print(f"⏱️ 总执行时间: {execution_time:.1f}秒")
    
    if not success:
        print("💡 如需人工介入，请检查上述失败报告中的建议")

if __name__ == "__main__":
    main()