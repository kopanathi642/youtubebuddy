import fs from 'fs';
import { chromium as pw } from 'playwright-core';
export const BASE = process.env.BASE_URL || 'http://localhost:3000';
export async function launch() {
  const chromePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  ];
  let exe = chromePaths.find(p => fs.existsSync(p));
  if (!exe) {
    const chromium = (await import('@sparticuz/chromium')).default;
    exe = await chromium.executablePath();
  }
  const browser = await pw.launch({ executablePath: exe, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1360, height: 900 } });
  const page = await ctx.newPage();
  page.issues = [];
  page.on('console', m => { if (m.type() === 'error' && !/ERR_NAME_NOT_RESOLVED/.test(m.text())) page.issues.push({ t: 'console', msg: m.text().slice(0, 220), url: page.url() }); });
  page.on('pageerror', e => page.issues.push({ t: 'pageerror', msg: String(e).slice(0, 220), url: page.url() }));
  page.on('response', r => { if (r.status() >= 400 && !r.url().includes('_next')) page.issues.push({ t: 'http', msg: `${r.status()} ${r.request().method()} ${r.url().replace('http://localhost','')}`, url: page.url() }); });
  page.on('requestfailed', r => !/fonts.g(oogleapis|static)/.test(r.url()) && page.issues.push({ t: 'reqfailed', msg: `${r.method()} ${r.url().slice(0,120)} ${r.failure()?.errorText}`, url: page.url() }));
  return { browser, ctx, page };
}
export const results = [];
export function rec(name, ok, detail = '') { results.push({ name, ok, detail }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`); }
