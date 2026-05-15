const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  
  // Use existing Railway tab (find by URL matching)
  let rp = null;
  for (const p of ctx.pages()) {
    const url = p.url();
    if (url.includes('railway.com')) {
      rp = p;
      console.log('Found Railway tab:', url);
      break;
    }
  }
  
  if (!rp) {
    console.log('No Railway tab found, creating one');
    rp = await ctx.newPage();
    await rp.goto('https://railway.com/dashboard', { timeout: 15000, waitUntil: 'domcontentloaded' });
    await rp.waitForTimeout(3000);
  }
  
  // Navigate to project
  await rp.goto('https://railway.com/project/stellar-celebration', { timeout: 15000, waitUntil: 'domcontentloaded' });
  await rp.waitForTimeout(3000);
  
  console.log('URL:', rp.url());
  const text = await rp.evaluate(() => document.body.innerText.substring(0, 3000));
  console.log(text);
  
  await rp.screenshot({ path: '_railway_proj.png' });
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
