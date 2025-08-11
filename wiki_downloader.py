#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书知识库批量下载器 - 专门适配知识库结构
"""

from feishu_downloader import FeishuDownloader
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

class WikiDownloader(FeishuDownloader):
    """知识库专用下载器"""
    
    def get_document_links(self):
        """获取知识库中的文档链接 - 重写父类方法"""
        try:
            print("🔍 分析知识库结构...")
            self.wait_for_page_load()
            
            # 1. 查找并展开目标文件夹
            target_folders = ['新人园地-通关宝典']  # 可以添加更多文件夹
            
            all_docs = []
            
            for folder_name in target_folders:
                print(f"\n📁 处理文件夹: {folder_name}")
                docs_in_folder = self._expand_folder_and_get_docs(folder_name)
                all_docs.extend(docs_in_folder)
            
            if not all_docs:
                self.logger.warning("未找到可下载的文档")
                return []
            
            self.logger.info(f"共找到 {len(all_docs)} 个文档可下载")
            return all_docs
            
        except Exception as e:
            self.logger.error(f"获取知识库文档链接失败: {e}")
            return []
    
    def _expand_folder_and_get_docs(self, folder_name):
        """展开指定文件夹并获取其中的文档"""
        try:
            # 查找文件夹节点
            doc_nodes = self.driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
            target_folder = None
            
            for node in doc_nodes:
                text = node.text.strip()
                if folder_name in text:
                    print(f"✅ 找到文件夹: {text}")
                    target_folder = node.find_element(By.XPATH, './..')
                    break
            
            if not target_folder:
                print(f"❌ 未找到文件夹: {folder_name}")
                return []
            
            # 点击展开文件夹
            print("展开文件夹...")
            self.driver.execute_script("arguments[0].click();", target_folder)
            time.sleep(4)  # 增加等待时间确保DOM更新
            
            # 查找子文档 - 使用更稳定的方法
            found_docs = []
            
            # 知识库中常见的文档关键词
            doc_keywords = ['新人须知', '新人办公', '部门初相识', '新人学习', '新人培养', '新人必读', '组织文化']
            
            # 分批处理，避免一次处理太多元素导致问题
            for keyword in doc_keywords:
                doc_info = self._find_and_process_doc_by_keyword(keyword)
                if doc_info:
                    found_docs.append(doc_info)
                    print(f"✅ 添加文档: {doc_info['title']}")
                
                # 小延迟避免操作过快
                time.sleep(1)
            
            return found_docs
            
        except Exception as e:
            self.logger.error(f"展开文件夹失败: {e}")
            return []
    
    def _find_and_process_doc_by_keyword(self, keyword):
        """根据关键词查找并处理文档"""
        try:
            # 每次重新查找元素避免stale reference
            updated_nodes = self.driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
            
            for node in updated_nodes:
                text = node.text.strip()
                if text and keyword in text:
                    print(f"  处理文档: {text}")
                    
                    # 获取文档URL
                    doc_url = self._get_doc_url_by_text(text)
                    
                    if doc_url:
                        return {
                            'title': text,
                            'url': doc_url,
                            'type': 'wiki_doc'
                        }
                    else:
                        print(f"  ❌ 无法获取URL: {text}")
                        return None
            
            return None
            
        except Exception as e:
            print(f"  处理文档异常 {keyword}: {e}")
            return None
    
    def _get_doc_url_by_text(self, doc_title):
        """根据文档标题获取URL"""
        try:
            # 重新查找元素
            all_nodes = self.driver.find_elements(By.CSS_SELECTOR, '.workspace-tree-view-node-content')
            
            for node in all_nodes:
                if node.text.strip() == doc_title:
                    parent = node.find_element(By.XPATH, './..')
                    original_url = self.driver.current_url
                    
                    # 使用JavaScript双击
                    self.driver.execute_script("""
                        arguments[0].click();
                        setTimeout(function() {
                            arguments[0].click();
                        }, 100);
                    """, parent)
                    
                    time.sleep(4)  # 等待页面跳转
                    new_url = self.driver.current_url
                    
                    if new_url != original_url and '/wiki/' in new_url:
                        print(f"    ✅ 获取到URL: {new_url}")
                        return new_url
                    else:
                        print(f"    ❌ URL无变化: {doc_title}")
                        return None
            
            print(f"    ❌ 未找到元素: {doc_title}")
            return None
            
        except Exception as e:
            print(f"    ❌ 获取URL异常: {e}")
            return None
    
    
    def download_document(self, doc_info):
        """重写下载方法适配知识库"""
        try:
            if doc_info.get('type') == 'wiki_doc':
                # 知识库文档的下载逻辑
                return self._download_wiki_document(doc_info)
            else:
                # 使用父类的下载方法
                return super().download_document(doc_info)
                
        except Exception as e:
            self.logger.error(f"下载文档失败: {e}")
            return False
    
    def _download_wiki_document(self, doc_info):
        """下载知识库文档"""
        try:
            self.logger.info(f"下载知识库文档: {doc_info['title']}")
            
            # 导航到文档页面
            self.driver.get(doc_info['url'])
            self.wait_for_page_load()
            
            # 滚动到页面顶部确保按钮可见
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 使用与测试脚本相同的成功方法查找右上角按钮
            print(f"🔍 查找右上角三个点按钮...")
            
            # 查找所有按钮 - 采用测试脚本的成功方法
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
            window_size = self.driver.get_window_size()
            print(f"页面大小: {window_size['width']} x {window_size['height']}")
            print(f"找到 {len(all_buttons)} 个按钮元素")
            
            more_button = None
            right_top_buttons = []
            
            for i, button in enumerate(all_buttons):
                try:
                    if button.is_displayed() and button.is_enabled():
                        location = button.location
                        
                        # 检查是否在右上角区域 - 与测试脚本相同的判断逻辑
                        is_right_top = (location['x'] > window_size['width'] * 0.66 and 
                                       location['y'] < window_size['height'] * 0.33)
                        
                        if is_right_top:
                            text = button.text.strip()
                            aria_label = button.get_attribute('aria_label') or ""
                            title = button.get_attribute('title') or ""
                            class_name = button.get_attribute('class') or ""
                            
                            print(f"找到右上角按钮 {i+1}: 位置({location['x']}, {location['y']}) "
                                  f"文本:'{text}' 标签:'{aria_label}' 标题:'{title}'")
                            
                            # 跳过"编辑"、"分享"等明确不是更多操作的按钮
                            if text in ['编辑', '分享', '编辑', 'Edit', 'Share']:
                                print(f"  ⏭️ 跳过:{text}按钮")
                                continue
                            
                            # 优先选择没有文本的图标按钮（通常是三个点）
                            if not text and not more_button:
                                more_button = button
                                print(f"✅ 选择图标按钮: 按钮{i+1}")
                            # 或者选择包含"更多"、"菜单"等关键词的按钮
                            elif any(keyword in (text + aria_label + title).lower() 
                                   for keyword in ['more', 'menu', '更多', '菜单', '⋯', '…']):
                                if not more_button:
                                    more_button = button
                                    print(f"✅ 选择更多操作按钮: {text or aria_label or title}")
                            
                            right_top_buttons.append(button)
                        
                except Exception as e:
                    continue
            
            print(f"共找到 {len(right_top_buttons)} 个右上角按钮")
            
            # 如果没找到位置特定的按钮，尝试查找包含"更多"或"菜单"文本的按钮
            if not more_button:
                print("🔍 查找包含'更多'或'菜单'文本的按钮...")
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")
                
                for button in all_buttons:
                    try:
                        text = button.text.strip()
                        aria_label = button.get_attribute('aria-label') or ""
                        title = button.get_attribute('title') or ""
                        
                        if any(keyword in text + aria_label + title for keyword in ['更多', '菜单', 'more', 'menu', '⋯', '…']):
                            if button.is_displayed() and button.is_enabled():
                                more_button = button
                                print(f"✅ 找到更多操作按钮: {text or aria_label or title}")
                                break
                    except:
                        continue
            
            if not more_button:
                self.logger.warning("未找到更多操作按钮（三个点）")
                self.record_download(doc_info['title'], doc_info['url'], "未找到三个点按钮")
                return False
            
            # 点击三个点按钮
            print("🖱️ 点击三个点按钮...")
            self.driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)
            
            # 查找菜单项 - 采用与测试脚本相同的方法
            print("🔍 查找下载相关菜单项...")
            time.sleep(1)  # 等待菜单完全展开
            
            # 查找包含"下载"的菜单项
            download_items = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), '下载') or contains(text(), '导出') or contains(text(), 'download') or contains(text(), 'export')]")
            
            print(f"找到 {len(download_items)} 个下载相关菜单项")
            
            download_option = None
            for i, item in enumerate(download_items):
                try:
                    if item.is_displayed():
                        item_text = item.text.strip()
                        print(f"菜单项 {i+1}: '{item_text}'")
                        
                        # 优先选择"下载为"
                        if '下载' in item_text:
                            download_option = item
                            print(f"✅ 选择菜单项: {item_text}")
                            break
                except Exception as e:
                    continue
            
            if not download_option and download_items:
                # 如果没有找到"下载为"，选择第一个可用的下载项
                for item in download_items:
                    if item.is_displayed():
                        download_option = item
                        print(f"✅ 使用菜单项: {item.text}")
                        break
            
            if not download_option:
                print("❌ 未找到下载菜单项")
                self.record_download(doc_info['title'], doc_info['url'], "未找到下载菜单项")
                return False
            
            # 点击下载菜单项
            print("🖱️ 点击下载菜单项...")
            self.driver.execute_script("arguments[0].click();", download_option)
            time.sleep(2)
            
            # 查找下载格式选项
            print("🔍 查找下载格式选项...")
            format_items = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Word') or contains(text(), 'PDF') or contains(text(), 'docx') or contains(text(), 'pdf')]")
            
            print(f"找到 {len(format_items)} 个格式选项")
            
            format_option = None
            for i, item in enumerate(format_items):
                try:
                    if item.is_displayed():
                        item_text = item.text.strip()
                        print(f"格式选项 {i+1}: '{item_text}'")
                        
                        # 优先选择Word格式
                        if 'Word' in item_text or 'word' in item_text.lower():
                            format_option = item
                            print(f"✅ 选择格式: {item_text}")
                            break
                except Exception as e:
                    continue
            
            # 如果没找到Word，选择第一个可用格式
            if not format_option and format_items:
                for item in format_items:
                    if item.is_displayed() and item.text.strip():
                        format_option = item
                        print(f"✅ 使用格式: {item.text}")
                        break
            
            # 如果还是没找到，尝试查找通用菜单项
            if not format_option:
                print("🔍 查找通用菜单项...")
                all_menu_items = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[role='menuitem'], .menu-item, li, div[class*='menu'], div[class*='option']")
                
                for item in all_menu_items:
                    try:
                        if item.is_displayed() and item.text.strip():
                            format_option = item
                            print(f"✅ 使用通用选项: {item.text}")
                            break
                    except:
                        continue
            
            if not format_option:
                print("❌ 未找到任何格式选项")
                self.record_download(doc_info['title'], doc_info['url'], "未找到格式选项")
                return False
            
            # 点击格式选项
            print("🖱️ 点击格式选项...")
            self.driver.execute_script("arguments[0].click();", format_option)
            time.sleep(3)
            
            self.logger.info(f"文档 {doc_info['title']} 下载请求已发送")
            self.record_download(doc_info['title'], doc_info['url'], "成功")
            self.stats["successful_downloads"] += 1
            return True
                
        except Exception as e:
            self.logger.error(f"下载知识库文档异常: {e}")
            self.record_download(doc_info['title'], doc_info['url'], f"异常: {str(e)}")
            self.stats["failed_downloads"] += 1
            return False

def main():
    """主函数"""
    print("飞书知识库批量下载器 v1.0")
    print("=" * 50)
    print("专门适配知识库文件夹结构")
    print()
    
    # 使用知识库专用下载器
    downloader = WikiDownloader()
    
    try:
        downloader.run()
    except KeyboardInterrupt:
        print("\n用户中断下载")
    except Exception as e:
        print(f"运行错误: {e}")

if __name__ == "__main__":
    main()