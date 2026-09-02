// 数字人嘴型同步验证：播放过程中高频采样嘴部像素，证明嘴巴随声音变化
// 前置：对话系统(8088)与数字人服务(48620)已启动、loader.js 已注入、数字人窗口已启用。
// 用法（需要本机 Chrome + Open WebUI 账号）:
//   node tests\avatar_sync_test.js   （账号经 OWUI_EMAIL / OWUI_PASSWORD 环境变量传入，不提供则跳过）
// 可选环境变量:
//   CHROME_PATH    Chrome/Edge 可执行文件路径（默认自动探测常见位置）
const { chromium } = require('playwright-core');

function findChrome() {
  const env = process.env.CHROME_PATH;
  if (env) return env;
  const candidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/microsoft-edge',
  ];
  return candidates.find((p) => require('fs').existsSync(p));
}

(async () => {
  const email = process.env.OWUI_EMAIL;
  const passwd = process.env.OWUI_PASSWORD;
  if (!email || !passwd) {
    console.log('未提供 OWUI_EMAIL / OWUI_PASSWORD，跳过（需先完成部署并创建账号）。');
    process.exit(0);
  }
  const CHROME = findChrome();
  if (!CHROME) { console.error('未找到 Chrome/Edge，请设置 CHROME_PATH'); process.exit(1); }
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto('http://localhost:8088', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(4000);
  await page.evaluate(async ({ email, passwd }) => {
    const cred = { email: email };
    cred['password'] = passwd;
    const r = await fetch('/api/v1/auths/signin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cred) });
    const d = await r.json();
    localStorage.setItem('token', d.token);
  }, { email: email, passwd: passwd });
  await page.evaluate(async () => {
    const r = await fetch('/api/v1/audio/speech', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + localStorage.getItem('token') }, body: JSON.stringify({ model: 'azhong', input: '测试数字人同步，声音一二三四五，嘴巴动起来。', voice: 'azhong' }) });
    window.__testBlob = await r.blob();
  });
  await page.waitForTimeout(2500);
  const sampleMouth = () => page.evaluate(() => {
    const w = document.getElementById('dsh-avatar-win');
    if (!w) return null;
    const c = w.querySelector('canvas');
    if (!c) return null;
    try {
      const ctx = c.getContext('2d');
      const d = ctx.getImageData(Math.floor(c.width / 2), Math.floor(c.height * 0.58), 10, 10).data;
      let r = 0, g = 0, b = 0, n = 0;
      for (let i = 0; i < d.length; i += 4) { r += d[i]; g += d[i + 1]; b += d[i + 2]; n++; }
      return Math.round(r / n) * 10000 + Math.round(g / n) * 100 + Math.round(b / n);
    } catch (e) { return -1; }
  });
  // 播放
  await page.evaluate(async () => {
    const url = URL.createObjectURL(window.__testBlob);
    const a = new Audio(url);
    a.play();
  });
  const samples = [];
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(500);
    samples.push(await sampleMouth());
  }
  console.log('播放中嘴部像素采样:', JSON.stringify(samples));
  const uniq = new Set(samples).size;
  console.log(uniq > 1 ? 'PASS: 嘴巴在动（采样值有变化）' : 'FAIL: 嘴巴没动（采样值全部相同）');
  await browser.close();
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
