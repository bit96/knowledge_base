#!/usr/bin/env python3
"""
测试各个组件功能（不需要Chrome连接）
"""
import time
import threading

def test_imports():
    """测试模块导入"""
    print("🔍 测试组件导入")
    print("-" * 40)
    
    try:
        from hotkey_controller import HotkeyController, DownloadState
        print("✅ hotkey_controller 导入成功")
        
        from floating_ui import FloatingUI
        print("✅ floating_ui 导入成功")
        
        import pynput
        print("✅ pynput 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_hotkey_controller():
    """测试快捷键控制器"""
    print("\n🔍 测试快捷键控制器")
    print("-" * 40)
    
    try:
        from hotkey_controller import HotkeyController, DownloadState
        
        # 创建控制器
        events = []
        
        def on_start():
            events.append("启动")
            print("🚀 启动回调触发!")
        
        def on_stop():
            events.append("停止")
            print("⏹️ 停止回调触发!")
        
        controller = HotkeyController(on_start, on_stop)
        print("✅ 快捷键控制器创建成功")
        print(f"✅ 初始状态: {controller.state.value}")
        
        # 测试状态管理
        controller.reset_to_ready()
        print(f"✅ 重置后状态: {controller.state.value}")
        
        # 简短测试快捷键监听
        print("\n开始快捷键监听测试（5秒）...")
        print("请尝试双击空格键或按ESC键")
        
        controller.start_listening()
        time.sleep(5)
        controller.stop_listening()
        
        print(f"✅ 捕获的事件: {events}")
        return True
        
    except Exception as e:
        print(f"❌ 快捷键控制器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_state_enum():
    """测试状态枚举"""
    print("\n🔍 测试状态枚举")
    print("-" * 40)
    
    try:
        from hotkey_controller import DownloadState
        
        states = [DownloadState.READY, DownloadState.RUNNING, DownloadState.STOPPED]
        for state in states:
            print(f"✅ {state.name}: {state.value}")
        
        return True
    except Exception as e:
        print(f"❌ 状态枚举测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("飞书下载器 - 组件功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("状态枚举", test_state_enum),
        ("快捷键控制器", test_hotkey_controller)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断测试: {name}")
            results.append((name, False))
            break
        except Exception as e:
            print(f"❌ 测试 {name} 异常: {e}")
            results.append((name, False))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("组件测试结果:")
    print("=" * 50)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    print("\n下一步:")
    if passed == len(results):
        print("✅ 所有组件测试通过!")
        print("现在需要启动Chrome调试模式来测试UI功能:")
        print("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    else:
        print("❌ 部分组件测试失败，请先解决这些问题")

if __name__ == "__main__":
    main()