import { launch, BASE } from './lib.mjs';
const { browser, page } = await launch();
await page.goto(BASE + '/dev-login', { waitUntil: 'networkidle' }); await page.click('button:has-text("Login as Dev User")'); await page.waitForURL(/dashboard/, { timeout: 40000 });
const pages = ['/','/pricing','/explore','/dashboard','/dashboard/videos','/dashboard/analytics','/dashboard/billing','/dashboard/settings','/studio','/studio/shorts','/studio/cinematic','/studio/script','/agents','/profile','/audio','/image','/cinema','/collab','/influencer','/marketing','/login','/signup','/forgot-password'];
const found = new Map();
for (const p of pages) {
  await page.goto(BASE + p, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(()=>{}); await page.waitForTimeout(900);
  const hrefs = await page.$$eval('a[href]', as => as.map(a => a.getAttribute('href')));
  for (const h of hrefs) { if (!h || !h.startsWith('/') || h.startsWith('//')) continue; const clean = h.split('#')[0].split('?')[0]; if (clean && !found.has(clean)) found.set(clean, p); }
}
console.log('unique internal links found:', found.size);
let bad = 0;
for (const [l, from] of found) { const r = await fetch(BASE + l); if (r.status !== 200) { bad++; console.log('BROKEN', r.status, l, '(on', from + ')'); } }
console.log(bad === 0 ? `PASS all ${found.size} rendered internal links resolve` : `FAIL ${bad} broken links`);
await browser.close();
