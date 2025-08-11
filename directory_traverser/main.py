#!/usr/bin/env python3
"""
飞书知识库目录遍历器入口文件
模块化版本，基于原版directory_traverser.py重构
"""

import time
import traceback
from .traverser_core import FeishuDirectoryTraverser


def main():
    print("🚀 飞书知识库目录遍历器 v2.0 (模块化版本)")
    print("基于 test_word_click_fix_fast3.py 架构开发")
    print("="*60)
    
    print("✨ 主要特性:")
    print("  🕒 严格的访问频率控制 (2-5秒延迟)")
    print("  🛡️ 自动权限检查和尊重机制")
    print("  🔍 智能左侧目录识别")
    print("  📊 详细的统计和日志记录")
    print("  💾 多格式数据输出 (CSV/JSON/TXT)")
    print("  🌲 多层级递归遍历，支持折叠目录")
    print("  🔄 智能断点续传，失败后可继续执行")
    print()
    
    print("📋 使用前请确保:")
    print("1. ✅ Chrome调试模式运行中 (端口9222)")
    print("2. ✅ 已登录飞书账号")
    print("3. ✅ 当前页面是【知识库的文件列表页面】，而不是单个文档页面")
    print("4. ✅ 左侧有完整的目录树结构，包含多个文档链接")
    print("5. ✅ 网络连接稳定")
    print()
    
    print("🎯 正确的页面特征:")
    print("  • 页面显示多个文档/文件的列表")
    print("  • 左侧有目录树，包含文件夹和文档")
    print("  • URL通常是知识库主页，不包含'?'参数")
    print("  • 页面中有几十个或更多的文档链接")
    print()
    
    print("⚠️ 重要提醒:")
    print("  • 程序将严格遵循2-5秒访问间隔")
    print("  • 自动跳过无权限访问的页面")
    print("  • 过程中可随时按 Ctrl+C 安全中断")
    print("  • 结果将保存到指定的output目录")
    print("  • 如果中途失败，重新运行可自动继续上次进度")
    print()
    
    print("⚠️ 最后确认: 请确认您当前在【知识库目录页面】，而不是单个文档页面")
    
    try:
        response = input("🚀 确认页面正确后，按回车键开始遍历 (输入 'q' 退出): ").strip()
        if response.lower() == 'q':
            print("👋 程序退出")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n👋 程序退出")
        return
    
    print("\n" + "="*60)
    print("🚀 开始遍历...")
    print("="*60)
    
    # 记录总开始时间
    total_start_time = time.time()
    
    # 创建遍历器实例
    traverser = FeishuDirectoryTraverser()
    
    try:
        # 设置Chrome连接
        print("🔧 正在连接Chrome...")
        if not traverser.setup_driver():
            print("❌ Chrome连接失败")
            print("\n💡 解决建议:")
            print("1. 确保Chrome以调试模式启动:")
            print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
            print("2. 检查端口9222是否被占用")
            print("3. 重启Chrome浏览器")
            return
        
        # 开始遍历
        print("🎯 开始目录遍历...")
        traverser.traverse_all_items()
        
        # 计算总耗时
        total_duration = time.time() - total_start_time
        
        # 最终结果展示
        print("\n" + "🎉"*20)
        print("遍历任务完成！")
        print("🎉"*20)
        
        print(f"\n📊 最终统计:")
        print(f"   ✅ 成功访问: {traverser.stats['successful_access']} 个页面")
        print(f"   ⚠️ 权限限制: {traverser.stats['permission_denied']} 个页面")
        print(f"   ❌ 访问失败: {traverser.stats['access_failed']} 个页面")
        print(f"   ⏱️ 总耗时: {traverser.format_duration(total_duration)}")
        
        if traverser.stats['successful_access'] > 0:
            success_rate = (traverser.stats['successful_access'] / traverser.stats['total_items_found']) * 100
            print(f"   📈 成功率: {success_rate:.1f}%")
        
        print(f"\n📁 结果文件位置:")
        print(f"   📂 {traverser.output_dir}")
        print(f"   📄 主要数据: directory_traverse_log.csv")
        print(f"   📊 统计摘要: traverse_summary.json")
        
        print(f"\n💡 提示:")
        print(f"   • 可以使用Excel或其他工具打开CSV文件查看结果")
        print(f"   • JSON文件包含完整的统计信息")
        print(f"   • 日志文件记录了详细的执行过程")
        
    except KeyboardInterrupt:
        print("\n⏸️ 用户中断遍历")
        print("📊 部分结果已保存")
        if traverser.stats.get('successful_access', 0) > 0:
            print(f"✅ 已成功记录 {traverser.stats['successful_access']} 个页面")
            print(f"📁 结果保存在: {traverser.output_dir}")
        
    except Exception as e:
        print(f"\n❌ 遍历过程中出错: {e}")
        print("\n🔍 错误详情:")
        traceback.print_exc()
        
        print(f"\n💡 可能的解决方案:")
        print("1. 检查Chrome连接状态")
        print("2. 确认页面是否正确加载")
        print("3. 检查网络连接")
        print("4. 查看详细日志文件获取更多信息")
    
    finally:
        print(f"\n📝 详细日志保存在: {traverser.output_dir}/traverser.log")


if __name__ == "__main__":
    main()