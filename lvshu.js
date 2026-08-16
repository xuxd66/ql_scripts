#!/usr/bin/env node

const crypto = require('crypto');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// ========== 环境变量配置 ==========
const ACCOUNTS_CONFIG = process.env.TREECOIN_ACCOUNTS || process.env.YYB_GO1 || '';
const INVITE_CODE = process.env.TREECOIN_INVITE_CODE || 'XYKTD8MY';
const ENABLE_BIND_INVITER = true;

// ========== 并发配置 ==========
const MAX_CONCURRENT = parseInt(process.env.TREECOIN_MAX_CONCURRENT) || 2;
const ACCOUNT_DELAY_MIN = parseInt(process.env.TREECOIN_DELAY_MIN) || 3000;
const ACCOUNT_DELAY_MAX = parseInt(process.env.TREECOIN_DELAY_MAX) || 5000;

// ========== 缓存配置 ==========
const CACHE_DIR = process.env.TREECOIN_CACHE_DIR || './cache';
const CACHE_FILE = path.join(CACHE_DIR, 'treecoin_cache.json');
const CACHE_DURATION = 24 * 60 * 60 * 1000;

// ========== 请求参数 ==========
const API_TIMEOUT = 15000;
const BASE_URL = 'https://treecoin.cn/api';
const GCM_KEY = Buffer.from('asldhlfhdshkfashfluksdahfkjsadhfkjsdhfjshjkfhlakjshfjsdhfhsadflh'.substring(0, 32), 'utf8');

// ========== 风险控制配置 ==========
const RISK_CONFIG = {
    actionDelayMin: 600,
    actionDelayMax: 1800,
    signStepDelayMin: 300,
    signStepDelayMax: 1000,
    adDelayMin: 3000,
    adDelayMax: 6000,
    maxAdRetries: 10,
    rateLimitWaitBase: 300000,
    uaPool: [
        'Mozilla/5.0 (Linux; Android 14; 24069RA21C Build/UKQ1.240116.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/146.0.7680.178 Mobile Safari/537.36 XWEB/1460217 MMWEBSDK/20260202 MMWEBID/1137 MicroMessenger/8.0.71.3080(0x28004750) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
        'Mozilla/5.0 (Linux; Android 13; MI 13 Build/TKQ1.220829.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7645.166 Mobile Safari/537.36 XWEB/1420097 MMWEBSDK/20251201 MMWEBID/2048 MicroMessenger/8.0.70.2660(0x28004638) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
        'Mozilla/5.0 (Linux; Android 12; OPPO Find X6 Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7622.121 Mobile Safari/537.36 XWEB/1380156 MMWEBSDK/20251001 MMWEBID/3312 MicroMessenger/8.0.69.2520(0x28004532) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
        'Mozilla/5.0 (Linux; Android 15; Pixel 9 Build/AP31.240905.013; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/148.0.7700.201 Mobile Safari/537.36 XWEB/1480032 MMWEBSDK/20260301 MMWEBID/789 MicroMessenger/8.0.72.3200(0x28004855) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
        'Mozilla/5.0 (Linux; Android 11; HUAWEI Mate 40 Pro Build/HUAWEINOH-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.116 Mobile Safari/537.36 XWEB/1300211 MMWEBSDK/20250601 MMWEBID/1567 MicroMessenger/8.0.65.2200(0x28004130) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64'
    ]
};

// ========== 缓存管理 ==========
function ensureCacheDir() {
    if (!fs.existsSync(CACHE_DIR)) {
        fs.mkdirSync(CACHE_DIR, { recursive: true });
    }
}

function loadCache() {
    try {
        if (fs.existsSync(CACHE_FILE)) {
            const data = fs.readFileSync(CACHE_FILE, 'utf8');
            return JSON.parse(data);
        }
    } catch (err) {}
    return { authCodes: {} };
}

function saveCache(cache) {
    try {
        ensureCacheDir();
        fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2), 'utf8');
    } catch (err) {}
}

function getCachedAuthCode(server, ref) {
    const cache = loadCache();
    const key = `${server}|${ref}`;
    const cached = cache.authCodes?.[key];
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        return cached;
    }
    return null;
}

function saveAuthCodeToCache(server, ref, authCode, userInfo) {
    const cache = loadCache();
    const key = `${server}|${ref}`;
    if (!cache.authCodes) cache.authCodes = {};
    cache.authCodes[key] = { 
        authCode: authCode,
        userInfo: userInfo,
        timestamp: Date.now() 
    };
    saveCache(cache);
}

// ========== 工具函数 ==========
function parseAccounts() {
    if (!ACCOUNTS_CONFIG) return [];
    
    const accountMap = new Map();
    const entries = [];
    
    ACCOUNTS_CONFIG.split('\n')
        .map(line => line.trim())
        .filter(Boolean)
        .forEach(entry => {
            let server, ref, authCode;
            
            const hashIndex = entry.indexOf('#');
            if (hashIndex !== -1) {
                const beforeHash = entry.substring(0, hashIndex);
                authCode = entry.substring(hashIndex + 1).trim();
                
                if (beforeHash.includes('@')) {
                    const [serverPart, refPart] = beforeHash.split('@', 2);
                    server = serverPart.trim();
                    ref = refPart.trim();
                } else {
                    return;
                }
            } else {
                if (entry.includes('@')) {
                    const [serverPart, refPart] = entry.split('@', 2);
                    server = serverPart.trim();
                    ref = refPart.trim();
                    authCode = null;
                } else {
                    return;
                }
            }
            
            if (!server || !ref) return;
            
            let serverClean = server;
            if (serverClean.startsWith('http://')) {
                serverClean = serverClean.substring(7);
            } else if (serverClean.startsWith('https://')) {
                serverClean = serverClean.substring(8);
            }
            serverClean = serverClean.replace(/\/+$/, '');
            
            if (authCode && accountMap.has(authCode)) {
                console.log(`⚠️ 跳过重复的授权码: ${authCode.substring(0, 10)}... (ref: ${ref})`);
                return;
            }
            
            if (authCode) {
                accountMap.set(authCode, true);
            }
            
            entries.push({ 
                server: serverClean, 
                ref: ref,
                authCode: authCode || null
            });
        });
    
    return entries;
}

function genDeviceFP(index) {
    return `BROWSER_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 11)}`;
}

function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function randomDelay(min, max) {
    const ms = Math.floor(Math.random() * (max - min + 1)) + min;
    return sleep(ms);
}

// ========== 核心账号类 ==========
class TreeCoinClient {
    constructor(deviceFP) {
        this.deviceFP = deviceFP;
        this.sessionId = null;
        this.cbcKey = null;
        this.userInfo = null;
        this.userAgent = RISK_CONFIG.uaPool[Math.floor(Math.random() * RISK_CONFIG.uaPool.length)];
        this.authCode = null;
    }

    _getHeaders() {
        return {
            'User-Agent': this.userAgent,
            'Referer': 'https://treecoin.cn/home',
            'Origin': 'https://treecoin.cn',
            'X-Requested-With': 'com.tencent.mm',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-Device-Fingerprint': this.deviceFP
        };
    }

    _getRequestConfig() {
        return {
            headers: this._getHeaders(),
            timeout: API_TIMEOUT
        };
    }

    async loginWithAuthCode(authCode) {
        this.authCode = authCode;
        const res = await axios.post(`${BASE_URL}/auth/login-by-auth-code`, {
            authCode: authCode,
            device_fingerprint: this.deviceFP
        }, this._getRequestConfig());

        if (res.data.c !== 1) {
            throw new Error(res.data.msg || '登录失败');
        }

        this.sessionId = res.data.data.session.sessionId;
        this.cbcKey = Buffer.from(res.data.data.session.sessionKey, 'base64');
        this.userInfo = res.data.data.user.dataValues;
        return this.userInfo;
    }

    cbcEncrypt(obj) {
        const plain = Buffer.from(JSON.stringify(obj), 'utf8');
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-cbc', this.cbcKey, iv);
        const encrypted = Buffer.concat([cipher.update(plain), cipher.final()]);
        return Buffer.concat([iv, encrypted]).toString('base64');
    }

    cbcDecrypt(b64) {
        const raw = Buffer.from(b64, 'base64');
        const decipher = crypto.createDecipheriv('aes-256-cbc', this.cbcKey, raw.slice(0, 16));
        const decrypted = Buffer.concat([decipher.update(raw.slice(16)), decipher.final()]);
        return JSON.parse(decrypted.toString('utf8'));
    }

    gcmEncrypt(obj) {
        const plain = Buffer.from(JSON.stringify(obj), 'utf8');
        const iv = crypto.randomBytes(12);
        const cipher = crypto.createCipheriv('aes-256-gcm', GCM_KEY, iv);
        const encrypted = Buffer.concat([cipher.update(plain), cipher.final()]);
        return {
            data: Buffer.concat([encrypted, cipher.getAuthTag()]).toString('hex'),
            iv: iv.toString('hex')
        };
    }

    async request(path, data = {}, isEncrypt = true) {
        let payload;
        if (isEncrypt) {
            payload = {
                sessionId: this.sessionId,
                encryptedData: this.cbcEncrypt(data),
                nonce: uuid(),
                timestamp: Date.now()
            };
        } else {
            payload = data;
        }
        const res = await axios.post(`${BASE_URL}${path}`, payload, this._getRequestConfig());
        return res.data.encrypted ? this.cbcDecrypt(res.data.data) : res.data;
    }

    async prepareAd() {
        return await this.request('/app/ad-reward/prepare', {});
    }

    async claimAd(token) {
        return await this.request('/app/ad-reward/claim', { token: token }, true);
    }

    async signIn() {
        await this.request('/app/t', { deviceId: this.deviceFP });
        await randomDelay(RISK_CONFIG.signStepDelayMin, RISK_CONFIG.signStepDelayMax);

        const inner = this.gcmEncrypt({ token: '', deviceId: this.deviceFP });
        const outer = this.cbcEncrypt({ encryptedData: inner.data, iv: inner.iv });

        const payload = {
            sessionId: this.sessionId,
            encryptedData: outer,
            nonce: uuid(),
            timestamp: Date.now()
        };
        const res = await axios.post(`${BASE_URL}/app/signin`, payload, this._getRequestConfig());
        const result = res.data.encrypted ? this.cbcDecrypt(res.data.data) : res.data;

        if (result.c !== 1) {
            throw new Error(result.msg || '签到失败');
        }
        return result;
    }

    async bindInviter(inviteCode) {
        return await this.request('/app/user/bind-inviter', { inviteCode: inviteCode });
    }

    isAdExhaustedError(msg) {
        if (!msg) return false;
        return /次数已用完|已用完|明天|刷新|没有更多|暂无|额外奖励/.test(msg);
    }

    isAdRateLimitError(msg) {
        if (!msg) return false;
        return /休息|稍后|频繁|限流|等待|请休息/.test(msg);
    }

    parseWaitTime(msg) {
        if (!msg) return null;
        const match = msg.match(/(\d+)\s*分\s*(\d+)?\s*秒/);
        if (match) {
            const minutes = parseInt(match[1]) || 0;
            const seconds = parseInt(match[2]) || 0;
            return (minutes * 60 + seconds) * 1000;
        }
        const match2 = msg.match(/(\d+)\s*秒/);
        if (match2) {
            return parseInt(match2[1]) * 1000;
        }
        return null;
    }
}

// ========== 广告任务（优化版，支持中断和恢复） ==========
async function watchAds(client, accountIdx) {
    let totalReward = 0;
    let watchedCount = 0;
    let consecutiveRateLimit = 0;
    const log = (msg) => console.log(`[账号${accountIdx}] ${msg}`);

    for (let i = 1; i <= 5; i++) {
        let adCompleted = false;
        let retryCount = 0;
        let waitTimeMs = 0;

        while (!adCompleted && retryCount < RISK_CONFIG.maxAdRetries) {
            try {
                // 如果等待时间超过60秒，先中断，让其他账号先执行
                if (waitTimeMs > 60000) {
                    log(`⏸️ 等待时间过长 (${Math.ceil(waitTimeMs/1000)}秒)，暂停当前账号，稍后继续...`);
                    // 保存进度，返回部分结果
                    return { 
                        watchedCount, 
                        totalReward: totalReward.toFixed(2),
                        paused: true,
                        nextAdIndex: i,
                        waitTimeMs: waitTimeMs
                    };
                }

                if (waitTimeMs > 0) {
                    const waitSeconds = Math.ceil(waitTimeMs / 1000);
                    log(`⏳ 等待 ${waitSeconds} 秒后重试...`);
                    await sleep(waitTimeMs);
                    waitTimeMs = 0;
                }

                log(`📺 正在获取第 ${i}/5 个广告${retryCount > 0 ? ` (重试${retryCount})` : ''}...`);
                const prepareResult = await client.prepareAd();

                if (prepareResult.c !== 1) {
                    const errorMsg = prepareResult.msg || '未知错误';
                    
                    if (client.isAdExhaustedError(errorMsg)) {
                        log(`⚠️ 今日广告奖励次数已用完`);
                        return { watchedCount, totalReward: totalReward.toFixed(2), paused: false };
                    }
                    
                    if (client.isAdRateLimitError(errorMsg)) {
                        consecutiveRateLimit++;
                        const parsedWait = client.parseWaitTime(errorMsg);
                        if (parsedWait) {
                            waitTimeMs = parsedWait + 5000;
                            log(`⏳ 频率限制: ${errorMsg}，等待后重试...`);
                        } else {
                            const extraWait = consecutiveRateLimit * 30000;
                            waitTimeMs = RISK_CONFIG.rateLimitWaitBase + extraWait + Math.random() * 60000;
                            log(`⏳ 频率限制(第${consecutiveRateLimit}次)，等待 ${Math.ceil(waitTimeMs/60000)} 分钟后重试...`);
                        }
                        retryCount++;
                        continue;
                    }
                    
                    log(`⚠️ 获取广告失败: ${errorMsg}`);
                    retryCount++;
                    await randomDelay(2000, 4000);
                    continue;
                }

                consecutiveRateLimit = 0;
                
                const { token, remaining, used, total } = prepareResult.data;
                if (remaining === 0) {
                    log(`⚠️ 今日广告已看完 (${used}/${total})`);
                    return { watchedCount, totalReward: totalReward.toFixed(2), paused: false };
                }

                log(`✅ 获取广告成功 (已看 ${used}/${total}, 剩余 ${remaining})`);
                const watchTime = Math.floor(Math.random() * 3000) + 3000;
                log(`⏳ 模拟观看 ${(watchTime / 1000).toFixed(1)} 秒...`);
                await sleep(watchTime);

                const claimResult = await client.claimAd(token);
                if (claimResult.c === 1) {
                    const reward = claimResult.data.reward;
                    totalReward += reward;
                    watchedCount++;
                    adCompleted = true;
                    waitTimeMs = 0;
                    consecutiveRateLimit = 0;
                    log(`🎉 获得奖励: +${reward} 树苗 (累计: +${totalReward.toFixed(2)})`);
                } else {
                    const claimMsg = claimResult.msg || '未知错误';
                    if (client.isAdExhaustedError(claimMsg)) {
                        log(`⚠️ 今日广告奖励次数已用完`);
                        return { watchedCount, totalReward: totalReward.toFixed(2), paused: false };
                    }
                    if (client.isAdRateLimitError(claimMsg)) {
                        consecutiveRateLimit++;
                        const parsedWait = client.parseWaitTime(claimMsg);
                        if (parsedWait) {
                            waitTimeMs = parsedWait + 5000;
                            log(`⏳ 频率限制: ${claimMsg}，等待后重试...`);
                        } else {
                            const extraWait = consecutiveRateLimit * 30000;
                            waitTimeMs = RISK_CONFIG.rateLimitWaitBase + extraWait + Math.random() * 60000;
                            log(`⏳ 频率限制(第${consecutiveRateLimit}次)，等待 ${Math.ceil(waitTimeMs/60000)} 分钟后重试...`);
                        }
                        retryCount++;
                        continue;
                    }
                    log(`⚠️ 领取奖励失败: ${claimMsg}`);
                    retryCount++;
                    await randomDelay(2000, 4000);
                }
            } catch (err) {
                log(`❌ 出错: ${err.message}`);
                retryCount++;
                await randomDelay(2000, 4000);
            }
        }
        
        if (!adCompleted && i < 5) {
            log(`⚠️ 第 ${i} 个广告未能完成，跳过...`);
            await randomDelay(10000, 20000);
        }
        
        if (i < 5 && adCompleted) {
            await randomDelay(RISK_CONFIG.adDelayMin, RISK_CONFIG.adDelayMax);
        }
    }
    return { watchedCount, totalReward: totalReward.toFixed(2), paused: false };
}

// ========== 运行单个账号 ==========
async function runAccount(entry, accountIndex, totalAccounts) {
    const prefix = `🌸 账号[${accountIndex}]`;
    console.log(`${prefix} 开始处理...`);

    try {
        const { server, ref, authCode: providedAuthCode } = entry;
        const deviceFP = genDeviceFP(accountIndex);
        
        let finalAuthCode = providedAuthCode;
        
        if (!finalAuthCode) {
            const cached = getCachedAuthCode(server, ref);
            if (cached) {
                finalAuthCode = cached.authCode;
                console.log(`${prefix} 📦 从缓存获取授权码: ${finalAuthCode.substring(0, 10)}...`);
            } else {
                console.log(`${prefix} ❌ 没有授权码配置，且缓存中也没有`);
                return null;
            }
        }
        
        const client = new TreeCoinClient(deviceFP);
        console.log(`${prefix} 🔑 使用授权码登录... (authCode: ${finalAuthCode.substring(0, 10)}...)`);
        await client.loginWithAuthCode(finalAuthCode);
        console.log(`${prefix} ✅ 登录成功 | 昵称: ${client.userInfo.nickName} | 树苗: ${client.userInfo.vitality}`);

        saveAuthCodeToCache(server, ref, finalAuthCode, client.userInfo);

        if (ENABLE_BIND_INVITER && INVITE_CODE) {
            console.log(`${prefix} 🔗 绑定邀请码 ${INVITE_CODE} ...`);
            try {
                const bindResult = await client.bindInviter(INVITE_CODE);
                if (bindResult.c === 1) {
                    console.log(`${prefix} ✅ 邀请码绑定成功`);
                } else {
                    console.log(`${prefix} 🔒 ${bindResult.msg || '已绑定或无需绑定'}`);
                }
            } catch (bindErr) {
                console.log(`${prefix} 🔒 ${bindErr.message}`);
            }
            await randomDelay(RISK_CONFIG.actionDelayMin, RISK_CONFIG.actionDelayMax);
        }
        
        console.log(`${prefix} 📺 开始观看广告...`);
        const adResult = await watchAds(client, accountIndex);
        
        if (adResult.paused) {
            console.log(`${prefix} ⏸️ 广告任务暂停 (已看 ${adResult.watchedCount}/5 个，获得 ${adResult.totalReward} 树苗)`);
            console.log(`${prefix} 💡 将在下次运行时继续`);
            return {
                accountIndex: accountIndex,
                ref: ref,
                userInfo: client.userInfo,
                authCode: finalAuthCode,
                adWatched: adResult.watchedCount,
                adReward: adResult.totalReward,
                paused: true
            };
        }
        
        console.log(`${prefix} 📊 观看广告完成: ${adResult.watchedCount}/5 个, 获得 ${adResult.totalReward} 树苗`);
        
        console.log(`${prefix} 📝 签到中...`);
        try {
            const signResult = await client.signIn();
            if (signResult.c === 1) {
                const data = signResult.data || signResult;
                console.log(`${prefix} 🎉 签到成功`);
                if (data.increase) console.log(`${prefix} 🌱 获得树苗: +${data.increase}`);
                if (data.continuousReward) console.log(`${prefix} 🎁 连续奖励: +${data.continuousReward}`);
            }
        } catch (signErr) {
            if (signErr.message && /已签/.test(signErr.message)) {
                console.log(`${prefix} ⚠️ 今日已签到`);
            } else {
                throw signErr;
            }
        }

        return {
            accountIndex: accountIndex,
            ref: ref,
            userInfo: client.userInfo,
            authCode: finalAuthCode,
            adWatched: adResult.watchedCount,
            adReward: adResult.totalReward,
            paused: false
        };
    } catch (err) {
        console.log(`${prefix} ❌ 处理失败: ${err.message}`);
        return null;
    }
}

// ========== 并发控制 ==========
async function runWithConcurrency(tasks, concurrency) {
    const results = [];
    const executing = new Set();
    
    for (let i = 0; i < tasks.length; i++) {
        const task = tasks[i];
        const promise = task().then(result => {
            executing.delete(promise);
            return result;
        });
        executing.add(promise);
        results.push(promise);
        
        if (executing.size >= concurrency) {
            await Promise.race(executing);
        }
    }
    
    return Promise.all(results);
}

// ========== 主程序 ==========
async function main() {
    try {
        console.log('═══════════════════════════════════');
        console.log('🌲 绿树田园任务启动');
        console.log(`🕐 ${new Date().toLocaleString()}`);
        console.log('═══════════════════════════════════');
        console.log();

        const cache = loadCache();
        const authCodeCount = Object.keys(cache.authCodes || {}).length;
        console.log(`📦 缓存目录: ${CACHE_DIR}`);
        console.log(`📦 授权码缓存: ${authCodeCount} 条`);
        console.log(`⏰ 缓存有效期: 24小时`);
        console.log();

        const entries = parseAccounts();
        if (entries.length === 0) {
            console.log('❌ 未配置账号环境变量');
            console.log();
            console.log('📌 配置格式：');
            console.log('  TREECOIN_ACCOUNTS="192.168.3.174:8000@1#YOUR_AUTH_CODE"');
            console.log('  多账号换行分隔');
            return 1;
        }

        console.log(`📋 账号总数：${entries.length}`);
        console.log(`🚀 最大并发数：${MAX_CONCURRENT}`);
        console.log(`🎯 邀请码：${INVITE_CODE}`);
        console.log();

        console.log('📌 账号状态：');
        entries.forEach((entry, index) => {
            if (entry.authCode) {
                console.log(`  账号${index + 1}: ref=${entry.ref}, ✅ 有授权码`);
            } else {
                const cached = getCachedAuthCode(entry.server, entry.ref);
                if (cached) {
                    console.log(`  账号${index + 1}: ref=${entry.ref}, 📦 缓存授权码`);
                } else {
                    console.log(`  账号${index + 1}: ref=${entry.ref}, ❌ 无授权码`);
                }
            }
        });
        console.log();

        const tasks = entries.map((entry, index) => {
            return async () => {
                if (MAX_CONCURRENT < entries.length) {
                    const delay = Math.floor(Math.random() * (ACCOUNT_DELAY_MAX - ACCOUNT_DELAY_MIN + 1)) + ACCOUNT_DELAY_MIN;
                    await sleep(delay);
                }
                return await runAccount(entry, index + 1, entries.length);
            };
        });

        const results = await runWithConcurrency(tasks, MAX_CONCURRENT);

        let successCount = 0;
        let totalAdReward = 0;
        let totalAdWatched = 0;
        let pausedCount = 0;

        results.forEach((result, index) => {
            if (result) {
                if (result.paused) {
                    pausedCount++;
                } else {
                    successCount++;
                }
                totalAdReward += parseFloat(result.adReward || 0);
                totalAdWatched += result.adWatched || 0;
            }
        });

        console.log('═══════════════════════════════════');
        console.log(`📊 执行汇总`);
        console.log(`✅ 完成账号：${successCount}/${entries.length}`);
        if (pausedCount > 0) {
            console.log(`⏸️  暂停账号：${pausedCount} (等待冷却)`);
        }
        console.log(`📺 总观看广告：${totalAdWatched} 个`);
        console.log(`🌱 总获得树苗：+${totalAdReward.toFixed(2)}`);
        console.log('═══════════════════════════════════');
        
        if (pausedCount > 0) {
            console.log();
            console.log('💡 提示：部分账号因频率限制暂停，建议5-10分钟后重新运行');
            console.log('   重新运行将自动继续未完成的广告');
        }

        return successCount === entries.length ? 0 : 1;
    } catch (err) {
        console.error(`❌ 程序异常: ${err.message}`);
        return 1;
    }
}

// 执行
if (require.main === module) {
    main().then(code => {
        process.exit(code);
    }).catch(err => {
        console.error(err);
        process.exit(1);
    });
}