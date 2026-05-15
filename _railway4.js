const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  
  // Find existing Railway tab
  let rp = null;
  for (const p of ctx.pages()) {
    if (p.url().includes('railway.com')) { rp = p; break; }
  }
  if (!rp) { console.log('No railway tab'); return; }
  
  // Go to dashboard
  await rp.goto('https://railway.com/dashboard', { timeout: 15000, waitUntil: 'domcontentloaded' });
  await rp.waitForTimeout(3000);
  
  // Find and click project link
  const links = await rp.$$('a');
  for (const link of links) {
    const text = ((await link.textContent()) || '').trim();
    if (text.includes('stellar') || text.includes('celebration')) {
      console.log('Found project link:', text, await link.getAttribute('href'));
      await link.click();
      await rp.waitForTimeout(4000);
      console.log('After click URL:', rp.url());
      const t = await rp.evaluate(() => document.body.innerText.substring(0, 3000));
      console.log(t);
      break;
    }
  }
  
  await rp.screenshot({ path: '_railway_proj.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
