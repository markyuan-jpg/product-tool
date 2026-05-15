const { chromium } = require('playwright');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];

  let vp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('vercel.com')) { vp = p; break; }
  }
  if (!vp) { console.log('No vercel tab'); return; }

  await vp.goto('https://vercel.com/markyuan-jpgs-projects/quickquote/settings/environment-variables', { 
    timeout: 30000, waitUntil: 'domcontentloaded' 
  });
  await sleep(5000);
  
  const text = await vp.evaluate(() => document.body.innerText);
  console.log(text.substring(0, 3000));
  
  await vp.screenshot({ path: '_vercel_final.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
