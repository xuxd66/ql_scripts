/**
 * create: 2025/07/20
 * update: 2024/03/28
 * description: 自行寻找
 * test: 青龙2.19.2
 * 环境变量：wqwl_hg，多个换行或者新建多个
 * 免责声明：本脚本仅用于学习，请勿用于商业用途，否则后果自负，请在下载24小时之内删除，否则请自行承担。有问题自行解决。
 * 注：本脚本大多数代码均为ai写。
 */

const axios = require('axios')
const BASE_URL = 'http://www.iuris.cn'

let index = 0
class HongGuo {
    constructor(userCookie) {
        this.index = index++
        this.ck = userCookie.split("#")
        this.headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json",
            "token": "",
            "unionid": "null",
            "Referer": "http://app.ooowz.cn/"
        }
        this.unionid = ""
        this.isLoggedIn = false
    }
    
    async getCookie() {
        this.sendMessage(`开始执行第${this.index + 1}个账号:${this.ck[0].slice(0, 3)}****${this.ck[0].slice(-4)}`)
        const user = this.ck[0]
        const password = this.ck[1]
        
        try {
            const config = {
                url: BASE_URL + '/user/isuser2',
                method: 'POST',
                headers: this.headers,
                data: JSON.stringify({
                    phone: user,
                    password: password
                }),
                timeout: 10000
            }
            
            const res = await axios(config)
            if (res.data && res.data.data == 1) {
                this.headers['unionid'] = res.data.result.unionid
                this.headers['token'] = res.data.result.token
                this.unionid = res.data.result.unionid
                this.isLoggedIn = true
                this.sendMessage('登录成功')
                return true
            } else {
                this.sendMessage(`登录失败: ${res.data?.content || '未知错误'}`)
                return false
            }
        } catch (error) {
            this.sendMessage(`登录请求失败: ${error.message}`)
            return false
        }
    }

    // 打卡
    async sign() {
        if (!this.isLoggedIn) {
            this.sendMessage('未登录，无法签到')
            return false
        }
        
        try {
            const config = {
                url: BASE_URL + '/user/activeone',
                method: 'POST',
                headers: this.headers,
                data: JSON.stringify({
                    unionid: this.unionid
                }),
                timeout: 10000
            }
            
            const res = await axios(config)
            if (res.data && res.data.code == 1) {
                this.sendMessage('打卡成功')
                return true
            } else {
                this.sendMessage(`打卡失败: ${res.data?.content || '未知错误'}`)
                return false
            }
        } catch (error) {
            this.sendMessage(`打卡请求失败: ${error.message}`)
            return false
        }
    }

    // 查询余额
    async getBalance() {
        if (!this.isLoggedIn) {
            this.sendMessage('未登录，无法查询余额')
            return 0
        }
        
        try {
            const config = {
                url: BASE_URL + '/user/getuserinfo',
                method: 'POST',
                headers: this.headers,
                data: JSON.stringify({
                    unionid: this.unionid
                }),
                timeout: 10000
            }
            
            const res = await axios(config)
            if (res.data && res.data.code == 1) {
                return parseFloat(res.data.result.money) || 0
            } else {
                this.sendMessage(`查询余额失败: ${res.data?.content || '未知错误'}`)
                return 0
            }
        } catch (error) {
            this.sendMessage(`查询余额请求失败: ${error.message}`)
            return 0
        }
    }

    // 提现
    async pushcash() {
        if (!this.isLoggedIn) {
            this.sendMessage('未登录，无法提现')
            return false
        }
        
        // 先查询余额
        const balance = await this.getBalance()
        if (balance < 0.5) {
            this.sendMessage(`余额不足0.5元，当前余额: ${balance}元`)
            return false
        }
        
        try {
            const config = {
                url: BASE_URL + '/trade/pushcash',
                method: 'POST',
                headers: this.headers,
                data: JSON.stringify({
                    unionid: this.unionid,
                    money: 0.5
                }),
                timeout: 10000
            }
            
            const res = await axios(config)
            if (res.data && res.data.code == 1) {
                this.sendMessage('提现成功')
                return true
            } else {
                this.sendMessage(`提现失败: ${res.data?.content || '未知错误'}`)
                return false
            }
        } catch (error) {
            this.sendMessage(`提现请求失败: ${error.message}`)
            return false
        }
    }

    async main() {
        this.sendMessage('>开始登录')
        const loginSuccess = await this.getCookie()
        if (!loginSuccess) {
            this.sendMessage('登录失败，终止执行')
            return
        }
        
        await this.sleep(3000)
        this.sendMessage('>开始签到')
        await this.sign()
        
        await this.sleep(3000)
        this.sendMessage('>开始提现')
        await this.pushcash()
        
        await this.sleep(3000)
        this.sendMessage('>任务完成')
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    sendMessage(text) {
        console.log(`账号[${this.index + 1}]:${text}`)
    }
}

// 获取环境变量
function checkEnv(userCookie) {
    try {
        if (!userCookie) {
            console.log("未找到环境变量 wqwl_hg");
            console.log("🔔还没开始已经结束!");
            process.exit(1);
        }
        
        // 优先使用换行符分割，如果没有换行符则使用&
        let userList;
        if (userCookie.includes("\n")) {
            userList = userCookie.split("\n").filter(n => n.trim());
        } else if (userCookie.includes("&")) {
            userList = userCookie.split("&").filter(n => n.trim());
        } else {
            // 如果没有分隔符，尝试直接使用
            userList = [userCookie];
        }
        
        if (!userList || userList.length === 0) {
            console.log("环境变量格式错误，请检查配置");
            console.log("🔔还没开始已经结束!");
            process.exit(1);
        }

        console.log(`共找到${userList.length}个账号`);
        return userList;
    } catch (e) {
        console.log("环境变量处理错误:", e.message);
        process.exit(1);
    }
}

// 串行执行任务，避免并发风控
async function runTasks(tokens) {
    console.log("红果脚本开始运行");
    
    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];
        const hongGuo = new HongGuo(token);
        await hongGuo.main();
        
        // 账号之间增加延迟，避免风控
        if (i < tokens.length - 1) {
            console.log(`等待5秒后执行下一个账号...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
    
    console.log("全部任务已完成！");
}

!(async function () {
    const tokens = checkEnv(process.env['wqwl_hg']);
    await runTasks(tokens);
})();