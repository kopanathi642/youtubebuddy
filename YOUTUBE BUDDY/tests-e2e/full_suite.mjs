import { launch, BASE, rec, results } from './lib.mjs';
import fs from 'fs';
const { browser, ctx, page } = await launch();
const email = `full_${Date.now()}@example.com`, pw = 'Test@12345678';
const net = []; page.on('response', r => { if (r.url().includes(':8000/api')) net.push({ s: r.status(), m: r.request().method(), u: r.url().replace('http://localhost:8000/api/v1','') }); });
const T = async (name, fn) => { try { await fn(); } catch (e) { rec(name, false, 'EXC ' + String(e.message).split('\n')[0].slice(0,150)); await page.screenshot({ path: `shots/fail_${name.replace(/\W+/g,'_')}.png` }).catch(()=>{}); } };
const wait = (ms=1500) => page.waitForTimeout(ms);
const toasts = () => page.$$eval('[role=status]', els => els.map(e => e.innerText.trim()).filter(Boolean).join(' | '));
const mainText = async () => (await page.innerText('main')).replace(/\s+/g,' ');

// AUTH
await T('A1 logged-out /dashboard redirects to /login', async () => { await page.goto(BASE+'/dashboard'); await page.waitForURL(/login/,{timeout:15000}); rec('A1 logged-out /dashboard redirects to /login', true); });
await T('A2 signup -> dashboard', async () => {
  await page.goto(BASE+'/signup'); await page.fill('input[name=displayName]','Full Tester'); await page.fill('input[name=email]',email);
  await page.fill('input[name=password]',pw); await page.fill('input[name=confirmPassword]',pw);
  await page.click('button:has-text("Create free account")'); await page.waitForURL(/dashboard/,{timeout:40000}); rec('A2 signup -> dashboard', true); });
await T('A3 mismatched passwords blocked', async () => {
  await page.evaluate(()=>localStorage.clear()); await page.goto(BASE+'/signup');
  await page.fill('input[name=displayName]','Mismatch'); await page.fill('input[name=email]','mm_'+Date.now()+'@example.com');
  await page.fill('input[name=password]',pw); await page.fill('input[name=confirmPassword]',pw+'x'); await page.click('button:has-text("Create free account")'); await wait();
  rec('A3 mismatched passwords blocked', /signup/.test(page.url())); });
await T('A4 weak password blocked (server+client)', async () => {
  await page.goto(BASE+'/signup'); await page.fill('input[name=displayName]','Weak'); await page.fill('input[name=email]','weak_'+Date.now()+'@example.com');
  await page.fill('input[name=password]','abc'); await page.fill('input[name=confirmPassword]','abc'); await page.click('button:has-text("Create free account")'); await wait();
  rec('A4 weak password blocked', /signup/.test(page.url())); });
await T('A5 wrong password shows error', async () => {
  await page.goto(BASE+'/login'); await page.fill('input[name=email]',email); await page.fill('input[name=password]','WrongPass!1');
  await page.click('button:has-text("Sign in")'); await wait(2000); const t=(await page.innerText('body'))+await toasts();
  rec('A5 wrong password shows error', /login/.test(page.url()) && /invalid|incorrect|wrong|failed|credential/i.test(t)); });
await T('A6 login ok + persists across reload', async () => {
  await page.goto(BASE+'/login'); await page.fill('input[name=email]',email); await page.fill('input[name=password]',pw);
  await page.click('button:has-text("Sign in")'); await page.waitForURL(/dashboard/,{timeout:30000});
  await page.reload({waitUntil:'networkidle'}); await wait(); rec('A6 login ok + persists across reload', /dashboard/.test(page.url())); });
await T('A7 forgot-password is honest (no fake success)', async () => {
  await page.goto(BASE+'/forgot-password'); await page.fill('input[name=email]',email); await page.click('button:has-text("Send reset link")'); await wait(1500);
  const t=(await page.innerText('body'))+' '+await toasts(); rec('A7 forgot-password is honest (no fake success)', /not set up|contact support/i.test(t) && !/link has been sent|check your inbox/i.test(t), t.replace(/\s+/g,' ').slice(0,110)); });

// PROFILE
await T('P1 profile save persists after reload', async () => {
  await page.goto(BASE+'/profile',{waitUntil:'networkidle'}); await wait();
  await page.locator('main input[type=text]').first().fill('Renamed Tester'); await page.fill('main textarea','Kids 3D animation channel');
  net.length=0; await page.click('button:has-text("Save Changes")'); await wait(2000);
  const put=net.find(n=>n.m==='PUT'&&n.u.includes('user/profile'));
  await page.reload({waitUntil:'networkidle'}); await wait();
  const nm=await page.locator('main input[type=text]').first().inputValue(), bio=await page.inputValue('main textarea');
  rec('P1 profile save persists after reload', put?.s===200 && nm==='Renamed Tester' && bio==='Kids 3D animation channel', `PUT=${put?.s} name="${nm}" bio="${bio}"`); });
await T('P2 profile rejects 1-char name', async () => {
  await page.locator('main input[type=text]').first().fill('A'); net.length=0; await page.click('button:has-text("Save Changes")'); await wait(1000);
  rec('P2 profile rejects 1-char name (no request sent)', !net.some(n=>n.m==='PUT'), await toasts()); });

// SETTINGS
await T('S1 API key create, show-once, revoke', async () => {
  await page.goto(BASE+'/dashboard/settings',{waitUntil:'networkidle'}); await wait();
  net.length=0; await page.click('button:has-text("Generate New Key")'); await wait(2000);
  const post=net.find(n=>n.m==='POST'&&n.u.includes('api-keys')); const shown=await page.locator('code').count();
  rec('S1a Generate New Key creates real key + shows it once', post?.s<300 && shown>0, `POST=${post?.s} codeBlocks=${shown}`);
  net.length=0; await page.click('button:has-text("Revoke") >> nth=0'); await wait(1500);
  const del=net.find(n=>n.m==='DELETE'&&n.u.includes('api-keys')); rec('S1b Revoke removes key', del?.s<300 && await page.locator('button:has-text("Revoke")').count()===0, `DELETE=${del?.s}`); });
await T('S2 preferences persist after reload', async () => {
  await page.getByRole('button',{name:/System/}).click(); await page.selectOption('main select','French');
  await page.getByRole('switch',{name:'Marketing Updates'}).click(); await page.click('button:has-text("Save Changes")'); await wait(800);
  await page.reload({waitUntil:'networkidle'}); await wait();
  const lang=await page.inputValue('main select'), mk=await page.getByRole('switch',{name:'Marketing Updates'}).getAttribute('aria-checked');
  rec('S2 preferences persist after reload', lang==='French' && mk==='true', `lang=${lang} marketing=${mk}`); });

// UPLOAD + SHORTS + EXPORT
const API=process.env.API_URL||'http://localhost:8000/api/v1';
await T('U1 upload video', async () => {
  await page.goto(BASE+'/studio/shorts',{waitUntil:'networkidle'}); await wait();
  await page.setInputFiles('input[type=file]','test.mp4'); await wait(500); net.length=0;
  await page.click('button:has-text("Upload & Process")'); await wait(5000);
  const up=net.find(n=>n.u.includes('videos/upload')); rec('U1 upload video via UI', up?.s===200, `status=${up?.s}`); });
await T('U2 reject non-video via UI', async () => {
  fs.writeFileSync('fake.mp4','this is not a video'); await page.goto(BASE+'/studio/shorts',{waitUntil:'networkidle'}); await wait();
  await page.setInputFiles('input[type=file]','fake.mp4'); await wait(500); net.length=0; await page.click('button:has-text("Upload & Process")'); await wait(3000);
  const up=net.find(n=>n.u.includes('videos/upload')); rec('U2 fake video rejected with clear message', up?.s===415 && /valid video|Unsupported/i.test(await toasts()+await mainText()), `status=${up?.s} ${await toasts()}`); });
await T('U3 generate short -> render -> Export Short', async () => {
  await page.goto(BASE+'/studio/shorts',{waitUntil:'networkidle'}); await wait();
  await page.setInputFiles('input[type=file]','test.mp4'); await wait(400); await page.click('button:has-text("Upload & Process")');
  await page.waitForSelector('button:has-text("Generate Shorts")',{timeout:20000});
  await page.getByRole('button',{name:/9:16/}).click(); net.length=0;
  await page.click('button:has-text("Generate Shorts")'); await wait(1500);
  const gen=net.find(n=>n.u.includes('shorts/generate')); rec('U3a Generate Shorts accepted', gen?.s===202, `status=${gen?.s}`);
  const exp=page.getByRole('button',{name:/^Export Short$/}); await exp.waitFor({timeout:60000});
  rec('U3b render finishes and Export Short enabled', await exp.isEnabled());
  const [popup]=await Promise.all([ctx.waitForEvent('page',{timeout:10000}), exp.click()]);
  const resp=await popup.waitForLoadState().then(()=>fetch(popup.url())); const buf=await resp.arrayBuffer();
  rec('U3c Export opens real rendered mp4', resp.ok && buf.byteLength>10000, `${popup.url().replace('http://localhost:8000','')} ${buf.byteLength}B`); await popup.close(); });
await T('U4 uploaded videos listed, sort toggle, delete', async () => {
  await page.goto(BASE+'/dashboard/videos',{waitUntil:'networkidle'}); await wait();
  const t=await mainText(); rec('U4a My Videos lists uploads', !/No videos uploaded yet/.test(t), t.slice(0,90));
  await page.click('button[aria-label="Toggle sort order"]'); rec('U4b sort toggle works', /Oldest first/.test(await mainText()));
  net.length=0; page.once('dialog',d=>d.accept()); const del=page.getByRole('button',{name:/^Delete /}).first();
  if (await del.count()) { await del.click(); await wait(2000); const d=net.find(n=>n.m==='DELETE'); rec('U4c delete video (with renders) ok', d?.s===200, `DELETE=${d?.s}`); } else rec('U4c delete control found', false, 'no delete button located'); });
await T('U5 Create New Video routes to studio', async () => {
  await page.goto(BASE+'/dashboard/videos',{waitUntil:'networkidle'}); await page.click('button:has-text("Create New Video")'); await wait(2000);
  rec('U5 Create New Video routes to /studio/shorts', /studio\/shorts/.test(page.url()), page.url().replace(BASE,'')); });

// AI + AGENTS
await T('G1 studio generate shows simulated notice', async () => {
  await page.goto(BASE+'/studio/script',{waitUntil:'networkidle'}); await wait(); await page.fill('textarea','A cat teaching math to kids');
  net.length=0; await page.click('button:has-text("Generate Now")'); await wait(5000);
  const g=net.find(n=>n.u.includes('studio/generate')); const t=await toasts();
  rec('G1 studio generate ok + "Demo output" notice', g?.s===200 && /demo output|simulated/i.test(t), `POST=${g?.s} toast="${t.slice(0,90)}"`); });
await T('AG1 agent Run triggers backend', async () => {
  await page.goto(BASE+'/agents',{waitUntil:'networkidle'}); await wait(); net.length=0;
  await page.click('main button:has-text("Run") >> nth=1'); await wait(5000); const p=net.find(n=>n.m==='POST'&&n.u.includes('agents'));
  rec('AG1 agent Run -> backend 2xx', p?.s<300, `POST=${p?.s} ${p?.u}`); });

// SIGN OUT + DEV LOGIN
await T('L1 sign out clears session', async () => {
  await page.goto(BASE+'/profile',{waitUntil:'networkidle'}); await wait(); await page.click('button:has-text("Sign Out")'); await wait(2500);
  await page.goto(BASE+'/dashboard'); await page.waitForURL(/login/,{timeout:15000}); rec('L1 sign out clears session', true); });
await T('L2 dev-login works (development)', async () => {
  await page.goto(BASE+'/dev-login',{waitUntil:'networkidle'}); await page.click('button:has-text("Login as Dev User")'); await page.waitForURL(/dashboard/,{timeout:30000}); rec('L2 dev-login works (development)', true); });

// FULL PAGE CRAWL (logged in as dev user)
for (const r of ['/dashboard','/dashboard/videos','/dashboard/analytics','/dashboard/billing','/dashboard/settings','/studio','/studio/shorts','/studio/cinematic','/studio/script','/agents','/profile','/audio','/image','/cinema','/collab','/influencer','/marketing','/explore','/pricing']) {
  await T('C '+r, async () => {
    page.issues.length=0; await page.goto(BASE+r,{waitUntil:'networkidle',timeout:60000}).catch(()=>{}); await wait(1200);
    const txt=(await page.innerText('body')); const crashed=/Application error|Unhandled Runtime Error|could not be found/i.test(txt);
    const real=page.issues.filter(i=>!/favicon|_rsc=.*ERR_ABORTED/.test(i.msg)); rec(`C page ${r} renders, no errors`, !crashed && real.length===0, real.slice(0,2).map(i=>i.t+': '+i.msg).join(' | ')); }); }
console.log(`\n==== ${results.filter(r=>r.ok).length}/${results.length} passed ====`);
fs.writeFileSync('full_results.json',JSON.stringify(results,null,1)); await browser.close();
