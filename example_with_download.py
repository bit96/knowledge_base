#!/usr/bin/env python3
"""
带下载功能的遍历器使用示例
演示如何启用自动下载功能
"""

import sys
import os
sys.path.insert(0, '/Users/abc/PycharmProjects/knowledge')

from directory_traverser.traverser_core import FeishuDirectoryTraverser

def example_without_download():
    """示例1: 传统用法（不下载）"""
    print("📝 示例1: 传统用法（仅遍历，不下载）")
    print("=" * 50)
    print()
    
    # 现有用户的代码完全不用改变
    traverser = FeishuDirectoryTraverser()
    
    print("代码示例:")
    print("```python")
    print("traverser = FeishuDirectoryTraverser()")
    print("# traverser.traverse_all_items()  # 与之前完全相同")
    print("```")
    print()
    print(f"下载功能状态: {'启用' if traverser.is_download_enabled() else '未启用'}")
    print("行为: 与之前版本完全一致，只遍历不下载")
    print()

def example_with_download():
    """示例2: 启用下载功能"""
    print("📝 示例2: 启用自动下载功能")
    print("=" * 50)
    print()
    
    # 新用法：启用下载功能
    traverser = FeishuDirectoryTraverser(enable_download=True)
    
    print("代码示例:")
    print("```python")
    print("traverser = FeishuDirectoryTraverser(enable_download=True)")
    print("# traverser.traverse_all_items()  # 会在每次访问文档后尝试下载")
    print("```")
    print()
    print(f"下载功能状态: {'启用' if traverser.is_download_enabled() else '未启用'}")
    print("行为: 遍历时会自动下载每个成功访问的文档")
    print()
    
    # 显示下载统计
    stats = traverser.get_download_stats_summary()
    print("初始统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

def example_custom_output():
    """示例3: 自定义输出目录+下载"""
    print("📝 示例3: 自定义输出目录 + 下载功能")
    print("=" * 50)
    print()
    
    custom_output = "/Users/abc/Downloads/feishu_knowledge"
    traverser = FeishuDirectoryTraverser(
        output_dir=custom_output,
        enable_download=True
    )
    
    print("代码示例:")
    print("```python")
    print("traverser = FeishuDirectoryTraverser(")
    print(f"    output_dir='{custom_output}',")
    print("    enable_download=True")
    print(")")
    print("```")
    print()
    print(f"输出目录: {traverser.output_dir}")
    print(f"下载功能: {'启用' if traverser.is_download_enabled() else '未启用'}")
    print("行为: CSV和日志保存到自定义目录，文档也下载到该目录")
    print()

def show_integration_details():
    """显示集成的技术细节"""
    print("🔧 集成技术细节")
    print("=" * 50)
    print()
    
    print("集成方式:")
    print("1. 创建了 DownloadMixin 混入类")
    print("2. 扩展了 FeishuDirectoryTraverser 核心类")
    print("3. 在成功访问文档后自动调用下载")
    print()
    
    print("安全设计:")
    print("✅ 默认关闭，向后兼容")
    print("✅ 下载失败不影响遍历继续")  
    print("✅ 独立的错误处理和日志")
    print("✅ 完整的统计和报告")
    print()
    
    print("使用的下载引擎:")
    print("📥 test_word_click_fix_fast6.py")
    print("   - 智能识别Word/Excel文档")
    print("   - 自动重试机制（最多3次）")
    print("   - 精确菜单定位和点击")
    print("   - 支持多种文档格式")
    print()

def main():
    """主函数"""
    print("🚀 飞书知识库遍历器 - 下载功能使用示例")
    print("=" * 60)
    print("基于 test_word_click_fix_fast6.py 的智能下载集成")
    print()
    
    # 运行所有示例
    example_without_download()
    example_with_download()
    example_custom_output()
    show_integration_details()
    
    print("💡 使用建议:")
    print("1. 首次使用建议先测试小范围目录")
    print("2. 确保有足够的磁盘空间存储下载文件")
    print("3. 下载会显著增加总遍历时间")
    print("4. 可以随时查看下载统计和日志")
    print()
    
    print("🎯 完整使用流程:")
    print("```python")
    print("from directory_traverser.traverser_core import FeishuDirectoryTraverser")
    print("")
    print("# 启用下载功能")
    print("traverser = FeishuDirectoryTraverser(enable_download=True)")
    print("")
    print("# 连接Chrome并开始遍历")
    print("traverser.connect_chrome()")
    print("traverser.traverse_all_items()")
    print("")
    print("# 查看最终统计（包含下载统计）")
    print("traverser.print_final_summary()")
    print("```")

if __name__ == "__main__":
    main()