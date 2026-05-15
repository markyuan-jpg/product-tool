const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const ctx = browser.contexts()[0];
  const page = await ctx.newPage();

  // Navigate to Vercel project settings
  await page.goto('https://vercel.com/markyuan-jpgs-projects/quickquote-65r2o5lx5/settings/general', {
    timeout: 20000, waitUntil: 'domcontentloaded'
  });
  await page.waitForTimeout(3000);
  
  console.log('URL:', page.url());
  console.log('Title:', await page.title());
  
  // Get page text to understand structure
  const text = await page.evaluate(() => document.body.innerText);
  // Show first 2000 chars
  console.log('--- PAGE TEXT (first 2000) ---');
  console.log(text.substring(0, 2000));
  
  await page.screenshot({ path: '_vercel_settings.png', fullPage: true });
  console.log('Screenshot saved');
  
  await page.close();
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
