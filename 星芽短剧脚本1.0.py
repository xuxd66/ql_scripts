#软件星芽短剧
#青龙变量xydj，抓取软件变量Authorization
from cgitb import text
import json
import time
import requests as r
import re
import os
import random

adv = 1
if os.environ.get("xydj"):
    dvm = os.environ["xydj"]
    if dvm != '':
        if "@" in dvm:
            Coo = dvm.split("@")
        elif "&" in dvm:
            Coo = dvm.split('&')
        else:
            Coo = dvm.split('\n')
    adv = 1
    for i in Coo:
        try:
            # 接口URL定义
            xxurl = "https://app.whjzjx.cn/v1/account/detail"  # 个人信息
            signurl = "https://speciesweb.whjzjx.cn/v1/sign/do"  # 签到
            rwlburl = "https://speciesweb.whjzjx.cn/v1/task/list?device_id=252cf01c9b6793c92afb138cb390b5e65"  # 任务列表
            scurl = "https://app.whjzjx.cn/v1/theater/doing_look_v2"  # 收藏
            adurl = "https://speciesweb.whjzjx.cn/v1/sign"  # 看广告
            zkadurl = "https://speciesweb.whjzjx.cn/v1/task_ad/claim"  # 再看广告&签到看广告
            dzurl = "https://speciesweb.whjzjx.cn/v1/task/like"  # 点赞
            gkscurl = "https://speciesweb.whjzjx.cn/v1/sign/escalation"  # 加观看时长
            gkjlurl = "https://speciesweb.whjzjx.cn/v1/sign/sign_multi_stage"  # 观看时长奖励领取
            kbxurl = "https://speciesweb.whjzjx.cn/v1/box/open"  # 开宝箱
            bxadurl = "https://speciesweb.whjzjx.cn/v1/box/view_ad"  # 开宝箱广告
            gjzjb = "https://speciesweb.whjzjx.cn/v1/task/shopping_claim"  # 逛街赚金币
            bbyurl = "https://speciesweb.whjzjx.cn/v3/task/red_rain_prize" #红包雨

            # 请求头
            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 14; 22041211AC Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.179 Mobile Safari/537.36 _dsbridge",
                'Accept': "application/json, text/plain, */*",
                'Accept-Encoding': "gzip, deflate, br, zstd",
                'content-length': "0",
                'pragma': "no-cache",
                'cache-control': "no-cache",
                'sec-ch-ua-platform': "\"Android\"",
                'authorization': i,
                'device_type': "22041211AC",
                'sec-ch-ua': "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Android WebView\";v=\"138\"",
                'sec-ch-ua-mobile': "?1",
                'user_agent': "Mozilla/5.0 (Linux; Android 14; 22041211AC Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.179 Mobile Safari/537.36 _dsbridge",
                'raw_channel': "default",
                'dev_token': "BauENsVpLb0uo9u-0uCtbPHK5gcQi1zbjpsJJ71YAaKQFyXALnIjtwwtXCrtwM6V3YEucTaZwW7pkxagCTPfuIn8aGOE2JWW942qtB35yFwVOJoAgh0Kq8TC1QcE8HjIFbCYg-mcKFs6zicr8YhzRGqmRh3zSehUdMwXQOSK8iiU*",
                'channel': "default",
                'device_id': "2f397d31a6ce93b5a94f840ba25ac996d",
                'device_platform': "android",
                'app_version': "3.9.3",
                'device_brand': "Redmi",
                'os_version': "14",
                'origin': "https://h5static.xingya.com.cn",
                'x-requested-with': "com.jz.xydj",
                'sec-fetch-site': "cross-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                'priority': "u=1, i"
            }

            # 登录验证
            def denglu():
                global adv
                dl = r.get(xxurl, headers=headers)
                dll = json.loads(dl.text)
                if dll["msg"] == "成功":
                    name = dll["data"]["nickname"]
                    print(f'******开始【星芽免费短剧账号{adv}】{name} *********')
                    print("💰目前金币数量:" + str(dll["data"]["species"]))
                    print("💰可提现:" + str(dll["data"]["cash_remain"]))
                else:
                    print("登录失败，请重新获取Authorization")

            # 签到
            def qiandao():
                qd = r.post(signurl, headers=headers)
                qdd = json.loads(qd.text)
                print("📅开始签到")
                if qdd["msg"] == "success":
                    print("✅签到成功获取金币:" + str(qdd["data"]["coin_val"]))
                    time.sleep(2)
                    signad()
                else:
                    print("❌签到失败原因:" + str(qdd["msg"]))

            # 签到广告
            def signad():
                zkadbody = {"ad_type": 4}
                zkad = r.post(zkadurl, headers=headers, json=zkadbody)
                zkkadd = json.loads(zkad.text)
                if zkkadd["code"] == "ok":
                    print("💱看签到广告成功获取金币:" + str(zkkadd["data"]["coin_val"]))
                else:
                    print("❌再看广告失败，原因:" + str(zkkadd["msg"]))

            # 看广告
            def lookad():
                adbody = {"type": 4, "mark": 2}
                ad = r.post(adurl, headers=headers, json=adbody)
                add = json.loads(ad.text)
                if add["msg"] == "签到成功":
                    print("💱看广告成功获取金币:" + str(add["data"]["species"]))
                else:
                    print("❌看广告失败原因:" + str(add["msg"]))

            # 再看广告
            def looklookad():
                zkadbody = {"ad_type": 2}
                zkad = r.post(zkadurl, headers=headers, json=zkadbody)
                zkkadd = json.loads(zkad.text)
                if zkkadd["code"] == "ok":
                    print("💱再看广告成功获取金币:" + str(zkkadd["data"]["coin_val"]))
                else:
                    print("❌再看广告失败，原因:" + str(zkkadd["msg"]))

            # 收藏
            def shoucang():
                sjs = random.randint(1, 2000)
                scbody = {"kind": 2, "target_id": sjs, "category": 1, "is_auto_collect": False}
                sc = r.post(scurl, headers=headers, json=scbody)
                scc = json.loads(sc.text)
                if scc["msg"] == "成功":
                    print("✅收藏成功")
                else:
                    print("❌收藏失败")

            # 点赞
            def dianzan():
                sjs = random.randint(1, 116161)
                dzbody = {"theater_id": sjs}
                dz = r.post(dzurl, headers=headers, json=dzbody)
                dzz = json.loads(dz.text)
                if dzz["msg"] == "success":
                    print("💱点赞成功获取金币:" + str(dzz["data"]["info"]["coin_val"]))
                else:
                    print("❌点赞失败，原因:" + str(dzz["msg"]))

            # 增加观看时长
            def gksc():
                print("🆙观看加时长运行")
                for _ in range(10):
                    gkbody = {"type": 3}
                    gk = r.post(gkscurl, headers=headers, json=gkbody)
                    gkk = json.loads(gk.text)
                    if gkk["msg"] == "上报成功":
                        print("📈增加时长成功")
                        time.sleep(2)
                    else:
                        print("❌增加失败，原因:" + str(gkk["msg"]))
                        time.sleep(2)
                        lqbody = {"type": 3, "makes": [1, 2, 3, 4, 5, 6, 7], "device_id": "87387123-7A4D-4B6A-912A-30CABD9CD4B3"}
                        lq = r.post(gkjlurl, headers=headers, json=lqbody)
                        lqq = json.loads(lq.text)
                        if lqq["msg"] == "签到成功":
                            print("💱领取观看时长金币成功:" + str(lqq["data"]["coin_value"]))
                        else:
                            print("❌领取观看时长金币失败，原因:" + str(lqq["msg"]))
                        break

            # 宝箱广告1
            def adbox():
                print("📺观看宝箱广告1")
                bxadbody = {"config_id": 3, "coin_val": 72, "ad_num": 2}
                bxad = r.post(bxadurl, headers=headers, json=bxadbody)
                bxadd = json.loads(bxad.text)
                if bxadd["msg"] == "success":
                    print("💰宝箱广告观看成功获得金币:" + str(bxadd["data"]["coin_val"]))
                else:
                    print("❌开宝箱失败，原因:" + str(bxadd["msg"]))

            # 宝箱广告2
            def adbox2():
                print("📺观看宝箱广告2")
                bxadbody = {"config_id": 3, "coin_val": 72, "ad_num": 1}
                bxad = r.post(bxadurl, headers=headers, json=bxadbody)
                bxadd = json.loads(bxad.text)
                if bxadd["msg"] == "success":
                    print("💰宝箱广告观看成功获得金币:" + str(bxadd["data"]["coin_val"]))
                else:
                    print("❌开宝箱失败，原因:" + str(bxadd["msg"]))

            # 开宝箱
            def openbox():
                print("🆙开始开宝箱")
                time.sleep(2)
                for _ in range(10):
                    boxbody = {"config_id": 3}
                    box = r.post(kbxurl, headers=headers, json=boxbody)
                    boxx = json.loads(box.text)
                    if boxx["msg"] == "success":
                        print("🗳️开宝箱成功获得金币:" + str(boxx["data"]["coin_val"]))
                        time.sleep(2)
                        adbox()
                        time.sleep(2)
                        adbox2()
                        time.sleep(2)
                    else:
                        print("❌开宝箱失败，原因:" + str(boxx["msg"]))
                        break

            # 逛街赚金币（执行7次，若某次失败则停止）
            def guangjie_zuanjinbi():
                print("🛒开始执行逛街赚金币（共7次，失败则停止）")
                total_runs = 7  # 总次数
                interval_ms = 0.3  # 间隔时间（秒，300毫秒）
                success = True  # 标记是否继续执行
                
                for run in range(1, total_runs + 1):
                    if not success:
                        break  # 若之前失败，直接退出循环
                    
                    print(f"\n第{run}次逛街赚金币")
                    gjzjb_payload = {"now_cpm": 15800}
                    
                    try:
                        gjzjb_response = r.post(gjzjb, headers=headers, json=gjzjb_payload)
                        gjzjb_data = json.loads(gjzjb_response.text)
                        
                        if gjzjb_data.get("msg") == "success":
                            print(f"💱成功，获得金币: {gjzjb_data.get('data', {}).get('coin_val', 0)}")
                        else:
                            print(f"❌失败，原因: {gjzjb_data.get('msg', '未知错误')}")
                            success = False  # 标记失败，下一次不再执行
                    except Exception as e:
                        print(f"❌第{run}次请求出错: {str(e)}")
                        success = False  # 异常也视为失败
                    
                    # 最后一次不间隔，非最后一次且成功时才间隔
                    if run != total_runs and success:
                        time.sleep(interval_ms)
                
                if success:
                    print("\n🛒7次逛街赚金币全部执行成功")
                else:
                    print("\n🛒逛街赚金币已停止（因某次失败）")
            
            # 红包雨请求（使用指定payload）
            def red_rain():
                print("🎁开始红包雨请求")
                payload_str = "QZJAhhTOA9Bp/3FiQwmUBzcgrP5NqTmiEY8KKoxHF8MqezF3BsJIJ2IkwIf69LpoF8MNQqFkp/Cb7aewru4HLZMumWhgxsohWM2BOXzHE8rseCZz7YX/HZNtNr+cNt6P8uCYuikAP/6j0MSbj/o6C9EP6t3k4VgBzpF3SY+3kVDQsmcZ02+I9QW75VxhTWFRNK9n+qTveoqrUX1EbxM3nRqW2Rlj13Mpq3pJ828cQhffS/4ZHPm5tuejTuvEDsJhOvRq+NQzIq2ek/oE+6CJuj0v5Vpo19uLZPPULjWRS0GILBEpZQC5cpfOLRCkWH0QTtOj7rd8pS8Ym60vlPCSFu71paV0bNHMdpicFU3C6J1HXcLUWKPh++Sv0OnWguo/BUfm1UsUrZ2aN71SjUNgMJVrMf9m1Z+lGHbP2N2KhxQOEtDIY3AVfhSNgAlMrcsvIAo+LP0ZW0+lSUcnet7xEg=="
                try:
                    response = r.post(bbyurl, headers=headers, data=payload_str)
                    try:
                        data = json.loads(response.text)
                    except:
                        print(f"❌红包雨返回内容不是JSON格式: {response.text[:200]}")
                        return
                    msg_content = data.get("msg", "未知信息")
                    if msg_content == "success":
                        print("✅红包雨请求成功")
                        print(f"获得金币: {data.get('data', {}).get('coin_val', 0)}")
                    else:
                        print(f"❌红包雨请求失败，返回信息: {msg_content}")
                except Exception as e:
                    print(f"❌红包雨请求出错: {str(e)}")

            # 主程序执行
            denglu()
            adv += 1
            time.sleep(2)
            qiandao()
            gksc()
            openbox()
            guangjie_zuanjinbi()  # 调用逛街赚金币函数
            red_rain()  # 调用红包雨请求函数
            time.sleep(2)
            print("📊查看任务列表")



            # 任务列表处理
            class Task:
                def __init__(self, code, num, total):
                    self.code = code
                    self.num = num
                    self.total = total

                def is_completed(self):
                    if self.total is not None and self.num >= self.total:
                        return True
                    elif self.total is None:
                        return True
                    else:
                        return False

            rwlb = r.get(rwlburl, headers=headers)
            rwlbb = json.loads(rwlb.text)
            task_list_data = rwlbb['data']['task_list']
            tasks = []

            for task_data in task_list_data:
                code = task_data['code']
                ext_data = task_data.get('ext')
                num = ext_data.get('num', 0) if ext_data else 0
                total = ext_data.get('total') if ext_data else None
                tasks.append(Task(code, num, total))

            for task in tasks:
                if task.is_completed():
                    if task.code == '1030':
                        print(f"🆗收藏新剧任务已完成！({task.num}/{task.total})")
                    elif task.code == '1060':
                        print(f"🆗看视频金币任务已完成！({task.num}/{task.total})")
                    elif task.code == '1080':
                        print(f"🆗点赞剧集任务已完成！({task.num}/{task.total})")
                    elif task.code == '1070':
                        print(f"🆗分享短剧任务已完成！({task.num}/{task.total})")
                else:
                    if task.code == '1030':
                        print(f"收藏新剧({task.num}/{task.total})")
                        print("🔛开始收藏新剧")
                        for _ in range(task.total - task.num):
                            shoucang()
                            time.sleep(2)
                    elif task.code == '1060':
                        print(f"看视频金币({task.num}/{task.total})")
                        print("🔛开始看广告")
                        for _ in range(task.total - task.num):
                            lookad()
                            time.sleep(2)
                            looklookad()
                            time.sleep(2)
                    elif task.code == '1080':
                        print(f"点赞剧集({task.num}/{task.total})")
                        for _ in range(task.total - task.num):
                            dianzan()
                            time.sleep(2)
                    elif task.code == '1070':
                        print(f"分享短剧({task.num}/{task.total})")
                    else:
                        print(f"{task.code} 任务描述未指定。")
        except:
                print("⚠️⚠️⚠️脚本报错执行下一个账号⚠️⚠️⚠️")
