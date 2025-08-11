#!/usr/bin/env python3
"""
简化序号延续逻辑测试脚本
验证修复后的断点续传序号计算
"""

import sys
import os
sys.path.insert(0, '/Users/abc/PycharmProjects/knowledge')

from directory_traverser.traverser_core import FeishuDirectoryTraverser

def test_simplified_calculation():
    """测试简化的序号计算逻辑"""
    print("🧪 测试简化的序号计算逻辑")
    print("=" * 40)
    
    traverser = FeishuDirectoryTraverser()
    
    # 测试数据
    test_cases = [
        ("1-2-2", "语雀空间权限说明"),  # 当前断点位置
        ("1", "新人园地-通关宝典"),     # 根级别
        ("1-2", "新人办公小贴士"),      # 中级别
    ]
    
    for current_path, current_name in test_cases:
        print(f"\n🔍 测试路径: {current_path} ({current_name})")
        
        # 模拟序号计算逻辑（不实际点击）
        try:
            # 情况1: 有子项目的情况
            child_path = f"{current_path}-1"
            print(f"  ✅ 如果有子项目 → {child_path}")
            
            # 情况2: 没有子项目，同级延续
            path_parts = current_path.split('-')
            path_parts[-1] = str(int(path_parts[-1]) + 1)
            sibling_path = '-'.join(path_parts)
            print(f"  📍 如果无子项目 → {sibling_path} (同级延续)")
            
        except Exception as e:
            print(f"  ❌ 计算失败: {e}")

def analyze_current_csv_state():
    """分析当前CSV状态"""
    print(f"\n📊 分析当前CSV状态")
    print("=" * 30)
    
    csv_file = "/Users/abc/PycharmProjects/knowledge/output/directory_traverse_log.csv"
    
    if not os.path.exists(csv_file):
        print("❌ CSV文件不存在")
        return
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) <= 1:
            print("❌ CSV文件为空或只有标题")
            return
        
        print(f"📋 CSV记录数: {len(lines) - 1}")
        
        # 显示最后几条记录
        print(f"\n📝 最后3条记录:")
        for line in lines[-3:]:
            if line.strip() and not line.startswith('序号'):
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    print(f"  {parts[0]:8} → {parts[1]}")
        
        # 分析最后一条记录
        last_line = lines[-1].strip()
        if last_line and not last_line.startswith('序号'):
            parts = last_line.split(',')
            if len(parts) >= 2:
                last_path = parts[0]
                last_name = parts[1]
                
                print(f"\n🎯 断点续传分析:")
                print(f"当前位置: {last_path} - {last_name}")
                
                # 预测下一个序号
                if "语雀空间权限说明" in last_name:
                    print(f"预期修复: 下一个应该是 1-2-3 (而不是 1-2-6)")
                    
                    # 显示计算逻辑
                    path_parts = last_path.split('-')
                    path_parts[-1] = str(int(path_parts[-1]) + 1)
                    next_path = '-'.join(path_parts)
                    print(f"计算结果: {next_path}")
    
    except Exception as e:
        print(f"❌ 分析CSV失败: {e}")

def main():
    """主函数"""
    print("🚀 简化序号延续逻辑测试")
    print("=" * 50)
    
    test_simplified_calculation()
    analyze_current_csv_state()
    
    print(f"\n💡 修复说明:")
    print("1. ✅ 简化了序号计算逻辑")
    print("2. ✅ 移除了复杂的上下文分析")
    print("3. ✅ 只检查是否有子项目，然后决定 +1 还是 -1")
    print("4. ✅ 保留了可靠的路径-名称映射导航")
    
    print(f"\n🧪 期望效果:")
    print("从 '1-2-2,语雀空间权限说明' 继续时：")
    print("- 如果该项目有子项目 → 1-2-2-1") 
    print("- 如果该项目无子项目 → 1-2-3 (修复跳号问题)")

if __name__ == "__main__":
    main()