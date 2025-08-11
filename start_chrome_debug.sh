#!/bin/bash

# Chrome调试模式启动脚本
# 用于飞书文档自动下载器

echo "🚀 Chrome调试模式启动脚本"
echo "=========================="

# 配置参数
DEBUG_PORT=9222
DATA_DIR="/tmp/chrome_debug"
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 检查Chrome是否已安装
if [ ! -f "$CHROME_PATH" ]; then
    echo "❌ 未找到Google Chrome，请确保已安装Chrome浏览器"
    echo "   Chrome路径: $CHROME_PATH"
    exit 1
fi

# 检查是否已有调试模式Chrome在运行
echo "🔍 检查现有Chrome调试进程..."
if curl -s --connect-timeout 3 --noproxy "*" http://127.0.0.1:$DEBUG_PORT/json/version > /dev/null 2>&1; then
    echo "✅ Chrome调试模式已在运行 (端口$DEBUG_PORT)"
    echo "📊 当前Chrome版本信息:"
    curl -s --noproxy "*" http://127.0.0.1:$DEBUG_PORT/json/version | python3 -m json.tool 2>/dev/null || echo "无法获取版本信息"
    echo ""
    echo "💡 如需重启Chrome调试模式，请先运行: killall 'Google Chrome'"
    exit 0
fi

# 检查端口是否被其他程序占用
echo "🔍 检查端口$DEBUG_PORT状态..."
if lsof -i :$DEBUG_PORT > /dev/null 2>&1; then
    echo "⚠️  端口$DEBUG_PORT已被占用，正在尝试释放..."
    # 尝试杀死占用端口的进程
    lsof -ti :$DEBUG_PORT | xargs kill -9 2>/dev/null
    sleep 2
fi

# 关闭现有的Chrome进程
echo "🔄 关闭现有Chrome进程..."
if pgrep -f "Google Chrome" > /dev/null; then
    echo "   发现运行中的Chrome进程，正在关闭..."
    killall "Google Chrome" 2>/dev/null
    sleep 3
    
    # 检查是否成功关闭
    if pgrep -f "Google Chrome" > /dev/null; then
        echo "⚠️  部分Chrome进程可能仍在运行，强制终止..."
        pkill -f "Google Chrome" 2>/dev/null
        sleep 2
    fi
fi

# 创建调试数据目录
echo "📁 准备调试数据目录..."
mkdir -p "$DATA_DIR"
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ 无法创建数据目录: $DATA_DIR"
    exit 1
fi

echo "✅ 数据目录已准备: $DATA_DIR"

# 启动Chrome调试模式
echo "🚀 启动Chrome调试模式..."
echo "   端口: $DEBUG_PORT"
echo "   数据目录: $DATA_DIR"

# 使用nohup确保后台运行
nohup "$CHROME_PATH" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$DATA_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-default-apps \
    > /dev/null 2>&1 &

# 获取Chrome进程ID
CHROME_PID=$!

# 等待Chrome启动
echo "⏳ 等待Chrome启动..."
sleep 5

# 验证Chrome是否成功启动
echo "🔍 验证Chrome调试模式..."
RETRY_COUNT=0
MAX_RETRIES=10

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s --noproxy "*" http://127.0.0.1:$DEBUG_PORT/json/version > /dev/null 2>&1; then
        echo "✅ Chrome调试模式启动成功!"
        echo ""
        echo "📊 Chrome信息:"
        curl -s --noproxy "*" http://127.0.0.1:$DEBUG_PORT/json/version | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   浏览器: {data.get(\"Browser\", \"未知\")}')
    print(f'   WebKit版本: {data.get(\"WebKit-Version\", \"未知\")[:20]}...')
    print(f'   调试端口: $DEBUG_PORT')
except:
    print('   无法解析版本信息')
" 2>/dev/null

        echo ""
        echo "🎯 使用说明:"
        echo "   1. 在新打开的Chrome窗口中登录飞书账号"
        echo "   2. 导航到需要下载的文档页面"  
        echo "   3. 运行下载脚本: python3 test_word_click_fix_fast3.py"
        echo ""
        echo "📝 其他命令:"
        echo "   检查状态: curl -s --noproxy \"*\" http://127.0.0.1:$DEBUG_PORT/json/version"
        echo "   关闭调试: killall 'Google Chrome'"
        echo "   查看标签: curl -s --noproxy \"*\" http://127.0.0.1:$DEBUG_PORT/json"
        echo ""
        echo "🔧 Chrome进程ID: $CHROME_PID"
        
        # 检查Chrome窗口是否打开
        sleep 2
        if ! ps -p $CHROME_PID > /dev/null 2>&1; then
            echo "⚠️  Chrome进程可能已退出，请检查错误信息"
        fi
        
        exit 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   尝试 $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

# 启动失败
echo "❌ Chrome调试模式启动失败"
echo ""
echo "🔍 故障排除:"
echo "   1. 检查Chrome是否正确安装在: $CHROME_PATH"
echo "   2. 检查端口$DEBUG_PORT是否被占用: lsof -i :$DEBUG_PORT"
echo "   3. 检查数据目录权限: ls -la $DATA_DIR"
echo "   4. 手动尝试启动: '$CHROME_PATH --remote-debugging-port=$DEBUG_PORT --user-data-dir=$DATA_DIR'"
echo ""
echo "📋 系统信息:"
echo "   当前用户: $(whoami)"
echo "   当前目录: $(pwd)"
echo "   系统版本: $(sw_vers -productVersion 2>/dev/null || echo '未知')"

exit 1