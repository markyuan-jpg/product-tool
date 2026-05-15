const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { console.log('No railway tab'); return; }
  
  await rp.goto('https://railway.com/project/7009ad57-9fad-4182-9a1b-757e27af171f', { 
    timeout: 20000, waitUntil: 'domcontentloaded' 
  });
  await rp.waitForTimeout(3000);
  
  // Click on product-tool
  const links = await rp.$$('a, [role="button"], button');
  for (const link of links) {
    try {
      const t = ((await link.textContent()) || '').trim();
      if (t.includes('product-tool') || t.includes('product')) {
        console.log('Clicking:', t);
        await link.click();
        await rp.waitForTimeout(4000);
        console.log('Post-click URL:', rp.url());
        const text = await rp.evaluate(() => document.body.innerText);
        console.log(text.substring(0, 3000));
        break;
      }
    } catch(e) { /* ignore */ }
  }
  
  await rp.screenshot({ path: '_railway_service.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
