/**
 * 望潮自动阅读与抽奖 (V25.0 by妖火24245)
 * 1. 第一次抽奖（在线时长）：位置在中间 -> 兜底使用【屏幕比例】。
 * 2. 第二次抽奖（阅读任务）：位置靠上 -> 兜底使用【自定义坐标】。
 * 3. 核心原则：优先识别文字，识别不到才用兜底。其他逻辑完全不动。
 * 4. 适配性能差手机，增加延时，效率慢一些。
 * 5. 如果比例或者文字识别不到，坐标获取使用另一个坐标.js获取填到下方。
 * 6. by妖火id：24245 凌乱相对简单，没有搞复杂的逻辑
 * 7. 配合定时启动每日自动，移除了pluspush通知模块，需要的自己AI加。
 */

"auto";

// ==========================================
// 【自定义区：仅用于第二次阅读抽奖】
// 请填写阅读任务完成后，那个靠上的转盘中心的绝对坐标
// ==========================================
var DIY_X = 360;  // 阅读抽奖-横坐标 (X)
var DIY_Y = 500;  // 阅读抽奖-纵坐标 (Y) - 建议填您测量的实际值

// ==========================================
// 环境与权限 (保持不变)
// ==========================================
if (!device.isScreenOn()) {
    device.wakeUp();
    sleep(1000);
}
device.keepScreenOn(15 * 60 * 1000); 

const WIDTH = device.width;
const HEIGHT = device.height;
const GREEN_COLOR = "#52c41a"; 

setScreenMetrics(WIDTH, HEIGHT);

// 自动授权线程
threads.start(function() {
    for (let i = 0; i < 20; i++) {
        let btn = textMatches(/立即开始|允许|开始投屏|确定/).findOne(500);
        if (btn) { btn.click(); break; }
        sleep(500);
    }
});

if (!requestScreenCapture()) {
    toastLog("请开启截图权限");
    exit();
}

console.show();
console.setPosition(WIDTH * 0.3, 0); 
console.setSize(WIDTH * 0.7, HEIGHT * 0.25);

threads.start(function() {
    while (true) {
        var now = new Date();
        ui.run(() => { 
            console.setTitle("望潮V25 | " + now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds()); 
        });
        sleep(1000);
    }
});

log("=== V25.0 启动 (双模式版) ===");

// ==========================================
// 主流程 (完全保持稳定逻辑)
// ==========================================

function main() {
    launchApp("望潮");
    log(">>> APP启动，强制等待7秒...");
    visualWait(7, "启动加载");

    while (true) {
        if (isHomePage()) {
            console.hide(); sleep(500);
            let entry = text("阅读有礼").visibleToUser(true).findOne(1000);
            if (entry) {
                click(entry.bounds().centerX(), entry.bounds().centerY());
                console.show();
                if (!monitorLoading(10)) { back(); sleep(2000); }
            } else {
                back(); console.show(); sleep(2000);
            }
        } 
        else if (isRealTaskPage()) {
            log("✅ 已在任务页，等待3秒...");
            visualWait(3, "数据同步"); 
            
            runBusiness(); 

            log("🎉 任务完成，挂机12分钟...");
            visualWait(12 * 60, "在线挂机");
            device.cancelKeepingAwake(); 
            home();
            break;
        }
        else {
            sleep(1500);
            if (!isHomePage() && !isRealTaskPage()) back();
        }
    }
}

main();

// ==========================================
// 业务逻辑
// ==========================================

function runBusiness() {
    // 1. 时长抽奖 (位置在中间)
    let bonusBtn = textContains("点击去抽奖").findOne(2000);
    if (bonusBtn) {
        let img = captureScreen();
        let c = images.pixel(img, bonusBtn.bounds().centerX(), bonusBtn.bounds().centerY());
        if (!colors.isSimilar(colors.toString(c), GREEN_COLOR, 30)) {
            log(">> 执行时长抽奖...");
            click(bonusBtn.bounds().centerX(), bonusBtn.bounds().centerY());
            // 传入模式 1：代表时长抽奖
            enhancedDraw(1); 
        } else {
            log(">> 时长奖励已领");
        }
    }

    // 2. 阅读任务 
    for (let i = 0; i < 15; i++) {
        let task = text("待完成").visibleToUser(true).findOne(1500);
        if (!task) {
            swipe(WIDTH/2, HEIGHT*0.7, WIDTH/2, HEIGHT*0.4, 800);
            sleep(1500);
            if (!text("待完成").exists()) break;
            task = text("待完成").visibleToUser(true).findOne(1000);
        }
        if (task) {
            click(task.bounds().centerX(), task.bounds().centerY());
            sleep(2000);
            for (let j = 0; j < 5; j++) {
                swipe(WIDTH/2, HEIGHT*0.8, WIDTH/2, HEIGHT*0.5, 800);
                sleep(1500);
            }
            backToTaskList();
        }
    }

    // 3. 阅读后的抽奖 (位置靠上)
    let finalBtn = text("抽奖").visibleToUser(true).findOne(2000);
    if (finalBtn) {
        log(">> 执行阅读任务抽奖...");
        click(finalBtn.bounds().centerX(), finalBtn.bounds().centerY());
        // 传入模式 2：代表阅读抽奖
        enhancedDraw(2); 
    }
}

// ==========================================
// 双模式抽奖函数
// @param mode: 1=时长抽奖(中间), 2=阅读抽奖(靠上)
// ==========================================

function enhancedDraw(mode) {
    console.hide(); 
    sleep(1500); // 等待转盘加载
    
    let clicked = false;
    let startWait = Date.now();
    
    // 1. 优先尝试：通用文字识别 (5秒)
    while (Date.now() - startWait < 5000) {
        let btn = text("点击抽奖").findOne(500) || desc("点击抽奖").findOne(500);
        if (btn) {
            click(btn.bounds().centerX(), btn.bounds().centerY());
            clicked = true;
            log("触发：文字识别点击");
            break;
        }
        sleep(500);
    }
    
    // 2. 兜底方案：根据模式选择不同的点击位置
    if (!clicked) {
        if (mode === 1) {
            // 模式1：时长抽奖 -> 使用【屏幕比例】(中间偏上)
            log("⚠️ 模式1兜底：使用屏幕比例点击");
            // 0.48 是大概中间的位置
            click(WIDTH * 0.5, HEIGHT * 0.48); 
        } 
        else if (mode === 2) {
            // 模式2：阅读抽奖 -> 使用【用户自定义坐标】(位置靠上)
            log("⚠️ 模式2兜底：使用固定坐标点击 (" + DIY_X + "," + DIY_Y + ")");
            click(DIY_X, DIY_Y); 
        }
    }
    
    sleep(6000); // 等待转动
    
    // 关弹窗
    let confirm = textMatches(/确定|确认|开心收下|好的/).findOne(2000);
    if (confirm) click(confirm.bounds().centerX(), confirm.bounds().centerY());
    
    console.show();
    backToTaskList();
}

// ==========================================
// 辅助函数
// ==========================================

function monitorLoading(seconds) {
    let start = Date.now();
    while (Date.now() - start < seconds * 1000) {
        if (isRealTaskPage()) return true;
        sleep(800);
    }
    return false;
}

function isHomePage() {
    return text("首页").boundsInside(0, HEIGHT * 0.8, WIDTH, HEIGHT).exists();
}

function isRealTaskPage() {
    let noNav = !text("首页").boundsInside(0, HEIGHT * 0.8, WIDTH, HEIGHT).exists();
    let hasSign = textContains("总计 12").exists() || textContains("阅读12篇").exists() || textContains("已完成").exists();
    return noNav && hasSign;
}

function backToTaskList() {
    let limit = 0;
    while (!isRealTaskPage() && limit < 5) {
        back();
        sleep(2500);
        limit++;
    }
}

function visualWait(sec, msg) {
    for (let i = sec; i > 0; i--) {
        if (i % 20 == 0 || i <= 5) toast(msg + " 剩 " + i + "秒");
        sleep(1000);
    }
}
