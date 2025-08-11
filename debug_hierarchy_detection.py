#!/usr/bin/env python3
"""
层级识别调试脚本
分析为什么 "飞书空间权限说明" 没有被识别为 "新人办公小贴士" 的子项目
"""

def analyze_hierarchy_issue():
    """分析层级识别问题"""
    print("🔍 层级识别问题分析")
    print("=" * 40)
    
    print("📋 当前CSV结构:")
    print("1,新人园地-通关宝典")
    print("1-1,新人需知") 
    print("1-2,新人办公小贴士")
    print("1-3,飞书空间权限说明  ❌ (应该是 1-2-1)")
    print("1-4,语雀空间权限说明")
    
    print("\n🎯 期望结构:")
    print("1,新人园地-通关宝典")
    print("1-1,新人需知")
    print("1-2,新人办公小贴士")
    print("1-2-1,飞书空间权限说明  ✅ (正确的子项目)")
    print("1-3,语雀空间权限说明")
    
    print("\n🔍 可能的原因分析:")
    print("1. DOM检测问题:")
    print("   - 点击 '新人办公小贴士' 后，页面没有实际展开子项目")
    print("   - len(items_after_click) > len(current_items) 检测失败")
    print("   - 子项目可能已经展开，但没有被正确识别")
    
    print("\n2. 时机问题:")
    print("   - time.sleep(1) 可能不够，子项目还未完全加载")
    print("   - 需要更长的等待时间或更智能的等待机制")
    
    print("\n3. 选择器问题:")
    print("   - find_sidebar_items_fresh() 可能没有获取到新增的子项目")
    print("   - CSS选择器可能不准确")
    
    print("\n🛠️ 调试建议:")
    print("1. 增加详细日志输出:")
    print("   - 点击前的项目数量")
    print("   - 点击后的项目数量")
    print("   - 新增项目的具体名称")
    
    print("\n2. 增加等待时间:")
    print("   - 将 time.sleep(1) 改为 time.sleep(3)")
    print("   - 或使用WebDriverWait等待特定条件")
    
    print("\n3. 手动验证:")
    print("   - 在飞书页面手动点击 '新人办公小贴士'")
    print("   - 观察是否真的展开了子项目")
    print("   - 确认 '飞书空间权限说明' 是否在子树中")

def simulate_detection_logic():
    """模拟检测逻辑"""
    print("\n🧪 模拟检测逻辑")
    print("=" * 25)
    
    # 模拟当前检测逻辑
    print("假设当前页面有以下项目:")
    current_items = [
        "新人园地-通关宝典",
        "新人需知", 
        "新人办公小贴士",
        "语雀空间权限说明",
        "办公设备申请标准"
    ]
    
    print(f"点击前项目数量: {len(current_items)}")
    for i, item in enumerate(current_items, 1):
        print(f"  {i}. {item}")
    
    # 模拟点击 "新人办公小贴士" 后的情况
    print(f"\n点击 '新人办公小贴士' 后...")
    
    # 情况1: 没有展开子项目 (当前实际情况)
    print("情况1 - 没有展开子项目:")
    items_after_no_expand = current_items.copy()
    print(f"  项目数量: {len(items_after_no_expand)} (无变化)")
    print(f"  检测结果: len({len(items_after_no_expand)}) > len({len(current_items)}) = False")
    print("  结论: 被当作普通文档处理，记录为 1-2")
    
    # 情况2: 正确展开子项目 (期望情况)
    print("\n情况2 - 正确展开子项目:")
    items_after_expand = current_items + ["飞书空间权限说明"]
    print(f"  项目数量: {len(items_after_expand)} (增加了1个)")
    print(f"  检测结果: len({len(items_after_expand)}) > len({len(current_items)}) = True")
    print("  结论: 发现子项目，递归处理，'飞书空间权限说明' 记录为 1-2-1")
    
    print(f"\n🎯 关键问题: 为什么没有进入情况2？")
    print("需要在实际运行时添加详细日志来确定原因")

def main():
    """主函数"""
    analyze_hierarchy_issue()
    simulate_detection_logic()
    
    print(f"\n💡 下一步调试计划:")
    print("1. 在 extraction.py 中添加详细的调试日志")
    print("2. 记录点击前后的具体项目变化") 
    print("3. 确认DOM结构是否真的发生了变化")

if __name__ == "__main__":
    main()