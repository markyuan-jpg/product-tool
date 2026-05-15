const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Go to Railway dashboard
  await page.goto('https://railway.com/dashboard', {
    timeout: 20000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  console.log('URL:', page.url());
  const text = await page.evaluate(() => document.body.innerText.substring(0, 3000));
  console.log(text);
  
  await page.screenshot({ path: '_railway_dash.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
