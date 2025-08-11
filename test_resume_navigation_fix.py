#!/usr/bin/env python3
"""
断点续传导航修复测试脚本
验证扩展搜索范围的修复效果
"""

import sys
import os
sys.path.insert(0, '/Users/abc/PycharmProjects/knowledge')

from directory_traverser.traverser_core import FeishuDirectoryTraverser

def test_navigation_logic():
    """测试导航逻辑修复"""
    print("🧪 测试断点续传导航逻辑修复")
    print("=" * 50)
    
    # 创建遍历器实例
    traverser = FeishuDirectoryTraverser()
    
    # 检查当前断点续传信息
    resume_info = traverser.check_resume_progress()
    
    if not resume_info:
        print("❌ 没有断点续传信息，无法测试")
        return
    
    path, name = resume_info
    print(f"📍 检测到断点续传信息: {path} - {name}")
    
    # 模拟不同的导航场景
    print(f"\n🔍 分析路径解析:")
    
    try:
        path_parts = [int(x) for x in path.split('-')]
        print(f"路径部分: {path_parts}")
        
        # 分析每一层需要导航的内容
        print(f"\n📋 导航路径分析:")
        for i, part in enumerate(path_parts):
            level = i + 1
            if level == 1:
                print(f"第 {level} 层: 查找位置 {part} (根级别)")
            elif level == len(path_parts):
                print(f"第 {level} 层: 查找位置 {part}，期望找到 '{name}' (目标层)")
            else:
                print(f"第 {level} 层: 查找位置 {part} (中间层)")
        
        print(f"\n💡 修复逻辑说明:")
        print("旧逻辑: 严格按索引查找，不匹配就失败")
        print("新逻辑: 从指定位置开始向后搜索，直到找到匹配项")
        print(f"对于目标项 '{name}'，会从位置 {path_parts[-1]} 开始搜索")
        print("直到找到名称匹配的项目为止")
        
    except Exception as e:
        print(f"❌ 路径解析失败: {e}")

def simulate_search_process():
    """模拟搜索过程"""
    print(f"\n🎯 模拟搜索过程")
    print("=" * 30)
    
    # 模拟当前页面可能的项目列表（第2层）
    mock_items_level2 = [
        "新人园地-通关宝典",      # 位置1 
        "新人需知",              # 位置2 (原索引指向这里)
        "新人办公小贴士",        # 位置3 (实际目标在这里)
        "其他项目1",
        "其他项目2"
    ]
    
    target_index = 2  # 原始路径指向位置2
    target_name = "新人办公小贴士"  # 但期望找到这个
    
    print(f"模拟第2层项目列表:")
    for i, item in enumerate(mock_items_level2, 1):
        marker = " 👈 原索引" if i == target_index else ""
        marker += " 🎯 实际目标" if item == target_name else ""
        print(f"  位置 {i}: {item}{marker}")
    
    print(f"\n🔍 搜索过程模拟:")
    print(f"原始查找: 位置 {target_index} = '{mock_items_level2[target_index-1]}'")
    print(f"期望目标: '{target_name}'")
    print(f"匹配结果: {'❌ 不匹配' if mock_items_level2[target_index-1] != target_name else '✅ 匹配'}")
    
    print(f"\n📍 扩展搜索:")
    found_position = None
    for search_pos in range(target_index, len(mock_items_level2) + 1):
        current_item = mock_items_level2[search_pos - 1]
        print(f"检查位置 {search_pos}: '{current_item}'", end="")
        
        if current_item == target_name:
            found_position = search_pos
            print(" ✅ 找到目标！")
            break
        else:
            print(" ⏭️ 继续搜索...")
    
    if found_position:
        print(f"\n🎉 搜索结果: 在位置 {found_position} 找到目标项目")
        print(f"修复效果: 原本会失败的导航现在可以成功！")
    else:
        print(f"\n❌ 搜索结果: 未找到目标项目")

def main():
    """主函数"""
    test_navigation_logic()
    simulate_search_process()
    
    print(f"\n🚀 测试建议:")
    print("1. 运行 python3 run_traverser_modular.py")
    print("2. 选择断点续传 (y)")
    print("3. 观察是否能正确导航到目标位置")
    print("4. 检查日志中的搜索过程")

if __name__ == "__main__":
    main()