const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Go to Vercel dashboard
  await page.goto('https://vercel.com/dashboard', {
    timeout: 20000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  console.log('URL:', page.url());
  
  // Get project list
  const text = await page.evaluate(() => document.body.innerText);
  const lines = text.split('\n').filter(l => l.trim());
  console.log('--- PAGE CONTENT ---');
  // Show everything
  console.log(text.substring(0, 3000));
  
  await page.screenshot({ path: '_vercel_dash.png' });
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
