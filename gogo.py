import os
import subprocess
import yaml
import requests

"""
脚本: 一键运行多个脚本+推送
作者: 3iXi
创建日期: 2024-10-30
更新日期：2025-05-28
需要依赖：pyyaml
描述: 需要在cfg.yaml配置好需要运行的脚本，cfg.yaml可在https://github.com/3ixi/autoscripts下载
      支持wxpusher和pushplus两种推送方式，可在配置文件中配置
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'cfg.yaml')

with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# 获取配置
scripts = config.get('scripts', [])
push_method = config.get('push_method', 'wxpusher')
wxpusher_config = config.get('wxpusher', {})
pushplus_config = config.get('pushplus', {})

def execute_script(script_name):
    try:
        # 使用subprocess执行脚本并捕获输出信息
        result = subprocess.run(['python', script_name], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"执行脚本时出错: {e}"

# 推送信息到wxpusher
def send_wxpusher_message(title, message):
    apptoken = wxpusher_config.get('apptoken')
    uids = wxpusher_config.get('uids', [])
    topic_id = wxpusher_config.get('topic_id')
    
    payload = {
        'appToken': apptoken,
        'uids': uids,
        'content': f"{title}\n\n{message}",
        'topicId': topic_id
    }
    
    response = requests.post('https://wxpusher.zjiecode.com/api/send/message', json=payload)
    return response.json()

# 推送信息到pushplus
def send_pushplus_message(title, message):
    token = pushplus_config.get('token')
    template = pushplus_config.get('template', 'html')
    channel = pushplus_config.get('channel', 'wechat')
    
    payload = {
        'token': token,
        'title': title,
        'content': message,
        'template': template,
        'channel': channel
    }
    
    response = requests.post('http://www.pushplus.plus/send', json=payload)
    return response.json()

# 根据配置选择推送方式
def send_message(title, message):
    if push_method == 'wxpusher':
        return send_wxpusher_message(title, message)
    elif push_method == 'pushplus':
        return send_pushplus_message(title, message)
    else:
        print(f"未知的推送方式: {push_method}")
        return None

all_outputs = []

for script in scripts:
    script_name = script['path']
    absolute_script_path = os.path.join(current_dir, script_name)

    print(f"正在执行: {script['name']} ({script_name})")
    output = execute_script(absolute_script_path)

    all_outputs.append(f"{script['name']} 执行结果:\n{output}\n")
    print(output)
    print("\n" + "-" * 50 + "\n")

final_message = "\n".join(all_outputs)
send_message("所有脚本执行结果", final_message)
print(f"所有脚本执行完毕，已发送结果到 {push_method}。")
