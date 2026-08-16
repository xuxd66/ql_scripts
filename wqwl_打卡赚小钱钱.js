/**
 * 脚本：wqwl_打卡赚小钱钱.js
 * 描述：微信小程序打卡赚小钱钱
 * 环境变量：wqwl_dkzxqq，多个换行或新建多个变量
 * 环境变量描述：抓包请求参数下的token，格式例如：token#备注1
 * 代理变量：wqwl_daili（获取代理链接，需要返回txt格式的http/https）
 * cron: 0 3 * * * 一天一次
 */


/**
 * 入口：https://gitee.com/cobbWmy/img/blob/master/dakazhuanxiaoqianiqian.png
 * 写本不易走个头呗
 */

const axios = require('axios');
const fs = require('fs');

//代理链接
let proxy = process.env["wqwl_daili"] || '';

//是否用代理，默认使用（填了代理链接）
let isProxy = process.env["wqwl_useProxy"] || true;

//并发数，默认4
let bfs = process.env["wqwl_bfs"] || 4;

// 是否通知
let isNotify = true;

//账号索引
let index = 0;

//ck环境变量名
const ckName = 'wqwl_dkzxqq';

//脚本名称
const name = '微信小程序打卡赚小钱钱'


!(async function () {
    let wqwlkj;

    const filePath = 'wqwl_require.js';
    const url = 'https://raw.githubusercontent.com/298582245/wqwl_qinglong/refs/heads/main/wqwl_require.js';

    if (fs.existsSync(filePath)) {
        console.log('✅wqwl_require.js已存在，无需重新下载，如有报错请重新下载覆盖\n');
        wqwlkj = require('./wqwl_require');
    } else {
        console.log('正在下载wqwl_require.js，请稍等...\n');
        console.log(`如果下载过慢，可以手动下载wqwl_require.js，并保存为wqwl_require.js，并重新运行脚本`)
        console.log('地址：' + url);
        try {
            const res = await axios.get(url);
            fs.writeFileSync(filePath, res.data);
            console.log('✅下载完成，准备开始运行脚本\n');
            wqwlkj = require('./wqwl_require');
        } catch (e) {
            console.log('❌下载失败，请手动下载wqwl_require.js，并保存为wqwl_require.js，并重新运行脚本\n');
            console.log('地址：' + url);
            return; // 下载失败，不再继续执行
        }
    }

    // 确保 require 成功后才继续执行
    try {
        wqwlkj.disclaimer();

        let notify;
        if (isNotify) {
            try {
                notify = require('./sendNotify');
                console.log('✅加载发送通知模块成功');
            } catch (e) {
                console.log('❌加载发送通知模块失败');
                notify = null
            }
        }

        // let fileData = wqwlkj.readFile('dkzxqq')
        class Task {
            constructor(ck) {
                this.index = index++;
                this.ck = ck
                this.maxRetries = 3; // 最大重试次数
                this.retryDelay = 3; // 重试延迟(秒)
            }

            async init() {
                const ckData = this.ck.split('#')
                if (ckData.length < 1) {
                    return this.sendMessage(`${index + 1} 环境变量有误，请检查环境变量是否正确`, true);
                }
                else if (ckData.length === 1) {
                    this.remark = ckData[0].slice(0, 8);
                }
                else {
                    this.remark = ckData[1];
                }
                this.token = ckData[0];
                this.headers = {
                    "accept": "*/*",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "content-type": "application/x-www-form-urlencoded",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "cross-site",
                    "xweb_xhr": "1",
                    "referrer": "https://servicewechat.com/wxd03a809cfc99930b/4/page-frame.html",
                    "referrerPolicy": "unsafe-url",
                }
                /*
                                this.today = wqwlkj.formatDate(new Date())
                                if (!fileData[this.remark])
                                    fileData[this.remark] = {}
                                if (!fileData[this.remark][this.today])
                                    fileData[this.remark][this.today] = { 'sign': false, 'ad': false, 'sp': false }
                                if (fileData[this.remark][this.today]['sign'] && fileData[this.remark][this.today]['ad'] && fileData[this.remark][this.today]['sp']) {
                                    this.sendMessage(`✅今日任务已经全部完成啦`)
                                    return false
                                }
                */
                if (proxy && isProxy) {
                    this.proxy = await wqwlkj.getProxy(this.index, proxy)
                    //console.log(`使用代理：${this.proxy}`)
                    this.sendMessage(`✅使用代理：${this.proxy}`)
                }
                else {
                    this.proxy = ''
                    this.sendMessage(`⚠️不使用代理`)
                }
                return true
            }


            async info() {
                try {
                    const url = this.getUrl('today', 'index')
                    const options = {
                        url: url,
                        headers: this.headers,
                        method: 'GET'
                    }
                    const res = await wqwlkj.request(options, this.proxy)
                    this.sendMessage(`✅获取信息成功,打卡币：${res?.info?.today?.currency}，余额：${res?.info?.today?.money}，今日打卡次数：${res?.info?.today?.clock}`)
                    return { currency: res?.info?.today?.currency, money: res?.info?.today?.money, clock: res?.info?.today?.clock }
                } catch (e) {
                    throw new Error(`❌获取信息失败，${e.message}`)
                }
            }

            async start() {
                try {
                    const url = this.getUrl('addTips', 'my')
                    const options = {
                        url: url,
                        headers: this.headers,
                        method: 'GET'
                    }
                    const res = await wqwlkj.request(options, this.proxy)
                    if (res?.status === 1)
                        return true
                    else
                        return false
                    //this.sendMessage(`✅获取信息成功,打卡币：${res?.info?.today?.currency}，余额：${res?.info?.today?.money}，今日打卡次数：${res?.info?.today?.clock}`)
                    //return { currency: res?.info?.today?.currency, money: res?.info?.today?.money, clock: res?.info?.today?.clock }
                } catch (e) {
                    throw new Error(`❌获取信息失败，${e.message}`)
                }
            }

            async end() {
                try {

                    let url = this.getUrl('sign', 'clock', { captcha_code: '', click_ad: 1 })
                    url += `&captcha_code=&click_ad=1`
                    const options = {
                        url: url,
                        headers: this.headers,
                        method: 'GET'
                    }
                    const res = await wqwlkj.request(options, this.proxy)
                    // console.log(res)
                    if (res?.status === 1)
                        return this.sendMessage(`✅模拟打卡成功`)
                    else
                        return this.sendMessage(`❌模拟打卡失败，原因:: ${JSON.stringify(res)}`)
                    //this.sendMessage(`✅获取信息成功,打卡币：${res?.info?.today?.currency}，余额：${res?.info?.today?.money}，今日打卡次数：${res?.info?.today?.clock}`)
                    //return { currency: res?.info?.today?.currency, money: res?.info?.today?.money, clock: res?.info?.today?.clock }
                } catch (e) {
                    throw new Error(`❌获取信息失败，${e.message}`)
                }
            }


            async Moneyinfo() {
                try {

                    let url = this.getUrl('cash', 'my')
                    const options = {
                        url: url,
                        headers: this.headers,
                        method: 'GET'
                    }
                    const res = await wqwlkj.request(options, this.proxy)
                    // console.log(res)
                    if (res?.status === 1) {
                        const money = res?.info?.member?.money
                        const least_money = res?.info?.least_money
                        this.sendMessage(`✅获取信息成功,余额：${money}，提现最低金额：${least_money}`, true)
                        if (money >= least_money)
                            await this.withdraw(money)
                    }
                    else {
                        return this.sendMessage(`❌获取信息失败，原因:: ${JSON.stringify(res)}`)
                    }
                } catch (e) {
                    throw new Error(`❌获取信息请求失败，${e.message}`)
                }
            }
            async withdraw(money) {
                try {

                    let url = this.getUrl('withdrawals', 'my', { money: money })
                    url += `&money=${money}`
                    const options = {
                        url: url,
                        headers: this.headers,
                        method: 'GET'
                    }
                    const res = await wqwlkj.request(options, this.proxy)
                    // console.log(res)
                    if (res?.status === 1) {
                        return this.sendMessage(`✅提现成功`)
                    }
                    else {
                        return this.sendMessage(`❌提现失败，原因: ${JSON.stringify(res)}`)
                    }
                } catch (e) {
                    throw new Error(`❌提现请求失败，${e.message}`)
                }
            }
            async main() {
                const isFinish = await this.init()
                if (!isFinish)
                    return
                //await this.withdraw(0.04)
                await wqwlkj.sleep(wqwlkj.getRandom(3, 5))

                const { clock } = await this.info()
                if (clock < 5) {
                    let i = parseInt(clock)
                    for (; i < 5; i++) {
                        this.sendMessage(`📝开始第 ${i + 1} 次打卡`)
                        const isStart = await this.start()
                        if (isStart) {
                            await wqwlkj.sleep(wqwlkj.getRandom(30, 40))
                            await this.end()
                        }
                        await wqwlkj.sleep(wqwlkj.getRandom(10, 16))
                    }
                    await this.info()
                }
                await wqwlkj.sleep(wqwlkj.getRandom(3, 5))
                await this.Moneyinfo()

            }

            getUrl(action, contr, arg = {}) {
                if (!this.token || !action)
                    return `❌验证数据为空`
                let url = `https://rr.qq66.cn/app/index.php?i=157&t=0&v=1.0.1&from=wxapp&c=entry&a=wxapp&do=distribute&m=bh_rising&action=${action}&contr=${contr}&token=${this.token}&version=3.5.4`
                const sign = this.getSign(url, arg)
                url += `&sign=${sign}`
                return url
            }
            getSign(e, t, n) {
                const getUrlParam = (url, param) => {
                    const urlObj = new URL(url, 'http://rr.qq66.cn');
                    return urlObj.searchParams.get(param);
                };
                const getQuery = (url) => {
                    const urlObj = new URL(url, 'http://rr.qq66.cn');
                    const params = [];
                    urlObj.searchParams.forEach((value, name) => {
                        params.push({ name, value });
                    });
                    return params;
                };

                let i = "";
                const o = getUrlParam(e, "sign");

                if (o || (t && t.sign)) {
                    return false;
                }

                if (e) {
                    i = getQuery(e);
                }

                if (t) {
                    let s = [];
                    for (let u in t) {
                        if (t.hasOwnProperty(u) && u && t[u] !== "") {
                            s.push({
                                name: u,
                                value: t[u]
                            });
                        }
                    }
                    i = i.concat(s);
                }

                // 替代 _.sortBy(i, "name")
                i.sort((a, b) => {
                    if (a.name < b.name) return -1;
                    if (a.name > b.name) return 1;
                    return 0;
                });

                // 替代 _.uniq(i, true, "name")
                const seen = new Set();
                i = i.filter(item => {
                    if (!item || !item.name) return false;
                    if (seen.has(item.name)) return false;
                    seen.add(item.name);
                    return true;
                });

                let c = "";
                for (let f = 0; f < i.length; f++) {
                    if (i[f] && i[f].name && i[f].value !== "") {
                        c += i[f].name + "=" + i[f].value;
                        if (f < i.length - 1) {
                            c += "&";
                        }
                    }
                }

                const secret = n || undefined;
                //console.log(c, secret);
                return wqwlkj.md5(c + '&' + secret);
            }

            // 带重试机制的请求方法
            async request(options, retryCount = 0) {
                try {
                    const data = await wqwlkj.request(options, this.proxy);
                    return data;

                } catch (error) {
                    this.sendMessage(`🔐检测到请求发生错误，正在重试...`)
                    // 刷新代理
                    const newProxy = await wqwlkj.getProxy(this.index, proxy);
                    this.proxy = newProxy
                    this.sendMessage(`✅代理更新成功:${this.proxy}`);

                    if (retryCount < this.maxRetries && newProxy) {
                        this.sendMessage(`🕒${this.retryDelay * (retryCount + 1)}s秒后重试...`);
                        await wqwlkj.sleep(this.retryDelay * (retryCount + 1));
                        return await this.request(options, retryCount + 1);
                    }

                    throw new Error(`❌请求最终失败: ${error.message}`);
                }
            }


            sendMessage(message, isPush = false) {
                message = `账号[${this.index + 1}](${this.remark}): ${message}`
                if (isNotify && isPush) {
                    return wqwlkj.sendMessage(message + "\n")
                }
                console.log(message)
                return message
            }

        }

        console.log(`${name}开始执行...`);
        const tokens = wqwlkj.checkEnv(process.env[ckName]);
        //console.log(`共${tokens.length}个账号`);
        const totalBatches = Math.ceil(tokens.length / bfs);

        for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
            const start = batchIndex * bfs;
            const end = start + bfs;
            const batch = tokens.slice(start, end);

            console.log(`开始执行第 ${batchIndex + 1} 批任务 (${start + 1}-${Math.min(end, tokens.length)})`);

            const taskInstances = batch.map(token => new Task(token));
            const tasks = taskInstances.map(instance => instance.main());
            const results = await Promise.allSettled(tasks);

            results.forEach((result, index) => {
                const task = taskInstances[index];

                if (result.status === 'rejected') {
                    task.sendMessage(result.reason);
                }
            });

            await wqwlkj.sleep(wqwlkj.getRandom(3, 5));
        }
        // wqwlkj.saveFile(fileData, 'dkzxqq')
        console.log(`${name}全部任务已完成！`);

        const message = wqwlkj.getMessage()
        if (message !== '' && isNotify === true) {
            await notify.sendNotify(`${name} `, `${message} `);
        }

    } catch (e) {
        console.error('❌ 执行过程中发生异常:', e.message);
    }

})();