#!/usr/bin/env python3
"""
悬浮UI诊断工具
专门诊断为什么悬浮框不显示
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

def test_chrome_connection():
    """测试Chrome连接"""
    print("🔍 测试1: Chrome连接")
    print("-" * 40)
    
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome连接成功")
        print(f"页面标题: {driver.title}")
        print(f"页面URL: {driver.current_url}")
        return driver
    except WebDriverException as e:
        print(f"❌ Chrome连接失败: {e}")
        print("\n请先启动Chrome调试模式:")
        print("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        return None

def test_basic_injection(driver):
    """测试基本注入功能"""
    print("\n🔍 测试2: JavaScript注入")
    print("-" * 40)
    
    try:
        # 测试简单的JavaScript执行
        result = driver.execute_script("return 'JavaScript可以执行'")
        print(f"✅ JavaScript执行结果: {result}")
        
        # 测试DOM操作
        driver.execute_script("console.log('飞书下载器测试')")
        print("✅ Console.log执行成功")
        
        return True
    except Exception as e:
        print(f"❌ JavaScript注入失败: {e}")
        return False

def test_simple_element_injection(driver):
    """测试简单元素注入"""
    print("\n🔍 测试3: 简单元素注入")
    print("-" * 40)
    
    try:
        # 注入一个简单的测试元素
        test_html = """
        <div id="test-element" style="
            position: fixed;
            top: 10px;
            left: 10px;
            background: red;
            color: white;
            padding: 10px;
            z-index: 999999;
            font-size: 14px;
            border-radius: 5px;
        ">测试元素</div>
        """
        
        driver.execute_script(f"document.body.insertAdjacentHTML('beforeend', `{test_html}`);")
        print("✅ 测试元素注入成功")
        
        # 等待3秒让用户看到
        print("请查看页面左上角是否有红色的'测试元素'...")
        time.sleep(3)
        
        # 检查元素是否存在
        exists = driver.execute_script("return document.getElementById('test-element') !== null;")
        print(f"✅ 元素存在检查: {exists}")
        
        # 移除测试元素
        driver.execute_script("document.getElementById('test-element').remove();")
        print("✅ 测试元素已移除")
        
        return True
    except Exception as e:
        print(f"❌ 简单元素注入失败: {e}")
        return False

def test_full_ui_injection(driver):
    """测试完整UI注入"""
    print("\n🔍 测试4: 完整悬浮UI注入")
    print("-" * 40)
    
    try:
        # CSS样式
        css_style = """
        #feishu-downloader-status {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 999999;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            min-width: 120px;
            text-align: center;
            user-select: none;
            pointer-events: none;
            transition: all 0.3s ease;
        }
        """
        
        # HTML结构
        html_structure = """
        <div id="feishu-downloader-status">
            <span style="margin-right: 8px;">🔧</span>
            <span>准备</span>
        </div>
        """
        
        # 注入CSS
        driver.execute_script(f"""
            if (!document.getElementById('feishu-downloader-style')) {{
                var style = document.createElement('style');
                style.id = 'feishu-downloader-style';
                style.textContent = `{css_style}`;
                document.head.appendChild(style);
                console.log('CSS样式注入成功');
            }}
        """)
        print("✅ CSS样式注入成功")
        
        # 注入HTML
        driver.execute_script(f"""
            if (!document.getElementById('feishu-downloader-status')) {{
                document.body.insertAdjacentHTML('beforeend', `{html_structure}`);
                console.log('HTML结构注入成功');
            }}
        """)
        print("✅ HTML结构注入成功")
        
        # 检查元素是否存在并可见
        element_info = driver.execute_script("""
            var element = document.getElementById('feishu-downloader-status');
            if (!element) return {exists: false};
            
            var rect = element.getBoundingClientRect();
            var styles = window.getComputedStyle(element);
            
            return {
                exists: true,
                visible: styles.display !== 'none' && styles.visibility !== 'hidden',
                position: {top: rect.top, left: rect.left, width: rect.width, height: rect.height},
                zIndex: styles.zIndex,
                background: styles.background
            };
        """)
        
        print(f"✅ 元素信息: {element_info}")
        
        if element_info['exists']:
            print("✅ 悬浮UI注入成功！请查看页面左上角")
            print("等待10秒供您查看...")
            time.sleep(10)
            
            # 清理
            driver.execute_script("""
                var element = document.getElementById('feishu-downloader-status');
                var style = document.getElementById('feishu-downloader-style');
                if (element) element.remove();
                if (style) style.remove();
            """)
            print("✅ UI已清理")
            return True
        else:
            print("❌ 悬浮UI元素未正确创建")
            return False
            
    except Exception as e:
        print(f"❌ 完整UI注入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_page_compatibility(driver):
    """测试页面兼容性"""
    print("\n🔍 测试5: 页面兼容性")
    print("-" * 40)
    
    try:
        # 获取页面基本信息
        page_info = driver.execute_script("""
            return {
                url: window.location.href,
                title: document.title,
                hasJQuery: typeof jQuery !== 'undefined',
                bodyChildren: document.body.children.length,
                contentSecurityPolicy: document.querySelector('meta[http-equiv="Content-Security-Policy"]') ? 
                    document.querySelector('meta[http-equiv="Content-Security-Policy"]').content : null,
                doctype: document.doctype ? document.doctype.name : null
            };
        """)
        
        print(f"页面URL: {page_info['url']}")
        print(f"页面标题: {page_info['title']}")
        print(f"是否有jQuery: {page_info['hasJQuery']}")
        print(f"Body子元素数量: {page_info['bodyChildren']}")
        print(f"Content Security Policy: {page_info['contentSecurityPolicy']}")
        print(f"文档类型: {page_info['doctype']}")
        
        # 检查是否是飞书页面
        is_feishu = 'feishu' in page_info['url'].lower() or 'lark' in page_info['url'].lower()
        print(f"是否为飞书页面: {is_feishu}")
        
        if page_info['contentSecurityPolicy']:
            print("⚠️ 检测到Content Security Policy，可能会阻止脚本注入")
        
        return True
    except Exception as e:
        print(f"❌ 页面兼容性检查失败: {e}")
        return False

def main():
    """主诊断流程"""
    print("飞书下载器 - 悬浮UI诊断工具")
    print("=" * 50)
    
    # 测试Chrome连接
    driver = test_chrome_connection()
    if not driver:
        return
    
    try:
        # 运行所有测试
        tests = [
            ("JavaScript注入", lambda: test_basic_injection(driver)),
            ("简单元素注入", lambda: test_simple_element_injection(driver)),
            ("页面兼容性", lambda: test_page_compatibility(driver)),
            ("完整UI注入", lambda: test_full_ui_injection(driver))
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"❌ 测试 {name} 出现异常: {e}")
                results.append((name, False))
        
        # 输出测试结果
        print("\n" + "=" * 50)
        print("诊断结果汇总:")
        print("=" * 50)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{name}: {status}")
        
        # 给出建议
        print("\n建议:")
        if not all(result for _, result in results):
            print("❌ 某些测试失败，请检查:")
            print("1. Chrome调试模式是否正确启动")
            print("2. 当前页面是否支持脚本注入")
            print("3. 是否有安全策略阻止DOM操作")
        else:
            print("✅ 所有测试通过！悬浮UI应该可以正常显示")
            print("如果在主程序中仍然看不到，请检查主程序的UI注入时机")
            
    except KeyboardInterrupt:
        print("\n用户中断诊断")
    finally:
        print("\n诊断完成，Chrome保持打开状态")

if __name__ == "__main__":
    main()