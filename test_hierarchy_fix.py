#!/usr/bin/env python3
"""
层级识别修复测试脚本
验证修改后的层级记录逻辑是否正确
"""

import os
import csv
from directory_traverser.traverser_core import FeishuDirectoryTraverser

def analyze_hierarchy_structure():
    """分析当前CSV文件的层级结构"""
    print("🔍 分析当前层级结构")
    print("=" * 50)
    
    traverser = FeishuDirectoryTraverser()
    csv_file = os.path.join(traverser.output_dir, "directory_traverse_log.csv")
    
    if not os.path.exists(csv_file):
        print("❌ CSV文件不存在")
        return
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) <= 1:
        print("📭 CSV文件为空或只有标题行")
        return
    
    print(f"📊 总记录数: {len(rows) - 1}")
    print("\n📋 层级结构分析:")
    
    # 按层级深度分类
    level_stats = {}
    parent_child_relations = []
    
    for i, row in enumerate(rows[1:], 1):  # 跳过标题行
        if len(row) >= 2:
            path = row[0].strip()
            name = row[1].strip()
            
            # 计算层级深度
            depth = len(path.split('-'))
            level_stats[depth] = level_stats.get(depth, 0) + 1
            
            print(f"  {path:8} - {name}")
            
            # 检查父子关系
            if depth > 1:
                # 获取父路径（去掉最后一级）
                parent_path = '-'.join(path.split('-')[:-1])
                parent_child_relations.append((parent_path, path, name))
    
    print(f"\n📊 各层级统计:")
    for depth in sorted(level_stats.keys()):
        print(f"  第 {depth} 层: {level_stats[depth]} 个项目")
    
    print(f"\n🔗 父子关系验证:")
    for parent_path, child_path, child_name in parent_child_relations:
        # 查找父项目是否存在
        parent_exists = False
        for row in rows[1:]:
            if len(row) >= 2 and row[0].strip() == parent_path:
                parent_exists = True
                parent_name = row[1].strip()
                break
        
        if parent_exists:
            print(f"  ✅ {child_path} ({child_name}) -> 父项目: {parent_path} ({parent_name})")
        else:
            print(f"  ❌ {child_path} ({child_name}) -> 找不到父项目: {parent_path}")

def check_expected_structure():
    """检查是否符合期望的层级结构"""
    print("\n🎯 期望结构检查")
    print("=" * 30)
    
    expected_structure = [
        ("1", "新人园地-通关宝典"),
        ("1-1", "新人需知"),
        ("1-2", "新人办公小贴士"),
        ("1-2-1", "飞书空间权限说明"),  # 关键：这里应该是1-2-1而不是1-3
    ]
    
    traverser = FeishuDirectoryTraverser()
    csv_file = os.path.join(traverser.output_dir, "directory_traverse_log.csv")
    
    if not os.path.exists(csv_file):
        print("❌ 无法检查，CSV文件不存在")
        return
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    print("检查关键项目的路径编号:")
    for expected_path, expected_name in expected_structure:
        found = False
        for row in rows[1:]:
            if len(row) >= 2:
                actual_path = row[0].strip()
                actual_name = row[1].strip()
                
                if expected_name in actual_name or actual_name in expected_name:
                    if actual_path == expected_path:
                        print(f"  ✅ {expected_name}: {actual_path} (正确)")
                    else:
                        print(f"  ❌ {expected_name}: 期望 {expected_path}, 实际 {actual_path}")
                    found = True
                    break
        
        if not found:
            print(f"  ⚠️ {expected_name}: 未找到")

def main():
    """主函数"""
    analyze_hierarchy_structure()
    check_expected_structure()
    
    print(f"\n💡 使用说明:")
    print("1. 如果发现层级结构不正确，说明修复未生效")
    print("2. 运行 python3 run_traverser_modular.py 测试新逻辑")  
    print("3. '飞书空间权限说明' 应该显示为 1-2-1，而不是 1-3")

if __name__ == "__main__":
    main()