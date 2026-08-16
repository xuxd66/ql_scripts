import requests
import json
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad,unpad
import base64
import time
import os



#福田e家的请求头
headers = {"User-Agent": "okhttp/3.14.9"}
#皮卡生活签到
hea = {
    "content-type": "application/json; charset=utf-8",
    "accept-encoding": "gzip",
    "channel": "1",
    "host": "czyl.foton.com.cn"
}


def encrypt_data(uid, memberId, userType):   
    # 固定密钥和IV
    key = b'fontone-trans@lx100$#365'
    iv = b'20161201'
    
    # 构建动态JSON
    data = {
        "limit": {
            "applicationType": "va_ftej",
            "auth": "",
            "brand": "OnePlus",
            "businessId": "",
            "businessMemberId": "",
            "from": "3",
            "mode": "PKG110",
            "roleId": "3",
            "timestamp": "",
            "uid": uid,
            "userType": userType,
            "version": "0"
        },
        "param": {
            "uid": uid,
            "protocolId": "83",
            "version": "7.2.4",
            "memberId": memberId
        }
    }
    
    # 转换为JSON字符串
    json_str = json.dumps(data, separators=(',', ':'))
    
    # 初始化3DES加密器 (CBC模式, PKCS5填充)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    
    # 加密处理
    padded_data = pad(json_str.encode('utf-8'), 8)
    encrypted_data = cipher.encrypt(padded_data)
    
    # 返回Base64编码结果
    return base64.b64encode(encrypted_data).decode('utf-8')

def get_version(jsonParame):
    headers['encrypt']="yes"
    url = "https://czyl.foton.com.cn/est/getVersion.action"
    data = {"jsonParame":jsonParame }
    response = requests.post(url, headers=headers, data=data)
    #print(response.text)
    return response.text
    #print(response.text)
    #print(response)

def decrypt_3des(encrypted_base64):
    print("4")
    # 密钥配置（文本形式）
    key_text = "fontone-trans@lx100$#365"
    iv_text = "20161201"
    
    # 转换为字节 (UTF-8编码)
    key = key_text.encode('utf-8')
    iv = iv_text.encode('utf-8')
    
    # Base64解码加密内容
    encrypted_data = base64.b64decode(encrypted_base64)
    
    # 创建3DES解密器 (CBC模式)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    
    # 解密并移除PKCS5填充
    decrypted_data = unpad(cipher.decrypt(encrypted_data), DES3.block_size)
    #print(decrypted_data)
    
    # 返回解码后的文本转为json
    result = json.loads(decrypted_data.decode('utf-8'))
    data_str = result.get('data')
    data_str = result.get('data')
    if not data_str:
        print("data字段为空")
        return None
    
    data_json = json.loads(data_str)
    return data_json.get('safeKey')  # 返回safeKey值

def signin(memberComplexCode, uid, usertyper, tel, safekey):
    # 创建局部 headers 副本，避免修改全局变量
    local_headers = headers.copy()
    
    # 在副本上修改
    if 'encrypt' in local_headers:
        del local_headers['encrypt']
    
    local_headers['app-token'] = '58891364f56afa1b6b7dae3e4bbbdfbfde9ef489'
    local_headers['app-key'] = '7918d2d1a92a02cbc577adb8d570601e72d3b640'
    local_headers['token'] = ''
    
    url = "https://czyl.foton.com.cn/ehomes-new/homeManager/api/bonus/signActivity2nd"
    data = {
        "memberId": memberComplexCode,
        "userId": uid,
        "userType": usertyper,
        "uid": uid,
        "mobile": tel,
        "tel": tel,
        "phone": tel,
        "brandName": "",
        "seriesName": "",
        "token": "ebf76685e48d4e14a9de6fccc76483e3",
        "safeEnc": int(time.time() * 1000) - int(safekey),
        "businessId": 1
    }
    data = json.dumps(data, separators=(',', ':'))
    response = requests.post(url, headers=local_headers, data=data)
    print(response.text)

def post(memberComplexCode,uid,usertyper,tel,safekey,post_content):#发帖
    headers['content-type'] =  "application/json; charset=utf-8"
    url = "https://czyl.foton.com.cn/ehomes-new/ehomesCommunity/api/post/addJson2nd"
    data = {
        "memberId": memberComplexCode,
        "userId": uid,
        "userType": usertyper,
        "uid": uid,
        "mobile": tel,
        "tel": tel,
        "phone": tel,
        "brandName": "",
        "seriesName": "",
        "token": "ebf76685e48d4e14a9de6fccc76483e3",
        "safeEnc": int(time.time() * 1000)-int(safekey),
        "businessId": 1,
        "content": post_content,
        "postType": 1,
        "topicIdList": [
            192
        ],
        "uploadFlag": 3,
        "title": "",
        "urlList": []
    }
    data = json.dumps(data, separators=(',', ':'))
    response = requests.post(url, headers=headers, data=data)
    print('发帖请求如下:')
    print(response.text)    
    

def get_content():#素颜api请求皮皮语录
    res = requests.get('https://v1.hitokoto.cn/').json()["hitokoto"]
    
    return res

def check_point(memberComplexCode,uid,usertyper,tel,safekey):#检查积分
    hea = {
        "user-agent": "web",
        "accept-encoding": "gzip",
        "content-length": "251",
        "host": "czyl.foton.com.cn",
        "app-key": "7918d2d1a92a02cbc577adb8d570601e72d3b640",
        "content-type": "application/json; charset=utf-8",
        "token": "",
        "app-token": "58891364f56afa1b6b7dae3e4bbbdfbfde9ef489"
        }
    url = "https://czyl.foton.com.cn/ehomes-new/homeManager/api/Member/findMemberPointsInfo"
    data = {
        "memberId": memberid,
        "userId": uid,
        "userType": usertyper,
        "uid": uid,
        "mobile": tel,
        "tel": tel,
        "phone": tel,
        "brandName": "",
        "seriesName": "",
        "token": "ebf76685e48d4e14a9de6fccc76483e3",
        "safeEnc": int(time.time() * 1000)-int(safekey),
        "businessId": 1,
        }
    data = json.dumps(data, separators=(',', ':'))
    res = requests.post(url, headers=hea, data=data).json()
    point = res['data']['pointValue']
    print(f'当前积分：{point}')
    return point


def pk_life_get_safekey():  #皮卡生活获取pk_safekey
    url = "https://czyl.foton.com.cn/ehomes-new/pkHome/version/getVersion"
    data = {
    "deviceType": 1
    }
    data = json.dumps(data, separators=(',', ':'))
    res = requests.post(url, headers=hea, data=data).json()
    return res["data"]["safeKey"]



def pk_life_get_safekey():  # 皮卡生活获取pk_safekey
    url = "https://czyl.foton.com.cn/ehomes-new/pkHome/version/getVersion"
    data = {
        "deviceType": 1
    }
    data = json.dumps(data, separators=(',', ':'))
    res = requests.post(url, headers=hea, data=data).json()
    return res["data"]["safeKey"]


def pk_life_sign(pk_life_token,pk_life_memberComplexCode,pk_life_memberno,pk_life_tel,pk_safekey):
    hea["token"]=pk_life_token
    url = "https://czyl.foton.com.cn/ehomes-new/pkHome/api/bonus/signActivity2nd"
    data = {
        "memberId": pk_life_memberComplexCode,
        "memberID": pk_life_memberno,
        "mobile": pk_life_tel,
        "token": "7fe186bb15ff4426ae84f300f05d9c8d",
        "vin": "",
        "safeEnc": int(time.time() * 1000)-int(pk_safekey)
    }
    data = json.dumps(data, separators=(',', ':'))
    response = requests.post(url, headers=hea, data=data).json()
    print('皮卡生活签到')
    print(response['data'])



conf = os.getenv('ftej2')
if not conf:
    print("未获取到ftej环境变量，请检查配置")
    exit(1)

#分割多账号
# 保存原始的 headers 结构
original_headers = headers.copy()

# 全局保存第一个账号的safekey
global_safekey = None

accounts = conf.split('@')
for i, account in enumerate(accounts):
    try:
        # 每次处理新账号前重置 headers
        headers = original_headers.copy()
        
        # 解析账号信息
        parts = account.split('#')
        tel, usertyper, uid, memberid, memberComplexCode, pk_life_memberno, pk_life_tel, pk_life_token, pk_life_memberComplexCode = parts
        
        # 转换需要的整数类型
        usertyper = int(usertyper)
        uid = int(uid)

        print(f"\n===== 开始处理账号: {tel} =====")
        
        # 复用逻辑：第一个账号正常获取safekey，后续账号复用
        if i == 0:  # 处理第一个账号
            jsonParame = encrypt_data(uid, memberid, usertyper)
            encrypted_base64 = get_version(jsonParame)
            safekey = decrypt_3des(encrypted_base64)
            global_safekey = safekey  # 保存到全局变量
        else:  # 后续账号直接复用第一个账号的safekey
            safekey = global_safekey
        
        print(f'safekey: {safekey}')
        
        point = check_point(memberid, uid, usertyper, tel, safekey)
        
        # 修改后的 signin 函数，不修改全局 headers
        signin(memberComplexCode, uid, usertyper, tel, safekey)
        time.sleep(3)
        
        # 获取内容逻辑
        content_text = ""
        for retry in range(3):
            try:
                response = get_content()
                if hasattr(response, 'json'):
                    content_text = response.json().get('text', '')
                else:
                    content_text = str(response)
                
                if len(content_text) >= 10:
                    break
                else:
                    print(f"内容长度不足({len(content_text)}), 重试中...")
            except Exception as e:
                print(f"获取内容失败: {str(e)}")
            time.sleep(1)
        
        print(content_text)
        
        # 同样需要确保 post 函数不会修改全局 headers
        post(memberComplexCode, uid, usertyper, tel, safekey, content_text)
        time.sleep(3)
        
        # 皮卡生活相关操作
        pk_safekey = pk_life_get_safekey()
        time.sleep(3)
        pk_life_sign(pk_life_token, pk_life_memberComplexCode, pk_life_memberno, pk_life_tel, pk_safekey)
        time.sleep(3)
        
        point1 = check_point(memberid, uid, usertyper, tel, safekey)
        time.sleep(3)
        new_get_point = point1 - point
        print(f'获得积分：{new_get_point}')
        time.sleep(60)
        print('延迟一分钟')
        
    except Exception as e:
        print(f"处理账号时发生错误: {e}")
        continue

print("\n所有账号处理完成")