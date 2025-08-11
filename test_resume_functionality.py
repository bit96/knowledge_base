#!/usr/bin/env python3
"""
断点续传功能测试脚本
演示如何在作业失败后继续执行
"""

from directory_traverser.traverser_core import FeishuDirectoryTraverser
import os

def test_resume_functionality():
    """测试断点续传功能"""
    print("🧪 断点续传功能测试")
    print("=" * 50)
    
    # 创建遍历器实例
    traverser = FeishuDirectoryTraverser()
    
    print(f"📂 输出目录: {traverser.output_dir}")
    
    # 检查是否有断点续传信息
    resume_info = traverser.check_resume_progress()
    
    if resume_info:
        path, name = resume_info
        print(f"✅ 检测到上次中断位置: {path} - {name}")
        print(f"🔄 下次运行时将从此位置继续")
        
        # 展示CSV文件内容
        csv_file = os.path.join(traverser.output_dir, "directory_traverse_log.csv")
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_items = len(lines) - 1  # 减去标题行
                
            print(f"📊 已处理项目数量: {total_items}")
            print("\n📋 已处理的最后5个项目:")
            
            if len(lines) > 1:
                # 显示最后5行（或所有行如果不足5行）
                start_idx = max(1, len(lines) - 5)  # 避免显示标题行
                for i in range(start_idx, len(lines)):
                    line = lines[i].strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            print(f"   • {parts[0]} - {parts[1]}")
    else:
        print("ℹ️ 未检测到断点续传信息")
        print("📝 这意味着:")
        print("   • 没有CSV文件，或")
        print("   • CSV文件为空，或")
        print("   • 这是第一次运行")
    
    print("\n🎯 使用说明:")
    print("1. 正常运行: python3 run_traverser_modular.py")
    print("2. 如果程序失败/中断，重新运行相同命令")
    print("3. 程序会自动检测上次中断位置并询问是否继续")
    print("4. 选择 'y' 继续，选择 'n' 重新开始")
    
    print("\n✨ 断点续传功能已集成，随时可以使用！")

if __name__ == "__main__":
    test_resume_functionality()