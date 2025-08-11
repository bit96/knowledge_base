#!/bin/bash

# 飞书文档自动下载器启动脚本

echo "飞书文档自动下载器启动脚本 v2.0"
echo "====================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查依赖是否安装
echo "🔍 检查依赖..."
if ! python3 -c "import selenium, pandas, pynput" &> /dev/null; then
    echo "📦 安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装成功"
else
    echo "✅ 依赖检查通过"
fi

# 检查Chrome是否在调试模式运行
echo "🔍 检查Chrome调试端口..."
if curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo "✅ Chrome调试模式已启动"
else
    echo "⚠️  Chrome调试模式未启动"
    echo ""
    echo "建议启动Chrome调试模式："
    echo '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222'
    echo ""
    echo "或者确保Chrome已经登录飞书账号"
    echo ""
    read -p "按回车继续..."
fi

# 创建输出目录
mkdir -p .venv/output

echo ""
echo "🚀 启动飞书文档自动下载器 v2.0 (快捷键控制版)..."
echo "✨ 新功能: 双击空格键启动，ESC键停止，左上角状态显示"
echo ""

# 运行主程序
python3 feishu_downloader.py