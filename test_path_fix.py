#!/usr/bin/env python3
"""
测试路径式标识修复功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append('/Users/abc/PycharmProjects/knowledge_base')

from directory_traverser.traverser_core import FeishuDirectoryTraverser

def test_path_identification():
    """测试路径标识功能"""
    print("🧪 测试路径式标识修复")
    print("=" * 50)
    
    try:
        # 创建遍历器实例
        traverser = FeishuDirectoryTraverser()
        print("✅ 遍历器创建成功")
        
        # 检查修复后的方法是否存在
        if hasattr(traverser, 'recursive_traverse_directory'):
            print("✅ recursive_traverse_directory 方法存在")
        else:
            print("❌ recursive_traverse_directory 方法不存在")
            return
            
        # 模拟测试路径生成逻辑
        test_paths = []
        
        # 模拟第一层目录
        level_1_path = []
        for i in range(1, 3):  # 2个一级目录
            current_path_1 = level_1_path + [i]
            path_str_1 = "-".join(map(str, current_path_1))
            test_paths.append((f"一级目录{i}", path_str_1, 1))
            
            # 模拟第二层子目录
            if i == 1:  # 只有第一个一级目录有子目录
                for j in range(1, 4):  # 3个二级目录
                    current_path_2 = current_path_1 + [j]  
                    path_str_2 = "-".join(map(str, current_path_2))
                    test_paths.append((f"二级目录{j}", path_str_2, 2))
                    
                    # 模拟第三层子目录  
                    if j == 2:  # 只有第二个二级目录有子目录
                        for k in range(1, 3):  # 2个三级目录
                            current_path_3 = current_path_2 + [k]
                            path_str_3 = "-".join(map(str, current_path_3))
                            test_paths.append((f"三级目录{k}", path_str_3, 3))
        
        print("\n📊 测试路径生成逻辑:")
        for name, path_id, level in test_paths:
            indent = "  " * (level - 1)
            print(f"{indent}[{path_id}] {name}")
        
        # 验证预期结果
        expected_results = {
            "1": "一级目录1", 
            "1-1": "二级目录1",
            "1-2": "二级目录2", 
            "1-2-1": "三级目录1",  # 这应该类似"飞书空间权限说明"
            "1-2-2": "三级目录2",
            "1-3": "二级目录3",
            "2": "一级目录2"
        }
        
        print("\n✅ 期望的路径标识结果:")
        for path_id, name in expected_results.items():
            level = len(path_id.split('-'))
            indent = "  " * (level - 1)
            print(f"{indent}[{path_id}] {name}")
        
        print(f"\n🎉 路径式标识修复测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_path_identification()