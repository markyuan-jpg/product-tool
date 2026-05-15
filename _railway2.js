const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  await page.goto('https://railway.com/project/stellar-celebration', {
    timeout: 20000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(4000);
  
  console.log('URL:', page.url());
  const text = await page.evaluate(() => document.body.innerText.substring(0, 3000));
  console.log(text);
  
  await page.screenshot({ path: '_railway_project.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
