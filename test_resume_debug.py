#!/usr/bin/env python3
"""
断点续传调试脚本
直接测试断点续传逻辑，不需要用户交互
"""

import sys
import os
sys.path.insert(0, '/Users/abc/PycharmProjects/knowledge')

from directory_traverser.traverser_core import FeishuDirectoryTraverser

def test_resume_logic():
    """测试断点续传逻辑"""
    print("🧪 测试断点续传和层级识别逻辑")
    print("=" * 50)
    
    # 创建遍历器实例
    traverser = FeishuDirectoryTraverser()
    
    # 检查是否有断点续传信息
    resume_info = traverser.check_resume_progress()
    
    if resume_info:
        path, name = resume_info
        print(f"✅ 检测到断点续传信息: {path} - {name}")
        
        # 模拟Chrome连接（不实际连接）
        print("🔧 模拟Chrome连接...")
        
        # 测试导航到断点位置的逻辑
        print(f"🎯 测试导航到断点位置: {path} - {name}")
        
        # 解析路径
        try:
            path_parts = [int(x) for x in path.split('-')]
            print(f"📍 解析路径: {path_parts}")
            
            # 计算下一个要处理的位置
            next_path_parts, next_index = traverser.calculate_next_position(path, name)
            next_path_str = '-'.join(map(str, next_path_parts))
            
            print(f"▶️ 计算的下一个处理位置: {next_path_str}")
            print(f"🔍 这意味着程序会从 {next_path_str} 开始继续遍历")
            
            # 显示已访问项目
            visited_texts = set()
            traverser.populate_visited_texts_from_csv(visited_texts)
            print(f"📋 已访问项目数量: {len(visited_texts)}")
            print("已访问项目列表:")
            for i, item in enumerate(sorted(visited_texts), 1):
                print(f"  {i:2d}. {item}")
                
        except Exception as e:
            print(f"❌ 解析路径失败: {e}")
    else:
        print("❌ 未检测到断点续传信息")
        print("这意味着将从头开始遍历")

def analyze_csv_structure():
    """分析当前CSV结构"""
    print("\n🔍 分析当前CSV结构")
    print("=" * 30)
    
    traverser = FeishuDirectoryTraverser()
    csv_file = os.path.join(traverser.output_dir, "directory_traverse_log.csv")
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"📄 CSV文件行数: {len(lines)}")
        print("📋 内容预览:")
        for i, line in enumerate(lines):
            print(f"  {i+1:2d}: {line.strip()}")
    else:
        print("❌ CSV文件不存在")

def main():
    """主函数"""
    test_resume_logic()
    analyze_csv_structure()
    
    print("\n💡 断点续传调试完成")
    print("如需实际测试，需要:")
    print("1. 确保Chrome调试模式运行")
    print("2. 导航到正确的飞书页面") 
    print("3. 运行完整的遍历程序")

if __name__ == "__main__":
    main()