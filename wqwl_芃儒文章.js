/**
 * 脚本：wqwl_芃儒文章.js
 * 描述：微信小程序芃儒文章
 * 环境变量：wqwl_frwz，多个换行或新建多个变量
 * 环境变量描述：抓包请求参数下的state，格式例如：state#备注1
 * 代理变量：wqwl_daili（获取代理链接，需要返回txt格式的http/https）
 * cron: 0 3 * * * 刷满为止
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
const ckName = 'wqwl_frwz';

//脚本名称
const name = '微信小程序芃儒文章'


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

        let fileData = wqwlkj.readFile('frwz')
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
                this.state = ckData[0];
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

                this.today = wqwlkj.formatDate(new Date())
                if (!fileData[this.remark])
                    fileData[this.remark] = {}
                if (!fileData[this.remark][this.today])
                    fileData[this.remark][this.today] = { 'sign': false, 'ad': false, 'sp': false }
                if (fileData[this.remark][this.today]['sign'] && fileData[this.remark][this.today]['ad'] && fileData[this.remark][this.today]['sp']) {
                    this.sendMessage(`✅今日任务已经全部完成啦`)
                    return false
                }

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

            async myScoreTasks() {
                const options = {
                    url: this.getUrl('MyScoreTasks'),
                    headers: this.headers,
                    method: 'GET'
                }
                //console.log(JSON.stringify(options))
                try {
                    let res = await this.request(options, 0)
                    let ad, sp
                    if (res.message === 'ok') {
                        ad = res?.data?.videoAd
                        sp = res?.data?.rollVideo
                        if (sp === undefined || ad === undefined) {
                            this.sendMessage(`🔍检查到为今天首次运行,将模拟第一次运行`)
                            await this.scoreTaskVideoAd()
                            await wqwlkj.sleep(wqwlkj.getRandom(8, 16))
                            await this.scoreTaskRollVideo()
                        }
                        res = await this.request(options, 0)
                        ad = res?.data?.videoAd
                        sp = res?.data?.rollVideo
                        const adStep = ad?.step || 0
                        const adTotal_step = ad?.total_step || 0
                        this.sendMessage(`任务${ad?.type_text}(${adStep}/${adTotal_step})`)

                        const spStep = sp?.step || 0
                        const spTotal_step = sp?.total_step || 0
                        this.sendMessage(`任务${sp?.type_text}(${spStep}/${spTotal_step})`)
                        return { ad: adTotal_step - adStep, sp: spTotal_step - spStep }
                    }
                    else {
                        this.sendMessage(`❌获取积分任务列表失败，${res.message}`)
                        return 0
                    }
                }
                catch (e) {
                    this.sendMessage(`❌请求获取积分任务列表失败，${e}`)
                    console.log(e)
                }
            }


            async scoreTaskSignIn() {
                const options = {
                    url: this.getUrl('ScoreTaskSignIn'),
                    headers: this.headers,
                    method: 'GET'
                }
                try {
                    const res = await this.request(options, 0)

                    if (res.message === 'ok') {
                        this.sendMessage(`✅签到成功，积分+${res?.data?.reward_score}`)
                        fileData[this.remark][this.today]['sign'] = true
                    } else {
                        if (res.message.includes('已签到'))
                            fileData[this.remark][this.today]['sign'] = true
                        this.sendMessage(`❌签到失败，${res.message}`)
                    }
                }
                catch (e) {
                    throw new Error(`❌请求签到失败，${e}`)
                }
            }

            async scoreTaskVideoAd() {
                const options = {
                    url: this.getUrl('ScoreTaskVideoAd'),
                    headers: this.headers,
                    method: 'GET'
                }
                try {
                    const res = await this.request(options, 0)

                    if (res.message === 'ok') {
                        this.sendMessage(`✅观看广告成功，积分+${res?.data?.reward_score}`)
                    } else {
                        this.sendMessage(`❌观看广告失败，${res.message}`)
                    }
                }
                catch (e) {
                    throw new Error(`❌观看广告失败，${e}`)
                }
            }
            async scoreTaskRollVideo() {
                const options = {
                    url: this.getUrl('ScoreTaskRollVideo'),
                    headers: this.headers,
                    method: 'GET'
                }
                try {
                    const res = await this.request(options, 0)

                    if (res.message === 'ok') {
                        this.sendMessage(`✅观看视频成功，积分+${res?.data?.reward_score}`)
                    } else {
                        this.sendMessage(`❌观看视频失败，${res.message}`)
                    }
                }
                catch (e) {
                    throw new Error(`❌观看视频请求失败，${e}`)
                }
            }


            async withdrawUserScore() {
                const options = {
                    url: this.getUrl('WithdrawUserScore'),
                    headers: this.headers,
                    method: 'GET'
                }
                try {
                    const res = await this.request(options, 0)

                    if (res.message === 'ok') {
                        let cash = res?.data?.max
                        cash = Math.floor(cash * 10) / 10;
                        this.sendMessage(`💸可提现最大余额：${cash}`, true)
                        if (cash > 99999) {
                            this.sendMessage(`准备提现`)
                            await this.withdrawApply(cash)
                        }
                    } else {
                        this.sendMessage(`❌获取余额失败，${res.message}`)
                    }
                }
                catch (e) {
                    throw new Error(`❌获取余额请求失败，${e}`)
                }
            }
            async withdrawApply(cash) {
                let url = this.getUrl('WithdrawApply', { cash: cash })
                url += '&cash=' + cash
                const options = {
                    url: url,
                    headers: this.headers,
                    method: 'GET'
                }
                try {
                    const res = await this.request(options, 0)
                    console.log(JSON.stringify(res))
                    if (res.message === 'ok') {
                        this.sendMessage(`✅提现成功`)
                    } else {
                        this.sendMessage(`❌提现失败，${res.message}`)
                    }
                }
                catch (e) {
                    throw new Error(`❌请求提现失败，${e}`)
                }
            }


            async main() {
                const isFinish = await this.init()
                if (!isFinish)
                    return
                await wqwlkj.sleep(wqwlkj.getRandom(3, 5))
                if (fileData[this.remark][this.today]['sign'] && fileData[this.remark][this.today]['ad'] && fileData[this.remark][this.today]['sp'])
                    return this.sendMessage(`✅今日任务已经全部完成啦`)
                else
                    await this.scoreTaskSignIn()
                const times = await this.myScoreTasks()
                await wqwlkj.sleep(wqwlkj.getRandom(3, 5))
                let i = 0, j = 0
                for (i = 0; i < times.ad; i++) {
                    const sleep = wqwlkj.getRandom(30, 40)
                    this.sendMessage(`🔁开始第${i + 1}次模拟观看广告，等待待${sleep}秒...`);
                    await wqwlkj.sleep(sleep)
                    await this.scoreTaskVideoAd()
                }
                if (i >= times.ad)
                    fileData[this.remark][this.today]['ad'] = true
                await wqwlkj.sleep(wqwlkj.getRandom(3, 5))
                for (j = 0; j < times.sp; j++) {
                    const sleep = wqwlkj.getRandom(8, 16)
                    this.sendMessage(`🔁开始第${j + 1}次模拟观看视频，等待待${sleep}秒...`);
                    await wqwlkj.sleep(sleep)
                    await this.scoreTaskRollVideo()
                }
                if (j >= times.sp)
                    fileData[this.remark][this.today]['sp'] = true
                await wqwlkj.sleep(wqwlkj.getRandom(3, 5))
                await this.withdrawUserScore()
            }

            getUrl(Do, arg = {}) {
                if (!this.state || !Do)
                    return `❌验证数据为空`
                let url = `https://weiqing.lingchuangwang.com/app/index.php?i=89&t=0&v=1.0.6&from=wxapp&c=entry&a=wxapp&do=${Do}&state=${this.state}&m=mof_shortvideo&_vi=76`
                const _t = (new Date).getTime()
                const _ut = _t + 1
                url += `&_t=${_t}&_ut=${_ut}`
                const sign = this.getSign(url, arg)
                url += `&sign=${sign}`
                return url
            }
            getSign(e, t, n) {
                const getUrlParam = (url, param) => {
                    const urlObj = new URL(url, 'http://dummy.com');
                    return urlObj.searchParams.get(param);
                };
                const getQuery = (url) => {
                    const urlObj = new URL(url, 'http://dummy.com');
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

                const secret = n || 'wq_mof_short_video_by_moufer_2020';
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
                    let newProxy;
                    if (isProxy) {
                        newProxy = await wqwlkj.getProxy(this.index, proxy);
                        this.proxy = newProxy
                        this.sendMessage(`✅代理更新成功:${this.proxy}`);
                    } else {
                        this.sendMessage(`⚠️未使用代理`);
                        newProxy = true
                    }

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
        wqwlkj.saveFile(fileData, 'frwz')
        console.log(`${name}全部任务已完成！`);

        const message = wqwlkj.getMessage()
        if (message !== '' && isNotify === true) {
            await notify.sendNotify(`${name} `, `${message} `);
        }

    } catch (e) {
        console.error('❌ 执行过程中发生异常:', e.message);
    }

})();