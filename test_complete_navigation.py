#!/usr/bin/env python3
"""
完整路径-名称映射导航方案测试脚本
验证新实现的断点续传导航逻辑
"""

import sys
import os
sys.path.insert(0, '/Users/abc/PycharmProjects/knowledge')

from directory_traverser.traverser_core import FeishuDirectoryTraverser

def test_path_name_mapping():
    """测试路径-名称映射构建"""
    print("🧪 测试路径-名称映射构建")
    print("=" * 40)
    
    traverser = FeishuDirectoryTraverser()
    
    # 测试构建映射表
    path_mapping = traverser.build_path_name_mapping()
    
    if path_mapping:
        print(f"✅ 成功构建映射表，包含 {len(path_mapping)} 个路径")
        print("📋 映射表内容:")
        for path, name in sorted(path_mapping.items()):
            print(f"  {path:8} → {name}")
    else:
        print("❌ 构建映射表失败")
        return False
    
    return path_mapping

def test_navigation_path_parsing(path_mapping):
    """测试导航路径解析"""
    print(f"\n🧪 测试导航路径解析")
    print("=" * 30)
    
    traverser = FeishuDirectoryTraverser()
    
    # 测试不同的目标路径
    test_paths = ["1", "1-1", "1-2", "1-2-1", "1-2-2"]
    
    for target_path in test_paths:
        if target_path in path_mapping:
            navigation_path = traverser.get_navigation_path(target_path, path_mapping)
            if navigation_path:
                print(f"✅ {target_path:6} → {navigation_path}")
            else:
                print(f"❌ {target_path:6} → 解析失败")
        else:
            print(f"⚠️ {target_path:6} → 路径不存在于映射表")

def simulate_navigation_process(path_mapping):
    """模拟完整导航过程"""
    print(f"\n🧪 模拟完整导航过程")
    print("=" * 30)
    
    traverser = FeishuDirectoryTraverser()
    
    # 模拟断点续传信息
    resume_info = traverser.check_resume_progress()
    if not resume_info:
        print("❌ 没有断点续传信息")
        return
    
    target_path, target_name = resume_info
    print(f"📍 断点续传信息: {target_path} → {target_name}")
    
    # 解析导航路径
    navigation_path = traverser.get_navigation_path(target_path, path_mapping)
    if not navigation_path:
        print("❌ 无法解析导航路径")
        return
    
    print(f"📍 解析的导航路径: {navigation_path}")
    
    # 模拟导航步骤
    print(f"\n🎯 模拟导航步骤:")
    for level, level_target in enumerate(navigation_path[:-1]):
        print(f"第{level + 1}步: 查找并点击 '{level_target}'")
    
    final_target = navigation_path[-1]
    print(f"第{len(navigation_path)}步: 验证目标 '{final_target}'")
    
    if final_target == target_name:
        print(f"✅ 导航路径验证成功！")
    else:
        print(f"❌ 导航路径验证失败！期望: {target_name}, 实际: {final_target}")

def compare_old_vs_new_approach():
    """对比旧方法和新方法"""
    print(f"\n📊 旧方法 vs 新方法对比")
    print("=" * 35)
    
    print("🔹 旧方法 (索引导航):")
    print("  - 基于路径索引 (如: 1-2-2)")
    print("  - 依赖DOM项目顺序")
    print("  - 容易因页面状态变化失败")
    print("  - 调试信息: 位置索引")
    
    print(f"\n🔹 新方法 (名称导航):")
    print("  - 基于项目名称 (如: 语雀空间权限说明)")
    print("  - 不依赖DOM项目顺序")  
    print("  - 稳定可靠，状态无关")
    print("  - 调试信息: 具体项目名称")
    
    print(f"\n🎯 新方法优势:")
    print("  ✅ 索引偏移问题彻底解决")
    print("  ✅ 错误信息更加明确")
    print("  ✅ 调试和维护更容易")
    print("  ✅ 适应页面结构变化")

def main():
    """主函数"""
    print("🚀 完整路径-名称映射导航方案测试")
    print("=" * 50)
    
    # 测试映射构建
    path_mapping = test_path_name_mapping()
    if not path_mapping:
        return
    
    # 测试路径解析
    test_navigation_path_parsing(path_mapping)
    
    # 模拟导航过程
    simulate_navigation_process(path_mapping)
    
    # 对比分析
    compare_old_vs_new_approach()
    
    print(f"\n💡 测试建议:")
    print("1. 运行 python3 run_traverser_modular.py")
    print("2. 选择断点续传 (y)")
    print("3. 观察新的名称导航日志")
    print("4. 验证是否能正确定位到目标位置")

if __name__ == "__main__":
    main()