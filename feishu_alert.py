#!/usr/bin/env python3
"""
飞书群告警通知脚本
专用于发送文档下载失败的告警信息

功能:
- 发送文档下载失败告警
- 包含时间戳和系统信息
- 错误处理和重试机制
"""
import requests
import json
import time
import socket
import platform
from datetime import datetime

class FeishuAlert:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.max_retries = 3
        self.retry_delay = 2
    
    def get_system_info(self):
        """获取系统信息"""
        try:
            hostname = socket.gethostname()
            system = platform.system()
            return f"{hostname} ({system})"
        except:
            return "未知系统"
    
    def send_download_failure_alert(self, doc_title=None, error_msg=None, attempt_count=None, execution_time=None):
        """发送文档下载失败告警"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_info = self.get_system_info()
        
        # 构建告警消息
        alert_title = "🚨 飞书文档下载失败告警"
        
        content_parts = [
            f"**⏰ 时间**: {current_time}",
            f"**💻 系统**: {system_info}",
        ]
        
        if doc_title:
            content_parts.append(f"**📄 文档**: {doc_title}")
        
        if attempt_count:
            content_parts.append(f"**🔄 尝试次数**: {attempt_count} 次")
        
        if execution_time:
            content_parts.append(f"**⏱️ 执行时间**: {execution_time:.1f} 秒")
        
        if error_msg:
            content_parts.append(f"**❌ 错误信息**: {error_msg}")
        
        content_parts.extend([
            "",
            "**💡 建议检查**:",
            "• Chrome调试模式状态 (端口9222)",
            "• 飞书文档页面是否正常加载",
            "• 网络连接状态",
            "• 文档下载权限"
        ])
        
        message_content = "\n".join(content_parts)
        
        # 构建消息体
        message_data = {
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": alert_title,
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "div",
                        "text": {
                            "content": message_content,
                            "tag": "lark_md"
                        }
                    }
                ],
                "header": {
                    "title": {
                        "content": "文档下载系统告警",
                        "tag": "plain_text"
                    },
                    "template": "red"
                }
            }
        }
        
        return self._send_message(message_data)
    
    
    def _send_message(self, message_data):
        """发送消息到飞书群，带重试机制"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    print(f"第 {attempt} 次重试发送消息...")
                    time.sleep(self.retry_delay)
                
                response = requests.post(
                    self.webhook_url,
                    headers=headers,
                    data=json.dumps(message_data),
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('StatusCode') == 0:
                        print("✅ 飞书告警发送成功")
                        return True
                    else:
                        print(f"❌ 飞书API返回错误: {result.get('msg', '未知错误')}")
                        if attempt < self.max_retries:
                            continue
                        return False
                else:
                    print(f"❌ HTTP错误 {response.status_code}: {response.text}")
                    if attempt < self.max_retries:
                        continue
                    return False
                    
            except requests.exceptions.Timeout:
                print(f"⏰ 请求超时 (尝试 {attempt + 1}/{self.max_retries + 1})")
                if attempt < self.max_retries:
                    continue
                return False
            except requests.exceptions.ConnectionError:
                print(f"🌐 网络连接错误 (尝试 {attempt + 1}/{self.max_retries + 1})")
                if attempt < self.max_retries:
                    continue
                return False
            except Exception as e:
                print(f"❌ 发送消息异常: {e}")
                if attempt < self.max_retries:
                    continue
                return False
        
        print("❌ 所有发送尝试都失败了")
        return False

def main():
    """发送文档下载失败告警"""
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/e4af21da-21b9-466f-9e98-a52357f17739"
    
    print("🚨 发送飞书文档下载失败告警")
    print("=" * 50)
    
    # 创建告警实例
    alert = FeishuAlert(webhook_url)
    
    # 发送下载失败告警
    success = alert.send_download_failure_alert(
        doc_title="飞书文档下载失败",
        error_msg="文档下载过程中遇到问题",
        attempt_count=4,
        execution_time=30.0
    )
    
    if success:
        print("✅ 告警消息发送成功，请检查飞书群")
    else:
        print("❌ 告警消息发送失败")

if __name__ == "__main__":
    main()