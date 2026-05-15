const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const pages = ctx.pages();
  
  console.log(`Open tabs: ${pages.length}`);
  for (let i = 0; i < pages.length; i++) {
    try {
      console.log(`Tab ${i}: ${pages[i].url().substring(0, 120)}`);
    } catch(e) {
      console.log(`Tab ${i}: (error: ${e.message})`);
    }
  }
  
  // Open new tab for Railway
  const rp = await ctx.newPage();
  await rp.goto('https://railway.app/dashboard', { timeout: 15000, waitUntil: 'domcontentloaded' });
  await rp.waitForTimeout(2000);
  console.log('Railway URL:', rp.url().substring(0, 100));
  await rp.screenshot({ path: '_railway.png' });
  console.log('Railway screenshot saved');
}

main().catch(e => { console.error('Error:', e.message); if (!e.message.includes('Timeout')) process.exit(1); });
