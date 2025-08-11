#!/usr/bin/env python3
"""
测试快捷键控制功能
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from hotkey_controller import HotkeyController, DownloadState
from floating_ui import FloatingUI

def test_hotkey_controller():
    """测试快捷键控制器"""
    print("=" * 50)
    print("测试 1: 快捷键控制器")
    print("=" * 50)
    
    def on_start():
        print("🚀 启动回调触发!")
    
    def on_stop():
        print("⏹️ 停止回调触发!")
    
    try:
        controller = HotkeyController(on_start, on_stop)
        print("✅ 快捷键控制器创建成功")
        
        with controller:
            print("快捷键监听已启动，测试10秒...")
            print("请尝试:")
            print("- 双击空格键 (启动)")
            print("- 按ESC键 (停止)")
            
            for i in range(10):
                print(f"状态: {controller.state.value} ({i+1}/10)")
                time.sleep(1)
        
        print("✅ 快捷键控制器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 快捷键控制器测试失败: {e}")
        return False

def test_floating_ui():
    """测试悬浮UI"""
    print("\n" + "=" * 50)
    print("测试 2: 悬浮UI")
    print("=" * 50)
    
    try:
        print("连接Chrome...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome连接成功")
        print(f"当前页面: {driver.title}")
        
        # 创建悬浮UI
        ui = FloatingUI(driver)
        print("✅ 悬浮UI创建成功")
        
        # 注入UI
        ui.inject_ui()
        print("✅ UI注入成功，请查看页面左上角")
        
        # 测试状态切换
        states = [
            (DownloadState.READY, "准备状态", 3),
            (DownloadState.RUNNING, "运行状态", 3),
            (DownloadState.STOPPED, "停止状态", 3),
            (DownloadState.READY, "重置为准备状态", 2)
        ]
        
        for state, desc, duration in states:
            print(f"切换到{desc}...")
            ui.update_status(state)
            time.sleep(duration)
        
        print("测试UI修复功能...")
        ui.check_and_repair()
        
        print("✅ 悬浮UI测试完成，5秒后清理...")
        time.sleep(5)
        ui.remove_ui()
        print("✅ UI已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 悬浮UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_features():
    """测试集成功能"""
    print("\n" + "=" * 50)
    print("测试 3: 集成功能")
    print("=" * 50)
    
    try:
        print("连接Chrome...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome连接成功")
        
        # 创建组件
        ui = FloatingUI(driver)
        
        state_changes = []
        
        def on_start():
            state_changes.append("启动")
            ui.update_status(DownloadState.RUNNING)
            print("🚀 系统启动!")
        
        def on_stop():
            state_changes.append("停止")
            ui.update_status(DownloadState.STOPPED)
            print("⏹️ 系统停止!")
        
        controller = HotkeyController(on_start, on_stop)
        
        # 初始化UI
        ui.inject_ui()
        ui.update_status(DownloadState.READY)
        
        print("✅ 集成系统初始化完成")
        print("开始15秒集成测试...")
        print("请测试:")
        print("- 双击空格键启动")
        print("- ESC键停止")
        print("- 观察左上角状态变化")
        
        with controller:
            for i in range(15):
                print(f"测试进度: {i+1}/15, 当前状态: {controller.state.value}")
                ui.check_and_repair()  # 确保UI正常
                time.sleep(1)
        
        ui.remove_ui()
        
        print("✅ 集成功能测试完成")
        print(f"状态变化记录: {state_changes}")
        return True
        
    except Exception as e:
        print(f"❌ 集成功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("飞书下载器快捷键功能测试套件")
    print("=" * 60)
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    tests = [
        ("快捷键控制器", test_hotkey_controller),
        ("悬浮UI", test_floating_ui), 
        ("集成功能", test_integrated_features)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🧪 开始测试: {name}")
        try:
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断测试: {name}")
            results.append((name, False))
            break
        except Exception as e:
            print(f"❌ 测试异常: {name} - {e}")
            results.append((name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过! 功能集成成功!")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main()