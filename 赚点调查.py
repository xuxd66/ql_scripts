#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赚点调查微信小程序签到脚本 - 青龙面板多账号版本

环境变量配置:
- ZDDC_TOKEN: 必需，支持多账号，格式：token1&token2&token3
- PUSPLUS_TOKEN: 可选，PushPlus推送服务的token，用于发送通知

抓包说明:
1. 使用抓包工具（如Charles、Fiddler等）抓取微信小程序的网络请求
2. 从请求头中获取z-token值（格式：Bearer xxxxx）
3. 将Bearer后面的token值设置为ZDDC_TOKEN环境变量
4. 多账号用&符号分隔，例如：token1&token2&token3

青龙面板使用方法:
1. 在青龙面板的环境变量中添加 ZDDC_TOKEN（支持多账号，用&分隔）
2. 可选添加 PUSPLUS_TOKEN 用于推送通知
3. 将此脚本上传到青龙面板并设置定时任务

作者: AI
自己写脚本ai链接：https://manus.im/invitation/ULHSLZ0GJALBO
版本: 1.2.0 (青龙面板多账号版本)
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime

# 青龙面板兼容性处理
def ensure_requests():
    """确保requests库可用"""
    try:
        import requests
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
            return True
        except:
            return False

# 确保requests库可用
if not ensure_requests():
    print("❌ 无法安装requests库，脚本无法运行")
    sys.exit(1)

class ZDDCCheckinMulti:
    def __init__(self):
        self.tokens = self.parse_tokens()
        self.pusplus_token = os.getenv('PUSPLUS_TOKEN')
        
        if not self.tokens:
            print("❌ 错误：未设置ZDDC_TOKEN环境变量或格式错误")
            print("请从抓包数据中获取z-token值并设置为环境变量")
            print("多账号格式：token1&token2&token3")
            sys.exit(1)
        
        self.base_url = "https://api.jisiba.com"
        print(f"📊 检测到 {len(self.tokens)} 个账号")
    
    def parse_tokens(self):
        """解析多账号Token"""
        token_str = os.getenv('ZDDC_TOKEN', '')
        if not token_str:
            return []
        
        # 支持多种分隔符：& @ | \n
        separators = ['&', '@', '|', '\n']
        tokens = [token_str]
        
        for sep in separators:
            new_tokens = []
            for token in tokens:
                new_tokens.extend(token.split(sep))
            tokens = new_tokens
        
        # 清理空白字符并过滤空值
        tokens = [token.strip() for token in tokens if token.strip()]
        return tokens
    
    def create_headers(self, token):
        """为指定token创建请求头"""
        return {
            'Host': 'api.jisiba.com',
            'Connection': 'keep-alive',
            'z-token': f'Bearer {token}',
            'z-client': '4',
            'z-version': '1.0.0',
            'content-type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.56(0x1800383b) NetType/4G Language/zh_CN',
            'Referer': 'https://servicewechat.com/wxff84ded73727360f/63/page-frame.html'
        }
    
    def safe_request(self, method, url, headers, **kwargs):
        """安全的HTTP请求，自动处理响应解码"""
        try:
            # 移除Accept-Encoding头，让requests自动处理压缩
            headers = headers.copy()
            if 'Accept-Encoding' in headers:
                del headers['Accept-Encoding']
            
            response = requests.request(method, url, headers=headers, timeout=15, **kwargs)
            
            if response.status_code == 200:
                try:
                    # 使用response.json()自动处理解码和JSON解析
                    data = response.json()
                    return True, data
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始文本
                    return True, response.text
            else:
                return False, f"HTTP状态码: {response.status_code}, 响应: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, f"网络请求失败: {str(e)}"
    
    def check_signin_status(self, token, account_index):
        """检查签到状态"""
        url = f"{self.base_url}/v1/users/checkin"
        headers = self.create_headers(token)
        return self.safe_request('GET', url, headers)
    
    def do_checkin(self, token, account_index):
        """执行签到"""
        url = f"{self.base_url}/v1/users/checkin"
        headers = self.create_headers(token)
        return self.safe_request('POST', url, headers)
    
    def send_notification(self, title, content, is_success=True):
        """发送PushPlus通知"""
        if not self.pusplus_token:
            return False
        
        try:
            url = "http://www.pushplus.plus/send"
            
            # 根据成功/失败状态设置不同的模板内容
            if is_success:
                html_content = f"""
                <div style="padding: 20px; font-family: Arial, sans-serif;">
                    <h2 style="color: #28a745;">✅ {title}</h2>
                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 10px 0;">
                        {content}
                    </div>
                    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                        📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        🤖 赚点调查签到脚本 v1.2.0 (青龙面板多账号版本)
                    </p>
                </div>
                """
            else:
                html_content = f"""
                <div style="padding: 20px; font-family: Arial, sans-serif;">
                    <h2 style="color: #dc3545;">❌ {title}</h2>
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 10px 0;">
                        {content}
                    </div>
                    <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                        📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        🤖 赚点调查签到脚本 v1.2.0 (青龙面板多账号版本)
                    </p>
                </div>
                """
            
            data = {
                "token": self.pusplus_token,
                "title": title,
                "content": html_content,
                "template": "html"
            }
            
            response = requests.post(url, json=data, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    return True
                else:
                    return False
            else:
                return False
                
        except Exception as e:
            return False
    
    def process_single_account(self, token, account_index):
        """处理单个账号的签到"""
        account_name = f"账号{account_index + 1}"
        token_display = f"{token[:10]}...{token[-6:]}" if len(token) > 16 else token
        
        print(f"\n{'='*20} {account_name} {'='*20}")
        print(f"🔑 Token: {token_display}")
        
        # 检查签到状态
        print("🔍 检查签到状态...")
        success, result = self.check_signin_status(token, account_index)
        
        if not success:
            error_msg = f"❌ {account_name} 检查签到状态失败: {result}"
            print(error_msg)
            return False, error_msg
        
        print("✅ 签到状态检查成功")
        
        # 执行签到
        print("📝 开始执行签到...")
        success, result = self.do_checkin(token, account_index)
        
        if not success:
            error_msg = f"❌ {account_name} 签到失败: {result}"
            print(error_msg)
            return False, error_msg
        
        # 解析签到结果
        if isinstance(result, dict):
            # 检查各种可能的成功标识
            success_indicators = [
                result.get('success') == True,
                result.get('code') == 200,
                result.get('status') == 'success',
                'success' in str(result).lower()
            ]
            
            if any(success_indicators):
                success_msg = f"✅ {account_name} 签到成功！"
                
                # 尝试提取积分信息
                data = result.get('data', {})
                if isinstance(data, dict):
                    points = data.get('points', data.get('reward', '未知'))
                    total_points = data.get('total_points', data.get('total', '未知'))
                    if points != '未知' or total_points != '未知':
                        success_msg += f"\n💰 本次获得积分: {points}\n💎 总积分: {total_points}"
                
                print(success_msg)
                return True, success_msg
            else:
                error_msg = f"❌ {account_name} 签到失败: {result.get('message', result.get('msg', '未知错误'))}"
                print(error_msg)
                return False, error_msg
        else:
            # 如果返回的不是字典，检查是否包含成功关键词
            result_str = str(result).lower()
            if any(keyword in result_str for keyword in ['success', '成功', 'ok']):
                success_msg = f"✅ {account_name} 签到成功！"
                print(success_msg)
                return True, success_msg
            else:
                error_msg = f"❌ {account_name} 签到失败，未知响应格式: {result}"
                print(error_msg)
                return False, error_msg
    
    def run(self):
        """运行多账号签到流程"""
        print("🚀 赚点调查签到脚本启动 (青龙面板多账号版本)")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 共检测到 {len(self.tokens)} 个账号")
        print("-" * 60)
        
        success_accounts = []
        failed_accounts = []
        
        # 逐个处理每个账号
        for i, token in enumerate(self.tokens):
            try:
                # 添加账号间的延迟，避免请求过于频繁
                if i > 0:
                    print(f"\n⏳ 等待 3 秒后处理下一个账号...")
                    time.sleep(3)
                
                success, message = self.process_single_account(token, i)
                
                if success:
                    success_accounts.append(f"账号{i + 1}")
                else:
                    failed_accounts.append(f"账号{i + 1}: {message}")
                    
            except Exception as e:
                error_msg = f"账号{i + 1} 处理异常: {str(e)}"
                print(f"❌ {error_msg}")
                failed_accounts.append(error_msg)
        
        # 汇总结果
        print("\n" + "="*60)
        print("📊 签到结果汇总")
        print("="*60)
        
        if success_accounts:
            print(f"✅ 成功账号 ({len(success_accounts)}个): {', '.join(success_accounts)}")
        
        if failed_accounts:
            print(f"❌ 失败账号 ({len(failed_accounts)}个):")
            for failed in failed_accounts:
                print(f"   - {failed}")
        
        # 发送汇总通知
        if self.pusplus_token:
            total_accounts = len(self.tokens)
            success_count = len(success_accounts)
            failed_count = len(failed_accounts)
            
            if failed_count == 0:
                # 全部成功
                title = "赚点调查签到全部成功"
                content = f"🎉 所有账号签到成功！<br>✅ 成功: {success_count}/{total_accounts}<br>📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.send_notification(title, content, is_success=True)
                print("📱 汇总通知发送成功")
            else:
                # 部分失败或全部失败
                title = "赚点调查签到结果汇总"
                content = f"📊 签到完成<br>✅ 成功: {success_count}/{total_accounts}<br>❌ 失败: {failed_count}/{total_accounts}<br>📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.send_notification(title, content, is_success=(success_count > 0))
                print("📱 汇总通知发送成功")
        else:
            print("📢 未配置PushPlus通知，跳过推送")
        
        print("-" * 60)
        
        # 返回整体结果
        return len(failed_accounts) == 0


def main():
    """主函数"""
    try:
        checkin = ZDDCCheckinMulti()
        success = checkin.run()
        
        if success:
            print("🎉 所有账号签到流程完成")
        else:
            print("💔 部分账号签到失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(0)
    except Exception as e:
        error_msg = f"💥 程序异常: {str(e)}"
        print(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()

