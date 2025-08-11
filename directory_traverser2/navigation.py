#!/usr/bin/env python3
"""
导航模块
处理点击、导航、权限检查等功能
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from typing import Dict


class NavigationMixin:
    """导航功能混入类"""
    
    def wait_with_respect(self):
        """尊重性访问等待 - 2-5秒随机延迟"""
        delay = random.uniform(*self.access_delay)
        self.logger.info(f"⏳ 尊重访问频率，等待 {delay:.1f} 秒...")
        time.sleep(delay)
        return delay
    
    def check_access_permission(self) -> bool:
        """检查页面访问权限"""
        try:
            # 检查URL是否包含权限相关关键词
            current_url = self.driver.current_url.lower()
            forbidden_url_indicators = [
                'login', 'signin', 'auth', '403', 'forbidden', 'denied'
            ]
            
            if any(indicator in current_url for indicator in forbidden_url_indicators):
                return False
            
            # 检查页面内容是否包含权限相关信息
            try:
                page_source = self.driver.page_source.lower()
                forbidden_content_indicators = [
                    '403', 'forbidden', '权限不足', '登录', 'login',
                    '需要权限', 'access denied', '无权访问', '权限错误',
                    'permission denied', '未授权', 'unauthorized'
                ]
                
                if any(indicator in page_source for indicator in forbidden_content_indicators):
                    return False
                
            except Exception:
                # 如果无法获取页面源码，假设有权限
                pass
            
            # 检查页面标题
            try:
                title = self.driver.title.lower()
                if any(indicator in title for indicator in ['登录', 'login', '错误', 'error', '403']):
                    return False
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            self.logger.warning(f"权限检查时出错: {e}")
            return True  # 出错时假设有权限，避免误判
    
    def click_directory_item(self, item: Dict) -> bool:
        """点击目录项并等待页面加载"""
        try:
            element = item['element']
            item_name = item['name']
            is_clickable_node = item.get('is_clickable_node', False)
            
            self.logger.info(f"🖱️ 点击项目: {item_name}")
            
            # 滚动到元素可见位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 对于可点击节点（目录树节点），使用特殊的点击策略
            if is_clickable_node:
                try:
                    # 对于目录树节点，可能需要点击父元素或特定的点击区域
                    parent_element = element.find_element(By.XPATH, "..")
                    
                    # 尝试点击节点本身或其父容器
                    click_targets = [element, parent_element]
                    
                    for target in click_targets:
                        try:
                            if target.is_displayed() and target.is_enabled():
                                self.driver.execute_script("arguments[0].click();", target)
                                time.sleep(2)  # 等待目录节点响应
                                
                                # 检查是否有页面变化或新内容加载
                                current_url_after = self.driver.current_url
                                if current_url_after != self.driver.current_url:
                                    return True
                                    
                                # 检查页面标题是否改变
                                time.sleep(1)
                                return True
                                
                        except Exception:
                            continue
                            
                except Exception:
                    pass
            
            # 传统的链接点击方法
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform()
            ]
            
            for method in click_methods:
                try:
                    method()
                    time.sleep(1)  # 等待页面开始加载
                    break
                except Exception:
                    continue
            else:
                self.logger.warning(f"所有点击方法都失败: {item_name}")
                return False
            
            # 等待页面加载完成
            try:
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(1)  # 额外等待确保内容加载
                return True
            except TimeoutException:
                self.logger.warning(f"页面加载超时: {item_name}")
                return True  # 即使超时也继续，可能页面已部分加载
                
        except Exception as e:
            self.logger.error(f"点击目录项失败: {e}")
            return False
    
    def click_element_safe(self, element, item_name: str) -> bool:
        """安全点击元素，包含多种重试策略"""
        try:
            # 滚动到元素可见位置
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # 尝试多种点击方法
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
                # 尝试点击父元素
                lambda: self.driver.execute_script("arguments[0].click();", element.find_element(By.XPATH, ".."))
            ]
            
            for i, method in enumerate(click_methods):
                try:
                    method()
                    time.sleep(1)
                    return True
                except Exception as e:
                    if i == len(click_methods) - 1:
                        self.logger.debug(f"点击方法 {i+1} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"安全点击元素失败: {e}")
            return False