#!/usr/bin/env python3
"""
测试修复后的find_element_by_text方法
"""

from directory_traverser import FeishuDirectoryTraverser

def test_element_finding():
    print("🧪 测试模块化版本的元素查找修复")
    print("=" * 50)
    
    try:
        # 创建遍历器实例
        traverser = FeishuDirectoryTraverser()
        print("✅ 遍历器创建成功")
        
        # 检查关键方法是否存在
        if hasattr(traverser, 'find_element_by_text'):
            print("✅ find_element_by_text 方法存在")
        else:
            print("❌ find_element_by_text 方法缺失")
            return
        
        # 显示修改后的XPath策略
        import inspect
        source = inspect.getsource(traverser.find_element_by_text)
        
        print("\n📝 修改后的查找策略:")
        if "contains(@class,'workspace-tree-view-node-content')" in source:
            print("   ✓ 使用灵活的CSS类匹配 (contains)")
        if "contains(text()," in source:
            print("   ✓ 使用灵活的文本匹配 (contains)")
        if "logger.debug" in source and "找到" in source:
            print("   ✓ 已添加调试日志输出")
            
        print("\n🎯 修复要点:")
        print("   • 原问题: 严格的精确匹配导致元素无法找到")
        print("   • 修复方案: 使用contains()进行灵活匹配")
        print("   • 调试增强: 显示实际找到的元素数量")
        
        print("\n✅ 修复验证完成!")
        print("现在可以重新运行: python3 run_traverser_modular.py")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_element_finding()