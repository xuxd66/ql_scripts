# -*- coding: utf-8 -*-
"""
柚子快看-自动刷金币脚本
================================================================
【功能】自动领取刷视频时长奖励、翻卡奖励、宝箱奖励、任务奖励等金币收益
【依赖】pycryptodome (pip install pycryptodome), requests
【原理】
    1. 请求加密: DES-CBC, 密钥由 APK 签名证书 SPKI 派生(预算为常量), 明文参数 → 加密 → zqkd_param
    2. 响应解密: AES-ECB, 密钥同样由 SPKI 派生, 密文 → 解密 → JSON
    3. 随机校验码: uf.aor() 在密文前后各追加随机字符, 需按 (char % 10) % 3 规则裁剪尾部
【加密架构】
    APK 签名证书(Subject: CN=Android Dev) → Base64(公钥) → substring(9) → substring(0, len-5)
    → substring(len-36) → 36位密钥串 full_key_36
    DES 密钥 = full_key_36[:8] = "c6fNrRQc" (固定, 与 trim 无关)
    DES IV   = Base64URL(MD5(key)[:8])[:8]
    AES 密钥 = full_key_36[:16] = "c6fNrRQcRYFcIx64" (固定)

【青龙面板配置】
    1. 上传脚本到青龙脚本目录, 命名为 youzi_earner.py
    2. 安装依赖: 青龙面板 → 依赖管理 → 添加 pycryptodome requests
    3. 添加环境变量(可选, 不填则使用内置默认账号):
        变量名: YOUZI_ACCOUNT
        变量值: uid1 uid2 uid3 (多个账号用空格/换行/逗号分隔)
        示例:
            单账号:  55580655
            多账号:  55580655 66677788
            多账号换行:
                55580655
                66677788
    4. 添加定时任务:
        命令:  python3 youzi_earner.py
        定时:  0 */2 * * *  (每2小时执行一次)
        带参数: python3 youzi_earner.py --rounds 10 --delay 20 40

【命令行用法】
    python youzi_earner.py                          # 默认账号, 5轮
    python youzi_earner.py --account 123456         # 指定单个账号
    python youzi_earner.py --account 111 222 333    # 多个账号依次执行
    python youzi_earner.py --rounds 10              # 指定轮数
    python youzi_earner.py --delay 30 60            # 轮间等待30-60秒
"""

import base64, json, hashlib, random, string, time, sys
from urllib.parse import quote
import requests
from Crypto.Cipher import DES, AES

# ================================================================
# 常量: 由 APK 签名证书 SPKI 派生的密钥
# ================================================================
# 36位完整密钥串(从 APK v2 签名块提取证书 → Base64(公钥.encoded) → 截取)
# 与 YouthSecurityHelper.rkz.mh() 中的逻辑完全一致
FULL_KEY_36 = 'c6fNrRQcRYFcIx64gZb4XrDIJ9rfiNdTkVQI'

# DES 密钥 = FULL_KEY_36[:8], 对应 YouthSecurityHelper.al.aor() 中的 DESKeySpec(key.getBytes())
DES_KEY = FULL_KEY_36[:8]

# AES 密钥 = FULL_KEY_36[:16], 对应 YouthSecurityHelper.rkz.ftr() 中 AES/ECB 模式
AES_KEY = b'c6fNrRQcRYFcIx64'

# 默认账号(从抓包获取, 可通过命令行 --account 覆盖)
DEFAULT_ACCOUNT = '55580655'

# ================================================================
# 加密 / 解密函数
# ================================================================

def md5_hex(data):
    """计算 MD5, 返回二进制摘要"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).digest()


def encrypt_des(plaintext, key_str):
    """
    DES-CBC 加密, 对应 YouthSecurityHelper.al.aor(key, plaintext)
    1. IV = Base64URL(MD5(key)[:8])[:8]
    2. 密钥 = key[:8].getBytes()
    3. 填充 PKCS7
    4. 返回 IV前缀(12字符) + Base64URL(密文, 无padding)
    """
    md5_digest = md5_hex(key_str.encode('utf-8'))
    iv_b64_full = base64.urlsafe_b64encode(md5_digest[:8]).decode()
    iv = iv_b64_full[:8].encode('utf-8')
    key_bytes = key_str[:8].encode('utf-8')

    cipher = DES.new(key_bytes, DES.MODE_CBC, iv)
    data = plaintext.encode('utf-8')
    pad_len = 8 - (len(data) % 8)
    padded = data + bytes([pad_len] * pad_len)
    ciphertext = cipher.encrypt(padded)

    # IV前缀(12字符 = 8字节的Base64URL) + 密文Base64URL(去尾部=)
    return iv_b64_full[:12] + base64.urlsafe_b64encode(ciphertext).decode().rstrip('=')


def decrypt_response(resp_text):
    """
    AES-ECB 解密服务端响应, 对应 YouthSecurityHelper.rkz.aor()
    密钥 = AES_KEY, 模式 = ECB, 填充 = PKCS7
    """
    raw = base64.b64decode(resp_text.strip())
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    dec = cipher.decrypt(raw)
    # 去 PKCS7 填充
    pad = dec[-1]
    dec = dec[:-pad]
    return json.loads(dec.decode('utf-8'))


def make_zqkd_param(plaintext):
    """
    构造 zqkd_param 参数, 对应 YouthApiHelper.og() → uf.aor() → al.aor()
    1. 随机 trim(0~9) 决定使用密钥前 N 位(N = 36 - trim)
    2. DES-CBC 加密明文
    3. 随机首字符 + 加密结果 + 尾部随机字符
    4. 尾部随机字符数量 = (首字符ASCII % 10) % 3  (对应 uf.aor 的 i = (c % '\\n') % 3)
    """
    trim = random.randint(0, 9)
    key = FULL_KEY_36[:36 - trim]
    encrypted = encrypt_des(plaintext, key)

    # 首字符
    rc = random.choice(string.ascii_letters + string.digits)
    # 尾部随机字符(数量由首字符决定)
    trailing_count = (ord(rc) % 10) % 3
    trailing = ''.join(random.choice(string.ascii_letters + string.digits)
                       for _ in range(trailing_count))

    return quote(rc + encrypted + trailing)


# ================================================================
# 设备指纹参数(从抓包 HAR 提取)
# ================================================================

def build_base_params(account):
    """根据账号ID构建基础设备参数"""
    return (
        'access=WIFI&account=' + account +
        '&androidid=f52c4b31bc9c82af&app-version=1.7.6'
        '&app_device_id=5RP9io4qxPg&app_name=kuaikan_youzi_jzhc'
        '&app_pkg=kuaikan.youzi.jzhc&app_version=1.7.6'
        '&carrier=%E4%B8%AD%E5%9B%BD%E8%81%94%E9%80%9A&channel=c1006&channe=c1006'
        '&dev_mode=&device_model=PLK110&device_type=android&device-platform=android'
        '&dpi=480&inner_version=&is_debug=0&jssdk_version=&language=zh-CN'
        '&memory=8192&mi=0&mobile_type=1&network_type=wifi&os_api=35'
        '&os_version=BP2A.250605.015&resolution=1080x2340&rom_version=BP2A.250605.015'
        '&sim=1&sm_device_id=&storage=256&uid=' + account +
        '&union_id=&user_cert=&version_code=&zqkey=&zqkey_id=&request_time='
    )

# 扩展设备参数(广告/设备指纹相关)
EXTRA_DEVICE_PARAMS = (
    '&channel_code=c1006'
    '&device_brand=OnePlus'
    '&device_id=49249622'
    '&device_platform=android'
    '&oaid=585693158C2D4096B0E80B9A8B57F22Ccc4c434df094e78509ac7575c89b5115'
    '&openudid=f52c4b31bc9c82af'
)


# ================================================================
# API 客户端
# ================================================================

class YouziClient:
    """
    柚子快看 API 客户端
    - 自动管理 PHPSESSID 会话(Cookie 由服务端 Set-Cookie 下发)
    - 所有请求经过 DES 加密, 响应经过 AES 解密
    """

    BASE_URL = 'https://lemon-api.52leho.com'

    # 接口路径映射(含版本前缀, 从 HAR 抓包提取)
    PATHS = {
        'userdata':          '/v15/user/userdata.json',
        'userinfo':          '/v3/user/userinfo.json',
        'collect':           '/v18/Bi/collect.json',
        'tf':                '/v18/bi/tf.json',
        'scoreTime':         '/v18/feed/scoreTime.json',
        'flipCard':          '/v18/Task/flipCard.json',
        'double':            '/v18/Task/double.json',
        'toGetReward':       '/v5/CommonReward/toGetReward.json',
        'nextVideo':         '/v5/Task/nextVideo.json',
        'getTaskList':       '/v17/TaskScoreOptimize/getTaskList.json',
        'readScore':         '/v18/task/readScore.json',
        'csjCpa':            '/v18/task/csjCpa.json',
        'ylhCpa':            '/v18/task/ylhCpa.json',
        'adConversion':      '/v18/task/adConversion.json',
        'rewardView':        '/v18/feed/rewardView.json',
        'rewardVideoCrv':    '/v18/task/rewardVideoCrv.json',
        'bannerstatus':      '/v5/nameless/bannerstatus.json',
        'audit':             '/v15/config/audit.json',
        'machine':           '/v15/config/machine.json',
        'getData':           '/v18/DyShop/getData.json',
        'exchange':          '/v17/TaskScoreOptimize/exchange.json',
    }

    def __init__(self, account=DEFAULT_ACCOUNT):
        self.account = account
        self.base_params = build_base_params(account)
        self.session = requests.Session()
        # 模拟 Android 客户端请求头
        self.session.headers.update({
            'device-platform': 'android',
            'app-pkg': 'kuaikan.youzi.jzhc',
            'User-Agent': 'android',
            'Content-Type': 'application/x-www-form-urlencoded',
        })

    def post(self, endpoint, extra_params=''):
        """
        发送加密 POST 请求
        :param endpoint: 接口路径(如 /v18/feed/scoreTime.json)
        :param extra_params: 额外参数(如 &time=5&type=2)
        :return: 解密后的 JSON dict
        """
        # 拼接基础参数 + 时间戳 + 扩展参数 + 自定义参数
        plaintext = self.base_params + str(int(time.time())) + extra_params
        # 加密为 zqkd_param
        body = 'zqkd_param=' + make_zqkd_param(plaintext)
        # 发送请求(PHPSESSID 由 requests.Session 自动管理)
        resp = self.session.post(self.BASE_URL + endpoint, data=body, timeout=10)
        # 解密响应
        return decrypt_response(resp.text)


# ================================================================
# 业务逻辑
# ================================================================

def get_userdata(client):
    """获取用户当前金币/余额信息"""
    data = client.post(client.PATHS['userdata'])
    if data.get('success'):
        items = data.get('items', {})
        return {
            'score': int(items.get('score', 0)),
            'money': items.get('money', '0'),
            'cash':  items.get('cash_balance', '0'),
        }
    return None


def earn_one_cycle(client):
    """
    执行一轮金币领取, 遍历所有可领取的奖励类型
    返回本轮总获得金币数

    可领取的奖励类型(均从 HAR 抓包逆向得到, 按收益排序):
    [高收益-广告类]
    - csjCpa:       穿山甲CPA广告, 固定+16000分, 需要 media_extra(含 media_verify)
    - ylhCpa:       优量汇CPA广告, 固定+10399分, 需要 media_extra(含 media_verify)
    - nextVideo:    看视频奖励, +5000~9000分, 需要 action 参数
    - toGetReward:  通用奖励领取, 分数不等, 需要 action 参数

    [中收益-任务类]
    - scoreTime:    刷视频时长, 每个时间段+50分
    - flipCard:     翻卡奖励, +1~9分

    [低收益-其他]
    - double:       翻倍奖励
    - getData:      商城数据(返回累计余额, 非增量)
    - exchange:     兑换现金
    """
    earned = 0

    # ========== 高收益: 广告CPA任务 ==========
    # 穿山甲CPA广告(+16000分) —— 需要 media_extra 含 media_verify
    # media_verify 由穿山甲SDK生成, 这里使用HAR抓包的有效值
    media_extra_csj = (
        '%7B%22media_app_id%22%3A%22sspTiYBitFIIky83%22'
        '%2C%22media_replace_score%22%3A0'
        '%2C%22media_scene_id%22%3A%22%22'
        '%2C%22media_slot_id%22%3A%22986448232%22'
        '%2C%22media_verify%22%3A%22PmBFmhaIgxUoxKRcd%2BLXxJvMv8wAgUJhosbvEI9b8MhX30MMVc3SUWPD92r44jCwClqpmYUAw%2BYTB7LfWq0OYyfXs87sV89mcx4PBPB%2BOVod6AKvoMZOERLIVp3yjQc250INKJhHeWXtRAppipGlnw%5Cu003d%5Cu003d%22'
        '%2C%22params_action_type%22%3A%22%22'
        '%2C%22params_app_name%22%3A%22%22'
        '%2C%22params_app_package%22%3A%22%22'
        '%2C%22params_slot_type%22%3A%22%22'
        '%2C%22position_id%22%3A%22987%22'
        '%2C%22slot_platform%22%3A%22CSJ%22'
        '%2C%22slot_price%22%3A%2218.75%22'
        '%2C%22slot_type%22%3A%22ListFlow%22'
        '%2C%22tactics_mold%22%3A%22bidding%22%7D'
    )
    try:
        d = client.post('/v18/task/csjCpa.json',
                        '&need_download=1&media_extra=' + media_extra_csj)
        if d.get('success'):
            s = d.get('items', {}).get('score', 0)
            if s:
                earned += s
                print('    穿山甲CPA广告: +%d' % s)
        time.sleep(0.5)
    except Exception as e:
        print('    穿山甲CPA: 请求失败 %s' % str(e)[:40])

    # 优量汇CPA广告(+10399分) —— 需要 media_extra 含 media_verify
    media_extra_ylh = (
        '%7B%22media_app_id%22%3A%22sspTiYBitFIIky83%22'
        '%2C%22media_replace_score%22%3A0'
        '%2C%22media_scene_id%22%3A%22%22'
        '%2C%22media_slot_id%22%3A%22983630425%22'
        '%2C%22media_verify%22%3A%22PmBFmhaIgxUoxKRcd%2BLXxJvMv8wAgUJhosbvEI9b8MhX30MMVc3SUWPD92r44jCwClqpmYUAw%2BYTB7LfWq0OYyfXs87sV89mcx4PBPB%2BOXjIRbaPrbZZqn%2BuIi5blA7qnBREXy67rgKwfie%2B1w7fA%5Cu003d%5Cu003d%22'
        '%2C%22params_action_type%22%3A%22%22'
        '%2C%22params_app_name%22%3A%22%22'
        '%2C%22params_app_package%22%3A%22%22'
        '%2C%22params_slot_type%22%3A%22%22'
        '%2C%22position_id%22%3A%22987%22'
        '%2C%22slot_platform%22%3A%22YLH%22'
        '%2C%22slot_price%22%3A%2210.0%22'
        '%2C%22slot_type%22%3A%22ListFlow%22'
        '%2C%22tactics_mold%22%3A%22bidding%22%7D'
    )
    try:
        d = client.post('/v18/task/ylhCpa.json',
                        '&need_download=0&media_extra=' + media_extra_ylh)
        if d.get('success'):
            s = d.get('items', {}).get('score', 0)
            if s:
                earned += s
                print('    优量汇CPA广告: +%d' % s)
        time.sleep(0.5)
    except Exception as e:
        print('    优量汇CPA: 请求失败 %s' % str(e)[:40])

    # ========== 高收益: 视频/奖励类 ==========
    # nextVideo 看视频奖励(+5000~9000分)
    next_video_actions = [
        ('box_reward',       '看视频-宝箱'),
        ('task_score_optimize', '看视频-领金币'),
        ('flip_card_reward', '看视频-翻卡'),
    ]
    for action, name in next_video_actions:
        try:
            d = client.post('/v5/Task/nextVideo.json',
                            '&action=%s&index=0&video_id=0' % action)
            if d.get('success'):
                s = d.get('items', {}).get('score', 0)
                if s:
                    earned += s
                    print('    %s: +%d' % (name, s))
            time.sleep(0.3)
        except Exception as e:
            print('    %s: 请求失败 %s' % (name, str(e)[:40]))

    # toGetReward 通用奖励领取
    reward_actions = [
        ('flip_card_reward',         '翻卡奖励'),
        ('box_reward',               '宝箱奖励'),
        ('task_score_optimize',      '刷视频领金币'),
        ('bonus_video_ad_award',     '视频广告奖励'),
    ]
    for action, name in reward_actions:
        try:
            d = client.post('/v5/CommonReward/toGetReward.json',
                            '&action=%s&index=0&video_id=0' % action)
            if d.get('success'):
                s = d.get('items', {}).get('score', 0)
                if s:
                    earned += s
                    print('    %s: +%d' % (name, s))
            time.sleep(0.3)
        except Exception as e:
            print('    %s: 请求失败 %s' % (name, str(e)[:40]))

    # ========== 中收益: 刷视频时长 ==========
    time_rewards = [
        ('&time=5&type=2',   '刷视频5s'),
        ('&time=10&type=2',  '刷视频10s'),
        ('&time=15&type=2',  '刷视频15s'),
        ('&time=20&type=2',  '刷视频20s'),
        ('&time=25&type=2',  '刷视频25s'),
    ]
    for extra, name in time_rewards:
        try:
            d = client.post('/v18/feed/scoreTime.json', extra)
            if d.get('success'):
                s = d.get('items', {}).get('score', 0)
                if s:
                    earned += s
                    print('    %s: +%d' % (name, s))
            time.sleep(0.3)
        except Exception as e:
            print('    %s: 请求失败 %s' % (name, str(e)[:40]))

    # 翻卡奖励
    try:
        d = client.post('/v18/Task/flipCard.json', '&index=0')
        if d.get('success'):
            s = d.get('items', {}).get('score', 0)
            if s:
                earned += s
                print('    翻卡: +%d' % s)
        time.sleep(0.3)
    except Exception as e:
        print('    翻卡: 请求失败 %s' % str(e)[:40])

    # ========== 低收益: 翻倍/其他 ==========
    try:
        d = client.post('/v18/Task/double.json', '&index=0')
        if d.get('success'):
            s = d.get('items', {}).get('score', 0)
            if s:
                earned += s
                print('    翻倍奖励: +%d' % s)
        time.sleep(0.3)
    except Exception as e:
        print('    翻倍奖励: 请求失败 %s' % str(e)[:40])

    # ========== 兑换现金 ==========
    try:
        d = client.post('/v17/TaskScoreOptimize/exchange.json')
        if d.get('success'):
            items = d.get('items', {})
            score = items.get('score', 0)
            money = items.get('money', '0')
            if money and money != '0':
                print('    兑换现金: %s元 (剩余金币:%s)' % (money, score))
        time.sleep(0.3)
    except Exception as e:
        print('    兑换现金: 请求失败 %s' % str(e)[:40])

    return earned


# ================================================================
# 主入口
# ================================================================

def run_one_account(account, rounds, delay_min, delay_max):
    """对单个账号执行刷金币循环"""
    print('\n' + '=' * 55)
    print('  账号: %s' % account)
    print('=' * 55)

    client = YouziClient(account=account)

    # 查询初始余额
    info = get_userdata(client)
    if info:
        print('初始状态: 金币=%d  现金=%s元  余额=%s元' % (
            info['score'], info['money'], info['cash']))
    else:
        print('[错误] 无法获取用户数据, 请检查账号 %s' % account)
        return 0

    total_earned = 0

    for cycle in range(rounds):
        print('\n--- 第 %d/%d 轮 ---' % (cycle + 1, rounds))

        earned = earn_one_cycle(client)
        total_earned += earned

        # 查询本轮后余额
        info_after = get_userdata(client)
        if info_after:
            print('  本轮获得: +%d | 当前金币: %d | 现金: %s元' % (
                earned, info_after['score'], info_after['money']))

        # 轮间随机等待(最后一轮不等待)
        if cycle < rounds - 1:
            wait = random.randint(delay_min, delay_max)
            print('  等待 %d 秒...' % wait)
            time.sleep(wait)

    # 最终汇总
    info_final = get_userdata(client)
    print('\n最终状态:', end='')
    if info_final:
        print(' 金币=%d  现金=%s元  余额=%s元' % (
            info_final['score'], info_final['money'], info_final['cash']))
    else:
        print(' 查询失败')
    print('本轮总计获得: %d 金币' % total_earned)

    return total_earned


def get_accounts_from_env():
    """
    从环境变量读取账号列表, 支持两种方式:

    方式一(推荐): YOUZI_ACCOUNT 环境变量, 多个uid用空格或逗号分隔
        示例: YOUZI_ACCOUNT="55580655 66677788 99900011"

    方式二: 命令行 --account 参数
        示例: python youzi_earner.py --account 55580655 66677788
    """
    import os

    env_accounts = os.environ.get('YOUZI_ACCOUNT', '').strip()
    if env_accounts:
        # 支持空格、逗号、换行分隔
        accounts = [a.strip() for a in env_accounts.replace(',', ' ').replace('\n', ' ').split() if a.strip()]
        if accounts:
            return accounts

    return None


def main():
    """
    主入口, 支持多账号

    青龙面板配置:
        环境变量名: YOUZI_ACCOUNT
        环境变量值: uid1 uid2 uid3 (空格分隔)
        例如: 55580655 66677788

    命令行用法:
        python youzi_earner.py                          # 默认账号, 5轮
        python youzi_earner.py --account 123456         # 指定单个账号
        python youzi_earner.py --account 111 222 333    # 多个账号依次执行
        python youzi_earner.py --rounds 10 --delay 20 40
    """
    import argparse

    parser = argparse.ArgumentParser(description='柚子快看自动刷金币')
    parser.add_argument('--account', '-a', nargs='+', default=None,
                        help='账号ID, 支持多个(空格分隔)')
    parser.add_argument('--rounds', '-r', type=int, default=5, help='每个账号执行轮数(默认5)')
    parser.add_argument('--delay', '-d', type=int, nargs=2, default=[15, 30],
                        help='轮间等待秒数范围(默认15 30)')
    args = parser.parse_args()

    # 优先命令行参数, 其次环境变量, 最后默认账号
    accounts = args.account or get_accounts_from_env() or [DEFAULT_ACCOUNT]

    print('=' * 55)
    print('  柚子快看 自动刷金币脚本 v3')
    print('  账号数: %d | 每账号轮数: %d | 等待: %d~%ds' % (
        len(accounts), args.rounds, args.delay[0], args.delay[1]))
    print('  账号列表: %s' % ', '.join(accounts))
    print('=' * 55)

    grand_total = 0

    for i, account in enumerate(accounts):
        earned = run_one_account(account, args.rounds, args.delay[0], args.delay[1])
        grand_total += earned

        # 多账号之间额外等待
        if i < len(accounts) - 1:
            wait = random.randint(30, 60)
            print('\n>>> 切换账号, 等待 %d 秒...' % wait)
            time.sleep(wait)

    print('\n' + '=' * 55)
    print('  全部完成! 总计获得: %d 金币' % grand_total)
    print('=' * 55)


if __name__ == '__main__':
    main()
